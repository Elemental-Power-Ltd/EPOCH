import asyncio
import datetime
import json
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pandas.core.api import DataFrame as DataFrame

from app.dependencies import CachedAsyncClient, HTTPClient, Jsonable, get_http_client, get_queue, url_to_hash
from app.internal.database.utils import _DB_URL
from app.internal.queue import IQueue
from app.internal.task_processor import process_tasks
from app.main import app
from app.models.constraints import Constraints
from app.models.core import Site, Task
from app.models.metrics import Metric
from app.models.optimisers import (
    NSGA2HyperParam,
    NSGA2Optimiser,
    OptimiserStr,
)

_http_client = AsyncClient(headers=[("Connection", "close")], timeout=60.0)


@pytest.fixture(scope="session")
def result_tmp_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("results")


class MockedHttpClient(CachedAsyncClient):
    """An overridden HTTP client that gets responses from JSON files."""

    def __init__(self, tmp_path: Path, **kwargs: Any):
        self.tmp_path = tmp_path
        super().__init__(**kwargs)

    def transmit_results(self, **kwargs: Any) -> None:
        result = kwargs.get("json")
        with open(Path(self.tmp_path, f"{result['tasks']['task_id']}.json"), "w") as f:  # type: ignore
            json.dump(kwargs.get("json"), f)

    async def get_result_configuration(self, url: str, **kwargs: Any) -> Jsonable:
        url_params = url_to_hash(url, kwargs.get("json"))
        storage_path = Path(".", "tests", "data", "result_configuration")
        storage_path.mkdir(parents=True, exist_ok=True)
        stored_result_configuration = Path(storage_path, f"{url_params}.json")
        if stored_result_configuration.exists():
            return cast(Jsonable, json.loads(stored_result_configuration.read_text()))
        else:
            data = (await _http_client.post(url, **kwargs)).json()
            stored_result_configuration.write_text(json.dumps(data, indent=4, sort_keys=True))
            return cast(Jsonable, data)

    def transmit_task(self) -> None:
        pass

    async def get_dataset_bundles_list(self, url: str, **kwargs: Any) -> Jsonable:
        url_params = url_to_hash(url, kwargs.get("json"))
        storage_path = Path(".", "tests", "data", "list_dataset_bundles")
        storage_path.mkdir(parents=True, exist_ok=True)
        stored_dataset_bundles_list = Path(storage_path, f"{url_params}.json")
        if stored_dataset_bundles_list.exists():
            return cast(Jsonable, json.loads(stored_dataset_bundles_list.read_text()))
        else:
            data = (await _http_client.post(url, **kwargs)).json()
            stored_dataset_bundles_list.write_text(json.dumps(data, indent=4, sort_keys=True))
            return cast(Jsonable, data)

    async def get_dataset_bundle(self, url: str, **kwargs: Any) -> Jsonable:
        url_params = url_to_hash(url, kwargs.get("params"))
        storage_path = Path(".", "tests", "data", "get_dataset_bundle")
        storage_path.mkdir(parents=True, exist_ok=True)
        stored_dataset_bundle = Path(storage_path, f"{url_params}.json")
        if stored_dataset_bundle.exists():
            return cast(Jsonable, json.loads(stored_dataset_bundle.read_text()))
        else:
            data = (await _http_client.post(url, **kwargs)).json()
            stored_dataset_bundle.write_text(json.dumps(data, indent=4, sort_keys=True))
            return cast(Jsonable, data)

    async def get_bundle_contents_list(self, url: str, **kwargs: Any) -> Jsonable:
        url_params = url_to_hash(url, kwargs.get("params"))
        storage_path = Path(".", "tests", "data", "list_bundle_contents")
        storage_path.mkdir(parents=True, exist_ok=True)
        stored_bundle_contents_list = Path(storage_path, f"{url_params}.json")
        if stored_bundle_contents_list.exists():
            return cast(Jsonable, json.loads(stored_bundle_contents_list.read_text()))
        else:
            data = (await _http_client.post(url, **kwargs)).json()
            stored_bundle_contents_list.write_text(json.dumps(data, indent=4, sort_keys=True))
            return cast(Jsonable, data)

    async def get_specific_datasets(self, url: str, **kwargs: Any) -> Jsonable:
        url_params = url_to_hash(url, kwargs.get("json"))
        storage_path = Path(".", "tests", "data", "get_specific_datasets")
        storage_path.mkdir(parents=True, exist_ok=True)
        stored_specific_datasets = Path(storage_path, f"{url_params}.json")
        if stored_specific_datasets.exists():
            return cast(Jsonable, json.loads(stored_specific_datasets.read_text()))
        else:
            data = (await _http_client.post(url, **kwargs)).json()
            stored_specific_datasets.write_text(json.dumps(data, indent=4, sort_keys=True))
            return cast(Jsonable, data)

    async def post(self, url: str | httpx._urls.URL, **kwargs: Any) -> httpx._models.Response:
        """Mock known posts requests by loading the data from files."""

        url = str(url)

        if url == _DB_URL + "/add-optimisation-results":
            self.transmit_results(**kwargs)
            return httpx.Response(status_code=200)

        elif url == _DB_URL + "/get-result-configuration":
            stored_result_configuration = await self.get_result_configuration(url=url, **kwargs)
            return httpx.Response(status_code=200, json=stored_result_configuration)

        elif url == _DB_URL + "/add-optimisation-task":
            self.transmit_task()
            return httpx.Response(status_code=200)

        elif url == _DB_URL + "/list-dataset-bundles":
            stored_dataset_bundles_list = await self.get_dataset_bundles_list(url=url, **kwargs)
            return httpx.Response(status_code=200, json=stored_dataset_bundles_list)

        elif url == _DB_URL + "/get-dataset-bundle":
            stored_dataset_bundle = await self.get_dataset_bundle(url=url, **kwargs)
            return httpx.Response(status_code=200, json=stored_dataset_bundle)

        elif url == _DB_URL + "/list-bundle-contents":
            stored_bundle_contents_list = await self.get_bundle_contents_list(url=url, **kwargs)
            return httpx.Response(status_code=200, json=stored_bundle_contents_list)

        elif url == _DB_URL + "/get-specific-datasets":
            stored_specific_datasets = await self.get_specific_datasets(url=url, **kwargs)
            return httpx.Response(status_code=200, json=stored_specific_datasets)

        return httpx.Response(status_code=400, text="No matching URL mock found.")


