"""
Database connection pool and HTTP Client connection pool dependencies.

We aim to re-use connections from a pool to give everything the maximal chance of scheduling intelligently.
To connect to a database, simply provide the relevant `DatabaseDep` or `HttpClientDep` as a type hint to a
function and FastAPI will figure it out through magic.
"""

import asyncio
import datetime
import logging
import multiprocessing
import os
import typing
from collections.abc import AsyncGenerator, AsyncIterator
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Never

import asyncpg
import httpx
import torch
from fastapi import Depends, FastAPI

from .epl_secrets import SecretDict, get_secrets_environment
from .internal.elec_meters import VAE
from .internal.elec_meters.vae_2_0 import VAE as VAE_2_0

logger = logging.getLogger("default")

type DBConnection = asyncpg.Connection | asyncpg.pool.PoolConnectionProxy
type HTTPClient = httpx.AsyncClient


class Database:
    """Shared database object that we'll re-use throughout the lifetime of this API."""

    def __init__(
        self,
        host: str | None = None,
        user: str = "python",
        password: str | None = None,
        dsn: str | None = None,
        database: str = "elementaldb",
    ) -> None:
        if dsn is not None and host is not None:
            raise ValueError("Must provide either one of host or dsn, but got both.")
        elif dsn is None and host is None:
            raise ValueError("Must provide either one of host or dsn, but got neither")

        self.dsn = dsn  # might be None

        self.host = host

        if password is None:
            # If we didn't get a password from the environment, it might be None anyway
            # (this can sometimes bite us when importing, as we'll do this bit first!)
            self.password = get_secrets_environment().get("EP_POSTGRES_PASSWORD", None)
        else:
            self.password = password

        self.user = user
        self.database = database
        self.pool: asyncpg.Pool | None = None

    async def create_pool(self) -> None:
        """
        Create the PostgreSQL connection pool.

        For a given endpoint, use `pool.acquire()` to get an entry from this pool
        and speed things up.
        """
        if self.pool is not None:
            logger.warning("Pool aready created for DB")
            return None

        try:
            if self.dsn is not None:
                # Use this for the local tests, where the DSN is provided by the testing framework
                self.pool = await asyncpg.create_pool(dsn=self.dsn)
            else:
                self.pool = await asyncpg.create_pool(
                    host=self.host, user=self.user, password=self.password, database=self.database
                )
        except asyncpg.exceptions.ConnectionFailureError as ex:
            raise RuntimeError(
                f"Could not connect to postgresql database={self.database}" + f" at host={self.host} with user={self.user}"
            ) from ex
        except ConnectionRefusedError as ex:
            raise RuntimeError(
                f"Connection refused to postgresql database={self.database}" + f" at host={self.host} with user={self.user}."
            ) from ex
        assert self.pool is not None, "Could not create database pool"


db = Database(host=os.environ.get("EP_DATABASE_HOST", "localhost"))

# These limits are enormous to make sure that we don't saturate the AsyncConnnections
# https://github.com/encode/httpx/discussions/3084
http_limits = httpx.Limits(max_keepalive_connections=10000, keepalive_expiry=datetime.timedelta(seconds=30).total_seconds())
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        pool=None,
        connect=datetime.timedelta(minutes=10).total_seconds(),
        read=datetime.timedelta(minutes=10).total_seconds(),
        write=None,
    ),
    limits=http_limits,
)

elec_vae_mdl: VAE | VAE_2_0 | None = None


async def get_http_client() -> AsyncGenerator[HTTPClient]:
    """
    Get a shared HTTP client.

    This is passed as a dependency to make the most use of connection and async
    pooling (i.e. everything goes through this client, so it has the most opportunity to schedule intelligently).
    """
    yield http_client


async def get_db_conn() -> AsyncGenerator[DBConnection]:
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


async def get_db_pool() -> AsyncGenerator[asyncpg.pool.Pool]:
    """
    Get access to the database connection pool directly.

    Use this for more fine-grained control than get_db_conn
    """
    assert db.pool is not None, "Database pool not yet created."
    yield db.pool


