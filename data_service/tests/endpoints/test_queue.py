"""Test job queue handling, including the consumer process."""

import asyncio
import datetime
import json
from asyncio import Queue, create_task
from typing import cast

import httpx
import pytest
import pytest_asyncio

from app.dependencies import load_vae
from app.internal.epl_typing import Jsonable
from app.internal.gas_meters import parse_half_hourly
from app.internal.site_manager.bundles import insert_dataset_bundle
from app.internal.utils.uuid import uuid7
from app.job_queue import ASyncFunctionRequest, GenericJobRequest, SyncFunctionRequest, TerminateTaskGroup, process_jobs
from app.models.carbon_intensity import GridCO2Request
from app.models.core import BundleEntryMetadata, DatasetTypeEnum, SiteIDWithTime, dataset_id_t
from app.models.electricity_load import ElectricalLoadRequest
from app.models.heating_load import HeatingLoadRequest
from app.models.import_tariffs import TariffRequest
from app.models.renewables import RenewablesRequest, RenewablesWindRequest
from app.models.site_manager import DatasetBundleMetadata
from app.routers.site_manager import generate_all_queue

from .conftest import get_internal_client_hack, get_pool_hack

# Use this as a dummy object that just sleeps for a moment
DummyRequest = lambda dt=0.1: ASyncFunctionRequest(asyncio.sleep, dt)


@pytest_asyncio.fixture
async def upload_gas_data(client: httpx.AsyncClient) -> dict[str, Jsonable]:
    """Upload gas  meter data for use in heating load requests."""
    gas_data = parse_half_hourly("./tests/data/test_gas.csv")
    gas_data["start_ts"] = gas_data.index
    metadata = {"fuel_type": "gas", "site_id": "demo_london", "reading_type": "halfhourly"}
    records = json.loads(gas_data.to_json(orient="records"))
    gas_result = await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})
    assert gas_result.is_success
    return gas_result.json()


@pytest_asyncio.fixture
async def upload_elec_data(client: httpx.AsyncClient) -> dict[str, Jsonable]:
    """Upload meter data for use in electrical and heating load requests."""
    elec_data = parse_half_hourly("./tests/data/test_elec.csv")
    elec_data["start_ts"] = elec_data.index
    metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "halfhourly"}
    records = json.loads(elec_data.to_json(orient="records"))
    elec_result = await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})
    assert elec_result.is_success
    return elec_result.json()


@pytest.fixture
def queue_fixture() -> Queue:
    """Initialise an empty queue."""
    return Queue[GenericJobRequest]()