@pytest_asyncio.fixture()
async def client(result_tmp_path: Path) -> AsyncGenerator[AsyncClient]:
    def override_get_http_client() -> HTTPClient:
        """
        Override the HTTP client with a functional local http client.

        If we re-use the same HTTPX AsyncClient then we cause trouble with AsyncIO, causing
        `RuntimeError: Event loop is closed" issues.
        """
        # Use the 'Connection Close' headers to suppress httpx's connection pooling, as
        # it'll helpfully try to reuse a connection between event loops and then fall over.
        return MockedHttpClient(tmp_path=result_tmp_path)

    queue = IQueue(maxsize=20)

    def override_get_queue() -> IQueue:
        return queue

    app.dependency_overrides[get_http_client] = override_get_http_client
    app.dependency_overrides[get_queue] = override_get_queue

    app.state.start_time = datetime.datetime.now(datetime.UTC)

    async with (
        AsyncClient(
            transport=ASGITransport(app),
            base_url="http://localhost",
        ) as client,
        asyncio.TaskGroup() as tg,
    ):
        # We also have to set up the queue handling task
        task = tg.create_task(
            process_tasks(
                queue=queue,
                http_client=override_get_http_client(),
            )
        )
        yield client
        try:
            await asyncio.wait_for(queue.join(), timeout=10.0)
        except TimeoutError:
            print("Failed to shutdown queue.")
        task.cancel()


def get_internal_client_hack(client: httpx.AsyncClient) -> MockedHttpClient:
    """
    Get the demo HTTP client that will maybe draw from a cache.

    This hack was implemented on 18-09-2025, please replace with a proper fixture in the future.

    Parameters
    ----------
    client
        The mocked test client

    Returns
    -------
    MockedHttpClient
        Mocked HTTP client that will get from a cache if needed
    """
    from app.dependencies import get_http_client

    return client._transport.app.dependency_overrides[get_http_client]()  # type: ignore


@pytest.fixture
def default_optimiser() -> NSGA2Optimiser:
    return NSGA2Optimiser(
        name=OptimiserStr.NSGA2, hyperparameters=NSGA2HyperParam(pop_size=512, n_offsprings=256, n_max_gen=10, period=8)
    )


@pytest.fixture
def default_task(
    default_objectives: list[Metric],
    default_optimiser: NSGA2Optimiser,
    default_portfolio: list[Site],
    default_constraints: Constraints,
) -> Task:
    return Task(
        name="test",
        optimiser=default_optimiser,
        objectives=default_objectives,
        portfolio=default_portfolio,
        client_id="demo",
        portfolio_constraints=default_constraints,
        epoch_version="0.0.1",
    )