async def get_vae_model(use_new: bool = True) -> VAE | VAE_2_0:
    """
    Get a loaded VAE model.

    This should have been loaded in when we did the lifespan events to start up.
    """
    global elec_vae_mdl
    if elec_vae_mdl is None:
        if use_new:
            elec_vae_mdl = load_vae_2_0()
        else:
            elec_vae_mdl = load_vae()
    return elec_vae_mdl


async def get_secrets_dependency() -> SecretDict:
    """Get the environment secrets, including API keys, from os environ, .env and files."""
    return get_secrets_environment()


_PROCESS_POOL: ProcessPoolExecutor | None = None
_THREAD_POOL: ThreadPoolExecutor | None = None


async def get_process_pool() -> ProcessPoolExecutor:
    """
    Dependency Injection for background process pools.

    Will initialise the process pool the first time it is called.
    """
    global _PROCESS_POOL
    if _PROCESS_POOL is None:
        # We use the "spawn" multiprocessing context as
        # "fork" can cause trouble with FastAPI's multithreading.
        mp_context = multiprocessing.get_context("spawn")
        _PROCESS_POOL = ProcessPoolExecutor(mp_context=mp_context)
    return _PROCESS_POOL


async def get_thread_pool() -> ThreadPoolExecutor:
    """
    Dependency Injection for background thread pools.

    Will initialise the thread pool the first time it is called.
    Uses many workers to avoid saturating the pool.
    """
    global _THREAD_POOL
    if _THREAD_POOL is None:
        _THREAD_POOL = ThreadPoolExecutor(max_workers=16)
    return _THREAD_POOL


SecretsDep = typing.Annotated[SecretDict, Depends(get_secrets_dependency)]
DatabaseDep = typing.Annotated[DBConnection, Depends(get_db_conn)]
DatabasePoolDep = typing.Annotated[asyncpg.pool.Pool, Depends(get_db_pool)]
HttpClientDep = typing.Annotated[HTTPClient, Depends(get_http_client)]
VaeDep = typing.Annotated[VAE | VAE_2_0, Depends(get_vae_model)]
ProcessPoolDep = typing.Annotated[ProcessPoolExecutor, Depends(get_process_pool)]


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


def find_model_path_2_0(base_dir: Path = Path(".")) -> Path:
    """
    Search upwards from this directory to find the models directory for the 2.0 version.

    This is useful if you're loading from a notebooks directory.

    Parameters
    ----------
    base_dir
        Initial directory to look in. We'll check for a given models suffix here, and then check "..", "../.." etc.

    Returns
    -------
        Fully resolved path to elecVAE_weights.pth
    """
    final_dir = Path("models", "draft", "32 - trained - QB", "elecVAE_weights.pth")

    fpath = base_dir / final_dir
    for _ in range(3):
        if fpath.exists():
            return fpath.resolve()
        fpath = Path("..") / fpath
    raise FileNotFoundError(f"Could not find {final_dir}")


def load_vae() -> VAE:
    """Load the VAE from a file, with the relevant sizes."""
    mdl = VAE(input_dim=1, aggregate_dim=1, date_dim=13, latent_dim=5, hidden_dim=64, num_layers=1)
    mdl.load_state_dict(torch.load(find_model_path(), weights_only=True))
    return mdl


def load_vae_2_0() -> VAE_2_0:
    """Load the new VAE from a file, with the relevant sizes."""
    mdl = VAE_2_0(
        input_dim=1,
        aggregate_dim=1,
        date_dim=13,
        latent_dim=16,
        hidden_dim_encoder=16,
        hidden_dim_decoder=8,
        num_layers_encoder=2,
        num_layers_decoder=1,
        dropout_decoder=0.1,
    )
    mdl.load_state_dict(torch.load(find_model_path_2_0(), weights_only=True))
    return mdl


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[Never]:
    """Set up a long clients: a database pool and an HTTP client."""
    # Startup events
    loop = asyncio.get_running_loop()
    thread_pool = await get_thread_pool()
    loop.set_default_executor(thread_pool)
    await db.create_pool()
    global elec_vae_mdl
    elec_vae_mdl = load_vae_2_0()
    yield  # type: ignore
    # Shutdown events
    await http_client.aclose()
