"""Tests for renewables generation endpoints."""

# ruff: noqa: D101, D102, D103
import datetime
import json
from typing import cast
from uuid import UUID

import httpx
import numpy as np
import pandas as pd
import pytest
import pytest_asyncio

from app.dependencies import get_db_pool, get_http_client
from app.internal.epl_typing import Jsonable
from app.internal.gas_meters import parse_half_hourly
from app.internal.pvgis import get_pvgis_optima
from app.internal.solar_pv.disaggregate import disaggregate_readings
from app.internal.utils.uuid import uuid7


@pytest_asyncio.fixture
async def upload_hh_meter_data(client: httpx.AsyncClient) -> dict[str, Jsonable]:
    elec_data = parse_half_hourly("./tests/data/test_elec.csv")
    elec_data["start_ts"] = elec_data.index
    metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "halfhourly"}
    records = json.loads(elec_data.to_json(orient="records"))
    elec_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

    return cast(dict[str, Jsonable], elec_result)


@pytest_asyncio.fixture
async def upload_monthly_meter_data(client: httpx.AsyncClient) -> dict[str, Jsonable]:
    elec_data = parse_half_hourly("./tests/data/test_elec.csv")

    elec_data = elec_data.resample(pd.Timedelta(days=28)).sum(numeric_only=True)
    elec_data["start_ts"] = elec_data.index
    elec_data["end_ts"] = elec_data.index + pd.Timedelta(days=28)
    metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "manual"}
    records = json.loads(elec_data.to_json(orient="records"))
    elec_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

    return cast(dict[str, Jsonable], elec_result)


@pytest.fixture
def demo_start_ts() -> datetime.datetime:
    return datetime.datetime(year=2020, month=1, day=1, hour=0, minute=0, second=0, tzinfo=datetime.UTC)


@pytest.fixture
def demo_end_ts() -> datetime.datetime:
    return datetime.datetime(year=2021, month=1, day=1, hour=0, minute=0, second=0, tzinfo=datetime.UTC)