class TestQueue:
    """Test that the AsyncQueue works."""

    @pytest.mark.asyncio
    async def test_add_dummies_before_creation(self, queue_fixture: Queue) -> None:
        """Test that if we add a job before creation, it's processed."""
        await queue_fixture.put(DummyRequest())
        assert not queue_fixture.empty()
        consumer = asyncio.create_task(
            process_jobs(
                queue_fixture,
                pool=None,  # type: ignore
                http_client=None,  # type: ignore
                vae=None,  # type: ignore
                secrets_env=None,  # type: ignore
            )
        )
        await queue_fixture.join()
        consumer.cancel()

    @pytest.mark.asyncio
    async def test_add_dummies_after_creation(self, queue_fixture: Queue) -> None:
        """Test that if we add a job after creation, it's processed."""
        consumer = create_task(
            process_jobs(
                queue_fixture,
                pool=None,  # type: ignore
                http_client=None,  # type: ignore
                vae=None,  # type: ignore
                secrets_env=None,  # type: ignore
            )
        )
        await queue_fixture.put(DummyRequest())
        assert not queue_fixture.empty()
        await queue_fixture.join()
        consumer.cancel()

    @pytest.mark.asyncio
    async def test_add_many_dummies_after_creation(self, queue_fixture: Queue) -> None:
        """Test that if we add many jobs they're all handled ok."""
        for _ in range(3):
            await queue_fixture.put(DummyRequest(0.1))
        consumer = create_task(
            process_jobs(
                queue_fixture,
                pool=None,  # type: ignore
                http_client=None,  # type: ignore
                vae=None,  # type: ignore
                secrets_env=None,  # type: ignore
            )
        )
        for _ in range(3):
            await queue_fixture.put(DummyRequest(0.1))
        assert not queue_fixture.empty()
        await queue_fixture.join()
        consumer.cancel()

    @pytest.mark.asyncio
    async def test_multiple_consumers(self, queue_fixture: Queue) -> None:
        """Test that if we add many jobs they're all handled ok."""
        try:
            async with asyncio.TaskGroup() as tg:
                for _ in range(10):
                    await queue_fixture.put(DummyRequest(0.1))
                for consumer in range(3):
                    _ = tg.create_task(
                        process_jobs(
                            queue_fixture,
                            pool=None,  # type: ignore
                            http_client=None,  # type: ignore
                            vae=None,  # type: ignore
                            secrets_env=None,  # type: ignore
                            ignore_exceptions=True,
                        )
                    )
                for _ in range(10):
                    await queue_fixture.put(DummyRequest(0.1))
                await queue_fixture.join()
                raise TerminateTaskGroup()
        except* TerminateTaskGroup:
            pass

    @pytest.mark.asyncio
    async def test_handle_exception_before_creation(self, queue_fixture: Queue) -> None:
        """Test that if we add a job before creation that definitely fails."""

        def raise_error(msg: str) -> None:
            raise ValueError(msg)

        await queue_fixture.put(SyncFunctionRequest(raise_error, "EXPECTED"))
        assert not queue_fixture.empty()
        consumer = asyncio.create_task(
            process_jobs(
                queue_fixture,
                pool=None,  # type: ignore
                http_client=None,  # type: ignore
                vae=None,  # type: ignore
                secrets_env=None,  # type: ignore
                ignore_exceptions=False,
            )
        )
        await queue_fixture.join()
        assert consumer.exception() is not None
        assert isinstance(consumer.exception(), ValueError)
        assert "EXPECTED" in consumer.exception().args[0]  # type: ignore
        consumer.cancel()

    @pytest.mark.asyncio
    async def test_handle_two_exceptions(self, queue_fixture: Queue) -> None:
        """Test that if we add a job before creation that definitely fails in a TaskGroup."""

        def raise_error(msg: str) -> None:
            raise ValueError(msg)

        await queue_fixture.put(SyncFunctionRequest(raise_error, "1"))
        await queue_fixture.put(DummyRequest())
        await queue_fixture.put(SyncFunctionRequest(raise_error, "2"))
        assert not queue_fixture.empty()
        with pytest.raises(ExceptionGroup):
            async with asyncio.TaskGroup() as tg:
                consumer = tg.create_task(
                    process_jobs(
                        queue_fixture,
                        pool=None,  # type: ignore
                        http_client=None,  # type: ignore
                        vae=None,  # type: ignore
                        secrets_env=None,  # type: ignore
                        ignore_exceptions=False,
                    )
                )

    @pytest.mark.asyncio
    async def test_ignore_two_exceptions(self, queue_fixture: Queue) -> None:
        """Test that we can ignore multiple exceptions"""

        def raise_error(msg: str) -> None:
            raise ValueError(msg)

        await queue_fixture.put(SyncFunctionRequest(raise_error, "1"))
        await queue_fixture.put(DummyRequest())
        await queue_fixture.put(SyncFunctionRequest(raise_error, "2"))
        assert not queue_fixture.empty()

        try:
            async with asyncio.TaskGroup() as tg:
                _ = tg.create_task(
                    process_jobs(
                        queue_fixture,
                        pool=None,  # type: ignore
                        http_client=None,  # type: ignore
                        vae=None,  # type: ignore
                        secrets_env=None,  # type: ignore
                        ignore_exceptions=True,
                    )
                )
                await queue_fixture.join()
                raise TerminateTaskGroup()
        except* TerminateTaskGroup:
            pass

    @pytest.mark.asyncio
    async def test_handle_exception_with_good(self, queue_fixture: Queue) -> None:
        """Test that if we add a job before creation that definitely fails but we can handle a good one."""

        def raise_error(msg: str) -> None:
            raise ValueError(msg)

        await queue_fixture.put(DummyRequest())
        assert not queue_fixture.empty()
        consumer = asyncio.create_task(
            process_jobs(
                queue_fixture,
                pool=None,  # type: ignore
                http_client=None,  # type: ignore
                vae=None,  # type: ignore
                secrets_env=None,  # type: ignore
                ignore_exceptions=False,
            )
        )
        await queue_fixture.put(SyncFunctionRequest(raise_error, "EXPECTED"))
        await queue_fixture.join()
        assert consumer.exception() is not None
        assert isinstance(consumer.exception(), ValueError)
        assert "EXPECTED" in consumer.exception().args[0]
        consumer.cancel()


