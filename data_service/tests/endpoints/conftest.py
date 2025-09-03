"""
Common fixtures for the FastAPI endpoints.

The main feature you want to be using here is the `client` fixture, which will
provide a FastAPI TestClient with an overridden database.
It can be slightly slow to load, so there's room to optimise it in future.

If your fixture is used by tests for multiple unrelated endpoints, put it here.
Otherwise, leave it in the test file.
"""

# ruff: noqa: D103
import asyncio
import json
import sys
from collections.abc import AsyncGenerator, Coroutine
from pathlib import Path
from typing import Any, Self, cast

import asyncpg
import httpx
import pytest
import pytest_asyncio
import testing.postgresql  # type: ignore
from httpx import ASGITransport, AsyncClient

from app.dependencies import (
    Database,
    DBConnection,
    get_db_conn,
    get_db_pool,
    get_http_client,
    get_secrets_dep,
    get_vae_model,
)
from app.internal.epl_typing import Jsonable
from app.internal.utils.database_utils import get_migration_files
from app.internal.utils.utils import url_to_hash
from app.job_queue import TerminateTaskGroup, TrackingQueue, process_jobs
from app.lifespan import get_job_queue
from app.main import app

# apply a windows-specific patch for database termination (we can't use SIGINT)
if sys.platform.startswith("win"):
    import testing.postgresql

    def win_terminate(self: Any, _signal: Any = None) -> None:
        if self.child_process:
            self.child_process.terminate()
            self.child_process.wait()

    testing.postgresql.Postgresql.terminate = win_terminate
    testing.common.database.Database.terminate = win_terminate

DO_MOCK = True
NUM_WORKERS = 2


async def apply_migrations(database: testing.postgresql.Database) -> None:
    """
    Apply the migrations to the testing database.

    Parameters
    ----------
    database
        Testing database, partially initialised, to use.

    Returns
    -------
    None

    Raises
    ------
    PostgresSyntaxError
        If there's an issue with a migration file.
    """
    conn = await asyncpg.connect(dsn=database.url())
    for fname in get_migration_files(Path("migrations"), end=999):
        try:
            await conn.execute(fname.read_text())
        except asyncpg.PostgresSyntaxError as ex:
            raise asyncpg.PostgresSyntaxError(f"Postgres syntax error in {fname}: {ex}") from ex
        except asyncpg.exceptions.UniqueViolationError as ex:
            raise asyncpg.exceptions.UniqueViolationError(f"Unique violation error {fname}: {ex}") from ex


db_factory = testing.postgresql.PostgresqlFactory(
    cache_initialized_db=True, on_initialized=lambda db: asyncio.run(apply_migrations(db))
)

_http_client = AsyncClient(headers=[("Connection", "close")], timeout=60.0)