class TestRenewables:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_renewables_metadata(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        earliest_possible = datetime.datetime.now(datetime.UTC)
        result = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": 178,
                    "tilt": 30,
                    "tracking": False,
                },
            )
        ).json()
        created_at = datetime.datetime.fromisoformat(result["created_at"])
        assert "dataset_id" in result
        assert earliest_possible <= created_at
        assert created_at <= datetime.datetime.now(datetime.UTC)

        assert result["parameters"]["azimuth"] == 178
        assert result["parameters"]["tilt"] == 30
        assert result["site_id"] == "demo_london"

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_renewables_without_optima(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        result = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": None,
                    "tilt": None,
                    "tracking": False,
                },
            )
        ).json()
        assert "dataset_id" in result
        assert (
            datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=1)
            <= datetime.datetime.fromisoformat(result["created_at"])
            <= datetime.datetime.now(datetime.UTC)
        )
        assert result["parameters"]["azimuth"] == pytest.approx(176, rel=5)
        assert result["parameters"]["tilt"] == pytest.approx(40, rel=5)
        assert result["site_id"] == "demo_london"

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_and_get_renewables(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        metadata = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": None,
                    "tilt": None,
                    "tracking": False,
                },
            )
        ).json()
        results = (
            await client.post(
                "/get-renewables-generation",
                json={
                    "dataset_id": metadata["dataset_id"],
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
            )
        ).json()

        assert all(
            len(results["timestamps"])
            == len(item)
            == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
            for item in results["data"]
        )
        assert all(all(item) >= 0 for item in results["data"])

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_default_location(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        """Test that we can generate a solar array in the `default` location."""
        locn_metadata = await client.post(
            "/add-solar-location",
            json={
                "site_id": "demo_london",
                "renewables_location_id": "demo_london_southroof",
                "name": "Matt's South Roof",
                "azimuth": 153,
                "tilt": 35,
                "maxpower": 5.0,
            },
        )
        assert locn_metadata.status_code == 200

        metadata = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": None,
                    "tilt": None,
                    "tracking": False,
                    "renewables_location_id": "demo_london_southroof",
                },
            )
        ).json()
        results = (
            await client.post(
                "/get-renewables-generation",
                json={
                    "dataset_id": metadata["dataset_id"],
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
            )
        ).json()

        assert all(
            len(results["timestamps"])
            == len(item)
            == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
            for item in results["data"]
        )
        assert all(all(item) >= 0 for item in results["data"])

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_and_get_renewables_not_full_year(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        start_ts = demo_start_ts - datetime.timedelta(days=99)
        end_ts = demo_end_ts - datetime.timedelta(days=101)
        metadata = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": start_ts.isoformat(),
                    "end_ts": end_ts.isoformat(),
                    "azimuth": None,
                    "tilt": None,
                    "tracking": False,
                },
            )
        ).json()
        results = (
            await client.post(
                "/get-renewables-generation",
                json={
                    "dataset_id": metadata["dataset_id"],
                    "start_ts": start_ts.isoformat(),
                    "end_ts": end_ts.isoformat(),
                },
            )
        ).json()

        assert all(
            len(results["timestamps"])
            == len(item)
            == (end_ts - start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
            for item in results["data"]
        )
        assert all(results["data"][0]) >= 0


class TestMultipleRenewables:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_and_get_repeated(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        """Test that we can get many copies of the same dataset."""
        metadata = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": None,
                    "tilt": None,
                    "tracking": False,
                },
            )
        ).json()
        results = (
            await client.post(
                "/get-renewables-generation",
                json={
                    "dataset_id": [metadata["dataset_id"] for _ in range(4)],
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
            )
        ).json()

        assert all(
            len(results["timestamps"])
            == len(item)
            == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
            for item in results["data"]
        )
        assert all(all(item) >= 0 for item in results["data"])
        assert all(item == results["data"][0] for item in results["data"])

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_and_get_different(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        """Test that we can get many copies of the same dataset."""
        metadata_1 = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": 175,
                    "tilt": 35,
                    "tracking": False,
                },
            )
        ).json()

        metadata_2 = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": 190,
                    "tilt": 45,
                    "tracking": True,
                },
            )
        ).json()
        results = (
            await client.post(
                "/get-renewables-generation",
                json={
                    "dataset_id": [metadata_1["dataset_id"], metadata_2["dataset_id"]],
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
            )
        ).json()

        assert all(
            len(results["timestamps"])
            == len(item)
            == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
            for item in results["data"]
        )
        assert all(all(item) >= 0 for item in results["data"])
        assert all(any(item) > 0 for item in results["data"])
        assert not all(item == results["data"][0] for item in results["data"])


class TestRenewablesErrors:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_useful_error_messages(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        """Test that we can get many copies of the same dataset."""
        bad_uuid = uuid7()
        results = await client.post(
            "/get-renewables-generation",
            json={
                "dataset_id": str(bad_uuid),
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )

        assert results.status_code == 400
        assert "dataset_id" in results.json()["detail"]
        assert str(bad_uuid) in results.json()["detail"]


class TestPVGIS:
    @pytest.mark.external
    @pytest.mark.asyncio
    async def test_pvgis_optima(self, client: httpx.AsyncClient) -> None:
        """That that we can get PVGIS optima without an error."""
        external_client = client._transport.app.dependency_overrides[get_http_client]()  # type: ignore
        result = await get_pvgis_optima(external_client, latitude=51.0, longitude=0.10, tracking=False)
        assert result.tilt == 39
        assert result.altitude == 61.0
        assert result.azimuth == 180


class TestWindRenewables:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_renewables_wind(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        result = (
            await client.post(
                "/generate-wind-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "height": 80,
                    "turbine": "Enercon E101 3000",
                },
            )
        ).json()
        assert "dataset_id" in result
        assert (
            datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=1)
            <= datetime.datetime.fromisoformat(result["created_at"])
            <= datetime.datetime.now(datetime.UTC)
        )
        assert result["parameters"]["height"] == 80
        assert result["parameters"]["turbine"] == "Enercon E101 3000"
        assert result["site_id"] == "demo_london"


class TestDisaggregate:
    @pytest.mark.external
    @pytest.mark.asyncio
    async def test_can_disaggregate_hh(self, client: httpx.AsyncClient, upload_hh_meter_data: dict[str, Jsonable]) -> None:
        """Test that we can do sensible disaggregration for halfhourly data."""
        elec_meter_meta = upload_hh_meter_data

        # The HTTP client we pass as a fixture is only useful for accessing endpoints and creates
        # a mocked HTTP client for external use; the pool is spun up per test.
        pool = await client._transport.app.dependency_overrides[get_db_pool]().__anext__()  # type: ignore
        external_client = client._transport.app.dependency_overrides[get_http_client]()  # type: ignore
        disaggregated_df = await disaggregate_readings(
            elec_meter_dataset_id=cast(UUID, elec_meter_meta["dataset_id"]),
            azimuth=None,
            tilt=None,
            pool=pool,
            http_client=external_client,
            system_size=1.0,
        )
        assert not disaggregated_df.empty
        assert ~np.any(np.isnan(disaggregated_df["consumption_kwh"])), "Disaggregated entry is NaN"
        assert np.any(disaggregated_df["consumption_kwh"] > disaggregated_df["import"]), "At least one reading must be higher"
        assert np.all(disaggregated_df["consumption_kwh"] >= disaggregated_df["import"]), "No readings may be lower"

    @pytest.mark.external
    @pytest.mark.asyncio
    async def test_can_disaggregate_monthly(
        self, client: httpx.AsyncClient, upload_monthly_meter_data: dict[str, Jsonable]
    ) -> None:
        """Test that we get monthly disaggregation correct."""
        elec_meter_meta = upload_monthly_meter_data

        # The HTTP client we pass as a fixture is only useful for accessing endpoints and creates
        # a mocked HTTP client for external use; the pool is spun up per test.
        pool = await client._transport.app.dependency_overrides[get_db_pool]().__anext__()  # type: ignore
        external_client = client._transport.app.dependency_overrides[get_http_client]()  # type: ignore
        disaggregated_df = await disaggregate_readings(
            elec_meter_dataset_id=cast(UUID, elec_meter_meta["dataset_id"]),
            azimuth=None,
            tilt=None,
            pool=pool,
            http_client=external_client,
            system_size=1.0,
        )
        assert not disaggregated_df.empty
        assert ~np.any(np.isnan(disaggregated_df["consumption_kwh"])), "Disaggregated entry is NaN"
        assert np.any(disaggregated_df["consumption_kwh"] > disaggregated_df["import"]), "At least one reading must be higher"
        assert np.all(disaggregated_df["consumption_kwh"] >= disaggregated_df["import"]), "No readings may be lower"

    @pytest.mark.external
    @pytest.mark.asyncio
    async def test_disagg_scales(self, client: httpx.AsyncClient, upload_monthly_meter_data: dict[str, Jsonable]) -> None:
        """Test that the disaggregation scales with the system size."""
        elec_meter_meta = upload_monthly_meter_data

        # The HTTP client we pass as a fixture is only useful for accessing endpoints and creates
        # a mocked HTTP client for external use; the pool is spun up per test.
        pool = await client._transport.app.dependency_overrides[get_db_pool]().__anext__()  # type: ignore
        external_client = client._transport.app.dependency_overrides[get_http_client]()  # type: ignore
        disaggregated_df = await disaggregate_readings(
            elec_meter_dataset_id=cast(UUID, elec_meter_meta["dataset_id"]),
            azimuth=None,
            tilt=None,
            pool=pool,
            http_client=external_client,
            system_size=1.0,
        )
        disaggregated_big_df = await disaggregate_readings(
            elec_meter_dataset_id=cast(UUID, elec_meter_meta["dataset_id"]),
            azimuth=None,
            tilt=None,
            pool=pool,
            http_client=external_client,
            system_size=10.0,
        )
        assert not disaggregated_df.empty
        assert np.any(disaggregated_big_df["consumption_kwh"] > disaggregated_df["consumption_kwh"]), (
            "At least one reading must be higher"
        )
        assert np.all(disaggregated_big_df["consumption_kwh"] >= disaggregated_df["consumption_kwh"]), (
            "At least one reading must be higher"
        )