class TestQueueEndpoints:
    """Test queuing real tasks."""

    @pytest.mark.asyncio
    async def test_add_grid_co2(self, queue_fixture: Queue, client: httpx.AsyncClient) -> None:
        """Test that we successfully handled a queued grid CO2 request."""
        pool = await get_pool_hack(client)
        internal_client = get_internal_client_hack(client)
        bundle_id = uuid7()
        expected_id = uuid7()
        await insert_dataset_bundle(
            DatasetBundleMetadata(
                bundle_id=bundle_id,
                site_id="demo_london",
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=7, tzinfo=datetime.UTC),
            ),
            pool=pool,
        )
        await queue_fixture.put(
            GridCO2Request(
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=7, tzinfo=datetime.UTC),
                site_id="demo_london",
                bundle_metadata=BundleEntryMetadata(
                    bundle_id=bundle_id, dataset_id=expected_id, dataset_type=DatasetTypeEnum.CarbonIntensity
                ),
            )
        )
        assert not queue_fixture.empty()

        consumer = create_task(
            process_jobs(
                queue_fixture,
                pool=pool,
                http_client=internal_client,
                vae=None,  # type: ignore
                secrets_env=None,  # type: ignore
            )
        )

        await queue_fixture.join()
        consumer.cancel()
        is_in_db = await pool.fetchrow(
            """SELECT exists
                (SELECT 1
                FROM carbon_intensity.metadata
                WHERE dataset_id = $1)""",
            expected_id,
        )
        assert is_in_db is not None and is_in_db["exists"], "Not filed in DB"

    @pytest.mark.asyncio
    async def test_add_elec_load(
        self, queue_fixture: Queue, client: httpx.AsyncClient, upload_elec_data: dict[str, Jsonable]
    ) -> None:
        """Test that we successfully handled a queued electrical load request."""
        pool = await get_pool_hack(client)
        internal_client = get_internal_client_hack(client)
        bundle_id = uuid7()
        expected_id = uuid7()
        await insert_dataset_bundle(
            DatasetBundleMetadata(
                bundle_id=bundle_id,
                site_id="demo_london",
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=7, tzinfo=datetime.UTC),
            ),
            pool=pool,
        )
        await queue_fixture.put(
            ElectricalLoadRequest(
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=7, tzinfo=datetime.UTC),
                dataset_id=cast(dataset_id_t, upload_elec_data["dataset_id"]),
                bundle_metadata=BundleEntryMetadata(
                    bundle_id=bundle_id, dataset_id=expected_id, dataset_type=DatasetTypeEnum.ElectricityMeterDataSynthesised
                ),
            )
        )
        assert not queue_fixture.empty()

        try:
            async with asyncio.TaskGroup() as tg:
                _ = tg.create_task(
                    process_jobs(
                        queue_fixture,
                        pool=pool,  # type: ignore
                        http_client=internal_client,  # type: ignore
                        vae=load_vae(),  # type: ignore
                        secrets_env=None,  # type: ignore
                        ignore_exceptions=False,
                    )
                )
                await queue_fixture.join()
                raise TerminateTaskGroup()
        except* TerminateTaskGroup:
            pass

        is_in_db = await pool.fetchrow(
            """SELECT exists
                (SELECT 1
                FROM client_meters.metadata
                WHERE dataset_id = $1 AND fuel_type = 'elec' AND is_synthesised)""",
            expected_id,
        )
        print(is_in_db)
        assert is_in_db is not None and is_in_db["exists"], "Not filed in DB"

    @pytest.mark.asyncio
    async def test_add_heating_load(
        self, queue_fixture: Queue, client: httpx.AsyncClient, upload_gas_data: dict[str, Jsonable]
    ) -> None:
        """Test that we successfully handled a queued heating load request."""
        pool = await get_pool_hack(client)
        internal_client = get_internal_client_hack(client)
        bundle_id = uuid7()
        expected_id = uuid7()
        await insert_dataset_bundle(
            DatasetBundleMetadata(
                bundle_id=bundle_id,
                site_id="demo_london",
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=7, tzinfo=datetime.UTC),
            ),
            pool=pool,
        )
        await queue_fixture.put(
            HeatingLoadRequest(
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=7, tzinfo=datetime.UTC),
                dataset_id=cast(dataset_id_t, upload_gas_data["dataset_id"]),
                bundle_metadata=BundleEntryMetadata(
                    bundle_id=bundle_id, dataset_id=expected_id, dataset_type=DatasetTypeEnum.HeatingLoad
                ),
            )
        )
        assert not queue_fixture.empty()

        try:
            async with asyncio.TaskGroup() as tg:
                _ = tg.create_task(
                    process_jobs(
                        queue_fixture,
                        pool=pool,  # type: ignore
                        http_client=internal_client,  # type: ignore
                        vae=None,  # type: ignore
                        secrets_env=None,  # type: ignore
                        ignore_exceptions=False,
                    )
                )
                await queue_fixture.join()
                raise TerminateTaskGroup()
        except* TerminateTaskGroup:
            pass

        is_in_db = await pool.fetchrow(
            """SELECT exists
                (SELECT 1
                FROM heating.metadata
                WHERE dataset_id = $1)""",
            expected_id,
        )
        assert is_in_db is not None and is_in_db["exists"], "Not filed in DB"

    @pytest.mark.asyncio
    async def test_add_import_tariff(self, queue_fixture: Queue, client: httpx.AsyncClient) -> None:
        """Test that we successfully handled a queued import tariff request."""
        pool = await get_pool_hack(client)
        internal_client = get_internal_client_hack(client)
        bundle_id = uuid7()
        expected_id = uuid7()
        await insert_dataset_bundle(
            DatasetBundleMetadata(
                bundle_id=bundle_id,
                site_id="demo_london",
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=7, tzinfo=datetime.UTC),
            ),
            pool=pool,
        )
        await queue_fixture.put(
            TariffRequest(
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=7, tzinfo=datetime.UTC),
                tariff_name="fixed",
                site_id="demo_london",
                bundle_metadata=BundleEntryMetadata(
                    bundle_id=bundle_id, dataset_id=expected_id, dataset_type=DatasetTypeEnum.ImportTariff
                ),
            )
        )
        assert not queue_fixture.empty()

        try:
            async with asyncio.TaskGroup() as tg:
                _ = tg.create_task(
                    process_jobs(
                        queue_fixture,
                        pool=pool,  # type: ignore
                        http_client=internal_client,  # type: ignore
                        vae=None,  # type: ignore
                        secrets_env=None,  # type: ignore
                        ignore_exceptions=False,
                    )
                )
                await queue_fixture.join()
                raise TerminateTaskGroup()
        except* TerminateTaskGroup:
            pass

        is_in_db = await pool.fetchrow(
            """SELECT exists
                (SELECT 1
                FROM tariffs.metadata
                WHERE dataset_id = $1)""",
            expected_id,
        )
        assert is_in_db is not None and is_in_db["exists"], "Not filed in DB"

    @pytest.mark.asyncio
    async def test_add_renewables(self, queue_fixture: Queue, client: httpx.AsyncClient) -> None:
        """Test that we successfully handled a queued renewables request."""
        pool = await get_pool_hack(client)
        internal_client = get_internal_client_hack(client)
        bundle_id = uuid7()
        expected_id = uuid7()
        await insert_dataset_bundle(
            DatasetBundleMetadata(
                bundle_id=bundle_id,
                site_id="demo_london",
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=7, tzinfo=datetime.UTC),
            ),
            pool=pool,
        )
        await queue_fixture.put(
            RenewablesRequest(
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=7, tzinfo=datetime.UTC),
                site_id="demo_london",
                azimuth=135,
                tilt=37.1,
                bundle_metadata=BundleEntryMetadata(
                    bundle_id=bundle_id, dataset_id=expected_id, dataset_type=DatasetTypeEnum.RenewablesGeneration
                ),
            )
        )
        assert not queue_fixture.empty()

        try:
            async with asyncio.TaskGroup() as tg:
                _ = tg.create_task(
                    process_jobs(
                        queue_fixture,
                        pool=pool,  # type: ignore
                        http_client=internal_client,  # type: ignore
                        vae=None,  # type: ignore
                        secrets_env=None,  # type: ignore
                        ignore_exceptions=False,
                    )
                )
                await queue_fixture.join()
                raise TerminateTaskGroup()
        except* TerminateTaskGroup:
            pass

        is_in_db = await pool.fetchrow(
            """SELECT exists
                (SELECT 1
                FROM renewables.metadata
                WHERE dataset_id = $1)""",
            expected_id,
        )
        assert is_in_db is not None and is_in_db["exists"], "Not filed in DB"

    @pytest.mark.asyncio
    async def test_add_wind_renewables(self, queue_fixture: Queue, client: httpx.AsyncClient) -> None:
        """Test that we successfully handled a queued wind renewables request."""
        pool = await get_pool_hack(client)
        internal_client = get_internal_client_hack(client)
        bundle_id = uuid7()
        expected_id = uuid7()
        await insert_dataset_bundle(
            DatasetBundleMetadata(
                bundle_id=bundle_id,
                site_id="demo_london",
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=7, tzinfo=datetime.UTC),
            ),
            pool=pool,
        )
        await queue_fixture.put(
            RenewablesWindRequest(
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=7, tzinfo=datetime.UTC),
                site_id="demo_london",
                height=10.0,
                turbine="Alstom Eco 110",
                bundle_metadata=BundleEntryMetadata(
                    bundle_id=bundle_id, dataset_id=expected_id, dataset_type=DatasetTypeEnum.RenewablesGeneration
                ),
            )
        )
        assert not queue_fixture.empty()

        try:
            async with asyncio.TaskGroup() as tg:
                _ = tg.create_task(
                    process_jobs(
                        queue_fixture,
                        pool=pool,  # type: ignore
                        http_client=internal_client,  # type: ignore
                        vae=None,  # type: ignore
                        secrets_env=None,  # type: ignore
                        ignore_exceptions=False,
                    )
                )
                await queue_fixture.join()
                raise TerminateTaskGroup()
        except* TerminateTaskGroup:
            pass

        is_in_db = await pool.fetchrow(
            """SELECT exists
                (SELECT 1
                FROM renewables.metadata
                WHERE dataset_id = $1)""",
            expected_id,
        )
        assert is_in_db is not None and is_in_db["exists"], "Not filed in DB"