class MockedHttpClient(httpx.AsyncClient):
    """An overridden HTTP client that gets responses from JSON files."""

    DO_RATE_LIMIT = False  # For reading from files, we don't want to apply a rate limit.

    def __init__(self, *args, **kwargs) -> Self:  # type: ignore
        super().__init__(*args, **kwargs)

    async def post(self, url: httpx.URL | str, **kwargs: Any) -> Coroutine[Any, Any, httpx.Response] | httpx.Response:  # type: ignore
        """
        Make an HTTP POST request, but actually load it from a file.

        Data are stored in JSON files with the filenames being the hash of the relevant URL plus any parameters.
        
        Returns
        -------
        Successful response with JSON from file
        """

        base_dir = Path(".", "tests", "data")
        url = str(url)
        if url.startswith("https://api.octopus.energy/v1/graphql/"):
            directory = base_dir / "octopus"
        else:
            raise ValueError(f"Unhandled post {url}")
        
        url_params = url_to_hash(url, kwargs.get("params"), kwargs.get("json"), kwargs.get("data"))
        
        stored_path = directory / f"{url_params}.json"
        if DO_MOCK and stored_path.exists():
            external_data = json.loads(stored_path.read_text())
        else:
            external_resp = await _http_client.post(url, **kwargs)
            if not external_resp.is_success:
                # Forward any errors we got
                return external_resp
            external_data = external_resp.json()
            stored_path.write_text(json.dumps(external_data, indent=4, sort_keys=True))
      
        return httpx.Response(200, json=external_data)
    
    # The httpx typing is gross so let's just bodge it and carry on
    async def get(self, url: httpx.URL | str, **kwargs: Any) -> Coroutine[Any, Any, httpx.Response] | httpx.Response:  # type: ignore
        """
        Make an HTTP GET request to the relevant 3rd party, but actually load it from the file.

        Data are stored in JSON files with the filenames being the hash of the relevant URL plus any parameters.

        Returns
        -------
            Successful response with data from cache
        """
        url = str(url)
        base_dir = Path(".", "tests", "data")
        
        if url.startswith("https://api.octopus.energy/v1/"):
            directory = base_dir / "octopus"    
        elif url.startswith("https://api.carbonintensity.org.uk/regional/"):
            directory = base_dir / "carbon_intensity"
        elif url.startswith("https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"):
            directory = base_dir / "visual_crossing"
        elif url.startswith("https://re.jrc.ec.europa.eu/api/PVcalc"):
            directory = base_dir / "pvgis"
        elif url.startswith("https://www.renewables.ninja/api/"):
            directory = base_dir / "renewables_ninja"
        elif url.startswith("https://api.re24.energy/v1/data/prices/nordpool"):
            directory = base_dir / "re24"
        else:
            raise ValueError(f"Unhandled GET {url}")
        
        # no data or JSON or a GET request
        url_params = url_to_hash(url, kwargs.get("params"))
        stored_path = directory / f"{url_params}.json"
        if DO_MOCK and stored_path.exists():
            external_data = json.loads(stored_path.read_text())
        else:
            external_resp = await _http_client.get(url, **kwargs)
            if not external_resp.is_success:
                # Forward any errors we got
                return external_resp
            external_data = external_resp.json()
            stored_path.write_text(json.dumps(external_data, indent=4, sort_keys=True))

        return httpx.Response(status_code=200, json=external_data)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
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

    def override_get_db_pool() -> asyncpg.pool.Pool:
        """
        Override the database creation with our database from this file.

        This is nested to use the `db` object from this functional scope,
        and not the global `db` object we use elsewhere.
        """
        assert db.pool is not None, "Database pool not yet created."
        return db.pool

    async def override_get_db_conn() -> AsyncGenerator[DBConnection]:
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

    def override_get_http_client() -> AsyncClient:
        """
        Override the HTTP client with a functional local http client.

        If we re-use the same HTTPX AsyncClient then we cause trouble with AsyncIO, causing
        `RuntimeError: Event loop is closed" issues.
        """
        # Use the 'Connection Close' headers to suppress httpx's connection pooling, as
        # it'll helpfully try to reuse a connection between event loops and then fall over.
        return MockedHttpClient()
        # return _http_client

    queue = TrackingQueue(pool=await override_get_db_pool())

    def override_get_job_queue() -> TrackingQueue:
        return queue

    app.dependency_overrides[get_db_pool] = override_get_db_pool
    app.dependency_overrides[get_db_conn] = override_get_db_conn
    app.dependency_overrides[get_http_client] = override_get_http_client
    app.dependency_overrides[get_job_queue] = override_get_job_queue

    try:
        async with (
            AsyncClient(
                transport=ASGITransport(app),
                base_url="http://localhost",
            ) as client,
            asyncio.TaskGroup() as tg,
        ):
            # We also have to set up the queue handling task
            for _ in range(NUM_WORKERS):
                _ = tg.create_task(
                    process_jobs(
                        queue=override_get_job_queue(),
                        pool=override_get_db_pool(),
                        http_client=override_get_http_client(),
                        vae=await get_vae_model(),
                        secrets_env=get_secrets_dep(),
                        ignore_exceptions=True,
                    )
                )
            yield client
            await queue.join()
            raise TerminateTaskGroup()
    except* TerminateTaskGroup:
        pass

    del app.dependency_overrides[get_db_conn]
    del app.dependency_overrides[get_db_pool]
    del app.dependency_overrides[get_http_client]


@pytest.fixture
def phpp_fpath() -> Path:
    """Load a PHPP into a dataframe and re-use it for each test."""
    return Path("tests", "data", "phpp", "PHPP_demo.xlsx").absolute()


async def get_pool_hack(client: httpx.AsyncClient) -> asyncpg.Pool:
    """
    Get the demo database from the pool as a filthy hack.

    This hack was implemented on 2025-05-07, so please replace with a proper fixture in the future.

    Parameters
    ----------
    client
        The mocked test client to extract the internal DB pool from

    Returns
    -------
    asyncpg.Pool
        Mocked database pool that you cn freely write to
    """
    from app.dependencies import get_db_pool

    return await client._transport.app.dependency_overrides[get_db_pool]()  # type: ignore


def get_internal_client_hack(client: httpx.AsyncClient) -> httpx.AsyncClient:
    """
    Get the demo HTTP client that will maybe draw from a cache.

    This hack was implemented on 2025-05-07, so please replace with a proper fixture in the future.

    Parameters
    ----------
    client
        The mocked test client to extract the internal DB pool from

    Returns
    -------
    httpx.AsyncClient
        Mocked HTTP client that will get from a cache if nneeded
    """
    from app.dependencies import get_http_client

    return client._transport.app.dependency_overrides[get_http_client]()  # type: ignore
