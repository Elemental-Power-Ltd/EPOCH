"""
Common fixtures for the FastAPI endpoints.

The main feature you want to be using here is the `client` fixture, which will
provide a FastAPI TestClient with an overridden database.
It can be slightly slow to load, so there's room to optimise it in future.

If your fixture is used by tests for multiple unrelated endpoints, put it here.
Otherwise, leave it in the test file.
"""

# ruff: noqa: D101, D102, D103
from collections.abc import AsyncGenerator
from pathlib import Path

import asyncpg
import pytest_asyncio
import testing.postgresql  # type: ignore
from httpx import ASGITransport, AsyncClient

from app.dependencies import Database, DBConnection, get_db_conn, get_db_pool, get_http_client
from app.main import app

db_factory = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Get a FastAPI client for a single test.

    Each time a test requests this fixture, it'll create a new database (which can be slow)
    and populate it with some test data.
    It then overrides the `get_db_conn` for all the endpoints deeper in, using mysterious FastAPI magic.
    """
    underlying_db = db_factory()
    db = Database(dsn=underlying_db.url())

    await db.create_pool()
    assert db.pool is not None, "Could not create database pool"
    conn = await db.pool.acquire()
    # TODO (2024-08-12 MHJB): there must be a better way...
    await conn.execute("""CREATE ROLE python""")
    with Path("./elementaldb_tables.sql").open() as fi:
        await conn.execute(fi.read())
    with Path("./elementaldb_client_info.sql").open() as fi:
        await conn.execute(fi.read())

    async def override_get_db_pool() -> AsyncGenerator[asyncpg.pool.Pool, None]:
        """
        Override the database creation with our database from this file.

        This is nested to use the `db` object from this functional scope,
        and not the global `db` object we use elsewhere.
        """
        assert db.pool is not None, "Database pool not yet created."
        yield db.pool

    async def override_get_db_conn() -> AsyncGenerator[DBConnection, None]:
        """
        Override the database creation with our database from this file.

        This is nested to use the `db` object from this functional scope,
        and not the global `db` object we use elsewhere.
        """
        await db.create_pool()
        assert db.pool is not None, "Could not create database pool"
        conn = await db.pool.acquire()
        try:
            yield conn
        finally:
            await db.pool.release(conn)

    async def override_get_http_client() -> AsyncGenerator[AsyncClient, None]:
        """
        Override the HTTP client with a functional local http client.

        If we re-use the same HTTPX AsyncClient then we cause trouble with AsyncIO, causing
        `RuntimeError: Event loop is closed" issues.
        """
        # Use the 'Connection Close' headers to suppress httpx's connection pooling, as
        # it'll helpfully try to reuse a connection between event loops and then fall over.
        async with AsyncClient(headers=[("Connection", "close")], timeout=60.0) as http_client:
            yield http_client

    app.dependency_overrides[get_db_pool] = override_get_db_pool
    app.dependency_overrides[get_db_conn] = override_get_db_conn
    app.dependency_overrides[get_http_client] = override_get_http_client

    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://localhost",
    ) as client:
        yield client
    del app.dependency_overrides[get_db_conn]
    del app.dependency_overrides[get_db_pool]
    del app.dependency_overrides[get_http_client]
