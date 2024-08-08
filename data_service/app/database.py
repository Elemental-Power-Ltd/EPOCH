"""
Database connection pool and HTTP Client connection pool dependencies.

We aim to re-use connections from a pool to give everything the maximal chance of scheduling intelligently.
To connect to a database, simply provide the relevant `DatabaseDep` or `HttpClientDep` as a type hint to a
function and FastAPI will figure it out through magic.
"""

import os
import typing
from typing import AsyncGenerator

import asyncpg
import httpx
from fastapi import Depends


class Database:
    """Shared database object that we'll re-use throughout the lifetime of this API."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    async def create_pool(self) -> None:
        """Create the PostgreSQL connection pool.

        For a given endpoint, use `pool.acquire()` to get an entry from this pool
        and speed things up.

        You can specify the database via the DATABASE_URL environment variable, or it falls back
        to a locally hosted version of Elemental DB if not.
        """
        self.pool = await asyncpg.create_pool(dsn=self.dsn)


db = Database(os.environ.get("DATABASE_URL", "postgresql://python:elemental@localhost/elementaldb"))
http_client = httpx.AsyncClient()

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


DatabaseDep = typing.Annotated[DBConnection, Depends(get_db_conn)]
HttpClientDep = typing.Annotated[HTTPClient, Depends(get_http_client)]
