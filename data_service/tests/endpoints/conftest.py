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
        self.octopus_requests = {"cached": 0, "uncached": 0}
        self.visualcrossing_requests = {"cached": 0, "uncached": 0}

    async def get_tariff_from_file(self, url: str, **kwargs: Any) -> Jsonable:
        """
        Get a stored tariff from a file when requesting an URL.

        Files are found in "get_tariff_from_file" and should be found in ./tests/data/{filename}.json
        with the slashes removed.

        Parameters
        ----------
        url
            Octopus API URl you want

        Returns
        -------
            contents of the JSON file, or None if not found
        """
        url_params = url_to_hash(url, kwargs.get("params"))
        stored_tariff = Path(".", "tests", "data", "octopus", f"{url_params}.json")
        if stored_tariff.exists() and DO_MOCK:
            self.octopus_requests["cached"] += 1
            return cast(Jsonable, json.loads(stored_tariff.read_text()))
        else:
            self.octopus_requests["uncached"] += 1
            data = (await _http_client.get(url, **kwargs)).json()
            stored_tariff.write_text(json.dumps(data, indent=4, sort_keys=True))
            return cast(Jsonable, data)

    async def cache_ci_data(self, url: str, **kwargs: Any) -> Jsonable:
        """
        Get some data from CarbonIntensity, and store it in a JSON file.

        Accessing the CarbonIntensity API is very slow, so check the DO_RATE_LIMIT class variable if needed.

        Parameters
        ----------
        url
            Base URL, which should be https://api.carbonintensity.org.uk/regional/intensity/

        Returns
        -------
            Response from VC, ideally via the stored file.
        """
        url_params = url_to_hash(url, kwargs.get("params"))
        stored_tariff = Path(".", "tests", "data", "carbon_intensity", f"{url_params}.json")
        if stored_tariff.exists() and DO_MOCK:
            return cast(Jsonable, json.loads(stored_tariff.read_text()))
        else:
            data = (await _http_client.get(url, **kwargs)).json()
            stored_tariff.write_text(json.dumps(data, indent=4, sort_keys=True))
            return cast(Jsonable, data)

    async def cache_vc_data(self, url: str, **kwargs: Any) -> Jsonable:
        """
        Get some data from VisualCrossing, and store it in a JSON file.

        These files are large and ugly, so watch out!
        Ignores URL parameters in the file store.

        Parameters
        ----------
        url
            Base URL, which should be https://www.renewables.ninja/api/data/pv

        Returns
        -------
            Response from VC, ideally via the stored file.
        """
        url_params = url_to_hash(url, kwargs.get("params"))
        stored_tariff = Path(".", "tests", "data", "visual_crossing", f"{url_params}.json")
        if stored_tariff.exists() and DO_MOCK:
            self.visualcrossing_requests["cached"] += 1
            return cast(Jsonable, json.loads(stored_tariff.read_text()))
        else:
            self.visualcrossing_requests["uncached"] += 1
            data = (await _http_client.get(url, **kwargs)).json()
            stored_tariff.write_text(json.dumps(data, indent=4, sort_keys=True))
            return cast(Jsonable, data)

    async def cache_renewables_ninja_data(self, url: str, **kwargs: Any) -> Jsonable:
        """
        Get some data from renewables.ninja, and store it in a JSON file.

        Note that we need the "params" passed to the kwargs, as that's the structure of their API.
        This will create a really very ugly filename in "./data/pvgis".

        Parameters
        ----------
        url
            Base URL, which should be https://www.renewables.ninja/api/data/pv
        kwargs
            params
                key value dict of parameters passed to RN

        Returns
        -------
            Response from RN, ideally via the stored file.
        """
        # Read the parameters passed to the endpoint to get a horrible _key_value_ type string.
        url_params = url_to_hash(url, kwargs.get("params"))
        stored_rn = Path(".", "tests", "data", "renewables_ninja", f"{url_params}.json")
        if stored_rn.exists() and DO_MOCK:
            return cast(Jsonable, json.loads(stored_rn.read_text()))
        else:
            data = (await _http_client.get(url, **kwargs)).json()
            stored_rn.write_text(json.dumps(data, indent=4, sort_keys=True))
            return cast(Jsonable, data)

    async def cache_pvgis_data(self, url: str, **kwargs: Any) -> Jsonable:
        """
        Get some data from PVGIS, and store it in a JSON file.

        Note that we need the "params" passed to the kwargs, as that's the structure of their API.
        This will create a really very ugly filename in "./data/pvgis".

        Parameters
        ----------
        url
            Base URL, which should be https://re.jrc.ec.europa.eu/api/PVcalc
        kwargs
            params
                key value dict of parameters passed to PVGIS

        Returns
        -------
            Response from PVGIS, ideally via the stored file.
        """
        # Read the parameters passed to the endpoint to get a horrible _key_value_ type string.
        url_params = url_to_hash(url, kwargs.get("params"))
        stored_rn = Path(".", "tests", "data", "pvgis", f"{url_params}.json")
        if stored_rn.exists() and DO_MOCK:
            return cast(Jsonable, json.loads(stored_rn.read_text()))
        else:
            print(f"Getting from {url}, {kwargs}")
            data = (await _http_client.get(url, **kwargs)).json()
            stored_rn.write_text(json.dumps(data, indent=4, sort_keys=True))
            return cast(Jsonable, data)

    async def cache_re24_data(self, url: str, **kwargs: Any) -> Jsonable:
        """
        Get some data from RE24, and store it in a JSON file.

        Note that we need the "params" passed to the kwargs, as that's the structure of their API.

        Parameters
        ----------
        url
            Base URL, which should be https://api.re24.energy/v1/data/prices/nordpool
        kwargs
            params
                key value dict of parameters passed to RE24, including start and end timesstamps

        Returns
        -------
            Response from RE24, ideally via the stored file.
        """
        # Read the parameters passed to the endpoint, but do not get the header as they contain an API key!
        url_params = url_to_hash(url, kwargs.get("params"))
        stored_re24 = Path(".", "tests", "data", "re24", f"{url_params}.json")
        if stored_re24.exists():
            return cast(Jsonable, json.loads(stored_re24.read_text()))
        else:
            data = (await _http_client.get(url, **kwargs)).json()
            stored_re24.write_text(json.dumps(data, indent=4, sort_keys=True))
            return cast(Jsonable, data)

    # The httpx typing is gross so let's just bodge it and carry on
    async def get(self, url: httpx.URL | str, **kwargs: Any) -> Coroutine[Any, Any, httpx.Response] | httpx.Response:  # type: ignore
        """
        Make an HTTP GET request to the relevant tariff, but actually load it from the file.

        Files are found in "get_tariff_from_file" and should be found in ./tests/data/{filename}.json
        with the slashes removed.

        Returns
        -------
            HTTPX status, 200 if file found, 404 otherwise.
        """
        print("Getting via mocked client", url)
        url = str(url)
        if url.startswith("https://api.octopus.energy/v1/products/"):
            maybe_tariff_data = await self.get_tariff_from_file(url, **kwargs)
            if maybe_tariff_data is not None:
                return httpx.Response(status_code=200, json=maybe_tariff_data)

        if url.startswith("https://api.carbonintensity.org.uk/regional/intensity/"):
            maybe_ci_data = await self.cache_ci_data(url, **kwargs)
            if maybe_ci_data is not None:
                return httpx.Response(status_code=200, json=maybe_ci_data)
        elif url.startswith("https://api.carbonintensity.org.uk/regional/"):
            return httpx.Response(
                status_code=200,
                json={
                    "data": [
                        {"regionid": 10, "dnoregion": "UKPN East", "shortname": "East England", "postcode": "SW1A", "data": []}
                    ]
                },
            )

        if str(url) == "https://www.gov.uk/bank-holidays.json":
            bank_holiday_path = Path(".", "tests", "data", "bank-holidays.json")
            return httpx.Response(status_code=200, json=json.loads(bank_holiday_path.read_text()))

        if url.startswith("https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"):
            maybe_vc_data = await self.cache_vc_data(url, **kwargs)
            if maybe_vc_data is not None:
                return httpx.Response(status_code=200, json=maybe_vc_data)

        if url.startswith("https://re.jrc.ec.europa.eu/api/PVcalc"):
            maybe_pvgis_data = await self.cache_pvgis_data(url, **kwargs)
            if maybe_pvgis_data is not None:
                return httpx.Response(status_code=200, json=maybe_pvgis_data)

        if url.startswith("https://www.renewables.ninja/api/"):
            maybe_rn_data = await self.cache_renewables_ninja_data(url, **kwargs)
            if maybe_rn_data is not None:
                return httpx.Response(status_code=200, json=maybe_rn_data)

        if url.startswith("https://api.re24.energy/v1/data/prices/nordpool"):
            maybe_re24_data = await self.cache_re24_data(url, **kwargs)
            if maybe_re24_data is not None:
                return httpx.Response(status_code=200, json=maybe_re24_data)
        return httpx.Response(status_code=404, text=f"Trying to get an unhandled URL with mock client: {url}")


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