class TestGenerateAllQueue:
    """Test that we can queue all requests"""

    @pytest.mark.asyncio
    async def test_call_directly(
        self,
        upload_gas_data: dict[str, Jsonable],
        upload_elec_data: dict[str, Jsonable],
        queue_fixture: Queue,
        client: httpx.AsyncClient,
    ) -> None:
        pool = await get_pool_hack(client)
        vae = load_vae()
        internal_client = get_internal_client_hack(client)
        _ = await generate_all_queue(
            params=SiteIDWithTime(
                site_id="demo_london",
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=1, day=8, tzinfo=datetime.UTC),
            ),
            pool=pool,
            queue=queue_fixture,
        )
        try:
            async with asyncio.TaskGroup() as tg:
                _ = tg.create_task(
                    process_jobs(
                        queue_fixture,
                        pool=pool,  # type: ignore
                        http_client=internal_client,  # type: ignore
                        vae=vae,  # type: ignore
                        secrets_env=None,  # type: ignore
                        ignore_exceptions=False,
                    )
                )
                await queue_fixture.join()
                raise TerminateTaskGroup()
        except* TerminateTaskGroup:
            pass


class TestGenerateAllQueue:
    """Test that we can queue all requests"""

    @pytest.mark.asyncio
    async def test_call_endpoint(
        self,
        upload_gas_data: dict[str, Jsonable],
        upload_elec_data: dict[str, Jsonable],
        queue_fixture: Queue,
        client: httpx.AsyncClient,
    ) -> None:
        pool = await get_pool_hack(client)
        vae = load_vae()
        internal_client = get_internal_client_hack(client)
        params = SiteIDWithTime(
            site_id="demo_london",
            start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
            end_ts=datetime.datetime(year=2022, month=1, day=8, tzinfo=datetime.UTC),
        )
        response = await client.post("generate-all-queue", json=params.model_dump_json())
