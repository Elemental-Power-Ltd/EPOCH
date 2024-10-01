"""
Database connection pool and HTTP Client connection pool dependencies.

We aim to re-use connections from a pool to give everything the maximal chance of scheduling intelligently.
To connect to a database, simply provide the relevant `DatabaseDep` or `HttpClientDep` as a type hint to a
function and FastAPI will figure it out through magic.
"""

import os
import typing
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Never

import asyncpg
import httpx
import torch
from fastapi import Depends, FastAPI

from .internal.elec_meters import VAE


class Database:
    """Shared database object that we'll re-use throughout the lifetime of this API."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.pool: asyncpg.pool.Pool | None = None

    async def create_pool(self) -> None:
        """Create the PostgreSQL connection pool.

        For a given endpoint, use `pool.acquire()` to get an entry from this pool
        and speed things up.

        You can specify the database via the DATABASE_URL environment variable, or it falls back
        to a locally hosted version of Elemental DB if not.
        """
        self.pool = await asyncpg.create_pool(dsn=self.dsn)
        assert self.pool is not None, "Could not create database pool"


db = Database(os.environ.get("DATABASE_URL", "postgresql://python:elemental@localhost/elementaldb"))
http_client = httpx.AsyncClient()

elec_vae_mdl = VAE(input_dim=1, aggregate_dim=1, date_dim=1, latent_dim=5, hidden_dim=64, num_layers=1)

DBConnection = asyncpg.Connection | asyncpg.pool.PoolConnectionProxy
HTTPClient = httpx.AsyncClient


async def get_http_client() -> AsyncGenerator[HTTPClient, None]:
    """
    Get a shared HTTP client.

    This is passed as a dependency to make the most use of connection and async
    pooling (i.e. everything goes through this client, so it has the most opportunity to schedule intelligently).
    """
    yield http_client


async def get_db_conn() -> AsyncGenerator[DBConnection, None]:
    """
    Get a connection to the database.

    There is a shared database object with a connection pool, and this will give you a single connection
    from that pool.
    """
    assert db.pool is not None, "Database pool not yet created."
    conn = await db.pool.acquire()
    try:
        yield conn
    finally:
        await db.pool.release(conn)


async def get_db_pool() -> AsyncGenerator[asyncpg.pool.Pool, None]:
    """
    Get access to the database connection pool directly.

    Use this for more fine-grained control than get_db_conn
    """
    assert db.pool is not None, "Database pool not yet created."
    yield db.pool


async def get_vae_model() -> VAE:
    """
    Get a loaded VAE model.

    This should have been loaded in when we did the lifespan events to start up.
    """
    return elec_vae_mdl


DatabaseDep = typing.Annotated[DBConnection, Depends(get_db_conn)]
DatabasePoolDep = typing.Annotated[asyncpg.pool.Pool, Depends(get_db_pool)]
HttpClientDep = typing.Annotated[HTTPClient, Depends(get_http_client)]
VaeDep = typing.Annotated[VAE, Depends(get_vae_model)]


def find_model_path(base_dir: Path = Path(".")) -> Path:
    """
    Search upwards from this directory to find the models directory.

    This is useful if you're loading from a notebooks directory.

    Parameters
    ----------
    base_dir
        Initial directory to look in. We'll check for a given models suffix here, and then check "..", "../.." etc.

    Returns
    -------
        Fully resolved path to elecVAE_weights.pth
    """
    final_dir = Path("models", "final", "elecVAE_weights.pth")

    fpath = base_dir / final_dir
    for _ in range(3):
        if fpath.exists():
            return fpath.resolve()
        fpath = Path("..") / fpath
    raise FileNotFoundError(f"Could not find {final_dir}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[Never]:
    """Set up a long clients: a database pool and an HTTP client."""
    # Startup events
    await db.create_pool()
    print(list(Path(".", "models", "final").walk()))
    elec_vae_mdl.load_state_dict(torch.load(find_model_path(), weights_only=True))
    yield  # type: ignore
    # Shutdown events
    await http_client.aclose()
