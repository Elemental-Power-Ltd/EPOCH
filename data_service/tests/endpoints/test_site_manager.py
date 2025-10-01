"""Test that the generate all function works."""

# ruff: noqa: D101, D102, D103
import asyncio
import datetime
import json
import uuid

import httpx
import numpy as np
import pytest
import pytest_asyncio

from app.internal.epl_typing import Jsonable
from app.internal.gas_meters import parse_half_hourly
from app.internal.site_manager.bundles import insert_dataset_bundle
from app.internal.utils.uuid import uuid7
from app.models.heating_load import InterventionEnum
from app.models.site_manager import DatasetBundleMetadata
from app.routers.site_manager import get_bundle_hints

from .conftest import get_pool_hack


@pytest_asyncio.fixture
async def upload_meter_data(client: httpx.AsyncClient) -> tuple[dict[str, Jsonable], dict[str, Jsonable]]:
    elec_data = parse_half_hourly("./tests/data/test_elec.csv")
    elec_data["start_ts"] = elec_data.index
    metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "halfhourly"}
    records = json.loads(elec_data.to_json(orient="records"))
    elec_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

    gas_data = parse_half_hourly("./tests/data/test_gas.csv")
    gas_data["start_ts"] = gas_data.index
    metadata = {"fuel_type": "gas", "site_id": "demo_london", "reading_type": "halfhourly"}
    records = json.loads(gas_data.to_json(orient="records"))
    gas_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

    return gas_result, elec_result


class TestGetMultipleTariffs:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_and_get_multiple_tariffs(self, client: httpx.AsyncClient) -> None:
        start_ts = datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2022, month=2, day=1, tzinfo=datetime.UTC)
        site_id = "demo_london"

        bundle_id = str(uuid7())
        bundle_resp = await client.post(
            "/create-bundle",
            json={
                "bundle_id": bundle_id,
                "name": "test_generate_and_get_multiple_tariffs",
                "site_id": "demo_london",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert bundle_resp.is_success

        async with asyncio.TaskGroup() as tg:
            # We generate four different types of tariff, here done manually to keep track of the
            # tasks and not lose the handle to the task (which causes mysterious bugs)
            import_tariff_response_fixed = tg.create_task(
                client.post(
                    "/generate-import-tariffs",
                    json={
                        "site_id": site_id,
                        "tariff_name": "fixed",
                        "start_ts": start_ts.isoformat(),
                        "end_ts": end_ts.isoformat(),
                        "bundle_metadata": {
                            "bundle_id": bundle_id,
                            "dataset_id": str(uuid7()),
                            "dataset_type": "ImportTariff",
                            "dataset_subtype": "fixed",
                        },
                    },
                )
            )
            import_tariff_response_agile = tg.create_task(
                client.post(
                    "/generate-import-tariffs",
                    json={
                        "site_id": site_id,
                        "tariff_name": "agile",
                        "start_ts": start_ts.isoformat(),
                        "end_ts": end_ts.isoformat(),
                        "bundle_metadata": {
                            "bundle_id": bundle_id,
                            "dataset_id": str(uuid7()),
                            "dataset_type": "ImportTariff",
                            "dataset_subtype": "agile",
                        },
                    },
                )
            )
        assert import_tariff_response_fixed.result().status_code == 200
        assert import_tariff_response_agile.result().status_code == 200

        # Test that we get two datasets, one for fixed and one for agile
        all_datasets_response = await client.post(
            "/list-latest-datasets",
            json={"site_id": "demo_london", "start_ts": start_ts.isoformat(), "end_ts": end_ts.isoformat()},
        )
        assert all_datasets_response.is_success, all_datasets_response.text
        all_json = all_datasets_response.json()
        assert len(all_json["ImportTariff"]) == 2

        get_datasets_response = await client.post(
            "/get-dataset-bundle",
            params={
                "bundle_id": bundle_id,
            },
        )
        assert get_datasets_response.is_success, get_datasets_response.text
        got_datasets = get_datasets_response.json()
        tariff_data = got_datasets["import_tariffs"]["data"]
        assert all(all(np.isfinite(item)) for item in tariff_data), "Tariff is empty or NaN"

        # These shouldn't be identical
        assert any(x != y for x, y in zip(tariff_data[0], tariff_data[1], strict=True))


class TestGenerateAll:
    @pytest.mark.slow
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_all_same_length(
        self, client: httpx.AsyncClient, upload_meter_data: tuple[dict[str, Jsonable], dict[str, Jsonable]]
    ) -> None:
        _, _ = upload_meter_data
        demo_start_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
        demo_end_ts = datetime.datetime(year=2020, month=2, day=1, tzinfo=datetime.UTC)

        solar_data = {
            "site_id": "demo_london",
            "name": "Main Roof",
            "renewables_location_id": "demo_london_mainroof",
            "tilt": 35,
            "azimuth": 178,
            "maxpower": 6.0,
        }
        add_response = await client.post("/add-solar-location", json=solar_data)
        assert add_response.status_code == 200, add_response.text

        solar_data_2 = {
            "site_id": "demo_london",
            "name": "North Roof",
            "renewables_location_id": "demo_london_northroof",
            "tilt": 35,
            "azimuth": 345,
            "maxpower": 6.0,
        }
        add_response = await client.post("/add-solar-location", json=solar_data_2)
        assert add_response.status_code == 200, add_response.text
        response = await client.post(
            "/add-site-baseline",
            json={
                "site_id": {"site_id": "demo_london"},
                "baseline": {
                    "building": {"floor_area": 89.0},
                },
            },
        )
        FIXED_TARIFF_COSTS = 100.0
        assert response.is_success
        baseline_id = response.json()
        response = await client.post(
            "/add-baseline-tariff",
            json={
                "tariff_req": {
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "tariff_name": "fixed",
                    "day_cost": FIXED_TARIFF_COSTS,
                },
                "baseline_id": {"dataset_id": baseline_id},
            },
        )

        response = await client.post(
            "/add-feasible-interventions",
            json={
                "site_id": {"site_id": "demo_london"},
                "interventions": ["loft", "cladding"],
            },
        )
        assert response.is_success, response.text
        assert len(response.json()) == 4, response.text

        generate_result = await client.post(
            "/generate-all",
            json={
                "site_id": "demo_london",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )

        assert generate_result.status_code == 200, generate_result.text
        # Check that they're all generated
        bundle_id = generate_result.json()["bundle_id"]
        start_time = datetime.datetime.now(datetime.UTC)
        timeout = datetime.timedelta(minutes=5)
        while True:
            q_resp = await client.post("list-bundle-contents", params={"bundle_id": bundle_id})
            assert q_resp.is_success, q_resp.text
            data = q_resp.json()

            if data["is_error"]:
                pytest.fail("Bundle creation failed")

            if data["is_complete"]:
                # Job done, the bundle is ready
                break
            # This is our backup bailout clause to prevent the tests
            # hanging
            await asyncio.sleep(1.0)
            if datetime.datetime.now(datetime.UTC) > start_time + timeout:
                pytest.fail(f"Generate-all didn't empty in {timeout}")

        list_result = await client.post(
            "/list-latest-datasets",
            json={
                "site_id": "demo_london",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        assert list_result.status_code == 200, list_result.text
        assert list_result.json()["ElectricityMeterDataSynthesised"] is not None, "ElectricityMeterDataSynthesised is None"
        assert list_result.json()["bundle_id"] is not None, "bundle id is None"

        data_result = await client.post(
            "/get-latest-datasets",
            json={
                "loc": "remote",
                "site_id": "demo_london",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        assert data_result.status_code == 200, data_result.text

        data_json = data_result.json()
        assert (
            len(data_json["eload"]["data"])
            == len(data_json["heat"]["data"][0]["reduced_hload"])
            == len(data_json["rgen"]["data"][0])
            == len(data_json["import_tariffs"]["data"][0])
            == len(data_json["grid_co2"]["data"])
        )

        assert all(
            len(item["reduced_hload"]) == len(data_json["heat"]["data"][0]["reduced_hload"])
            for item in data_json["heat"]["data"]
        )

        assert all(len(item) == len(data_json["rgen"]["data"][0]) for item in data_json["rgen"]["data"])

        assert all(len(item) == len(data_json["import_tariffs"]["data"][0]) for item in data_json["import_tariffs"]["data"])

        assert (
            data_json["eload"]["timestamps"]
            == data_json["heat"]["timestamps"]
            == data_json["rgen"]["timestamps"]
            == data_json["import_tariffs"]["timestamps"]
            == data_json["grid_co2"]["timestamps"]
        )

        # Check that we got multiple tariffs here, without having to generate all again
        tariff_data = data_json["import_tariffs"]

        assert all(all(np.isfinite(item)) for item in tariff_data["data"]), "Tariff is empty or NaN"

        # rgendata is of the form {"timestamps": [...], "data": [ [..., ] , ...}
        rgen_data = data_json["rgen"]
        assert len(rgen_data["data"]) == 2
        assert all(all(np.isfinite(item)) for item in rgen_data["data"]), "Renewables is empty or NaN"

        # This is an annoying switch of units
        assert all(item == FIXED_TARIFF_COSTS / 100.0 for item in tariff_data["data"][0])
        assert len(set(tariff_data["data"][0])) == 1, "First tariff must be fixed"
        assert len(set(tariff_data["data"][2])) >= 23, "Second tariff must be agile"
        assert all(item == tariff_data["data"][0][0] for item in tariff_data["data"][0]), "First entry must be fixed tariff"
        assert tariff_data["data"][0] != tariff_data["data"][1], "Tariffs must be different"

        # Check that we got multiple heat loads here, this should be an array of {"cost": ..., "reduced_hload": ...} dicts
        heatload_data = data_json["heat"]["data"]
        assert len(heatload_data) == 4
        assert len({item["cost"] for item in heatload_data}) == 4

        for idx in range(1, 4):
            assert heatload_data[0]["reduced_hload"] != heatload_data[idx]["reduced_hload"], "heatload_data must be different"

    @pytest.mark.asyncio
    async def test_same_timestamps(self, client: httpx.AsyncClient) -> None:
        """Check that we fail early if the same timestamps are requested."""
        data_result = await client.post(
            "/generate-all",
            json={"site_id": "bircotes_leisure_centre", "start_ts": "2022-01-01T00:00:00Z", "end_ts": "2022-01-01T00:00:00Z"},
        )
        assert data_result.status_code == 422
        assert "start_ts" in data_result.text
        assert "end_ts" in data_result.text


class TestGetLatestElectricity:
    @pytest.mark.asyncio
    async def test_get_blended_latest_elec(
        self, client: httpx.AsyncClient, upload_meter_data: tuple[dict[str, Jsonable], dict[str, Jsonable]]
    ) -> None:
        """Test that we can generate some electrical data, and then get it via the list- and get- pair."""
        _, elec_result = upload_meter_data
        start_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2020, month=2, day=1, tzinfo=datetime.UTC)

        bundle_id = uuid7()
        bundle_resp = await client.post(
            "/create-bundle",
            json={
                "bundle_id": str(bundle_id),
                "name": "test_get_blended_latest_elec",
                "site_id": "demo_london",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert bundle_resp.is_success

        generate_request = await client.post(
            "/generate-electricity-load",
            json={
                "dataset_id": elec_result["dataset_id"],
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
                "bundle_metadata": {
                    "bundle_id": str(bundle_id),
                    "dataset_id": str(uuid7()),
                    "dataset_type": "ElectricityMeterDataSynthesised",
                },
            },
        )
        assert generate_request.status_code == 200, generate_request.text

        list_result_with_blend = await client.post(
            "/list-latest-datasets",
            json={
                "site_id": "demo_london",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert list_result_with_blend.is_success, list_result_with_blend.text
        list_data = list_result_with_blend.json()
        assert list_data["ElectricityMeterData"] is not None
        assert list_data["ElectricityMeterDataSynthesised"] is not None

        get_result = await client.post("get-dataset-bundle", params={"bundle_id": str(bundle_id)})
        assert get_result.is_success, get_result.text
        assert (
            len(get_result.json()["eload"]["timestamps"])
            == len(get_result.json()["eload"]["data"])
            == (end_ts - start_ts) / datetime.timedelta(minutes=30)
        )


class TestGetMultipleHeatLoads:
    @pytest.mark.slow
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_create_and_get_heatloads(self, client: httpx.AsyncClient, upload_meter_data: tuple) -> None:
        """Test that we can get four different heatloads with different values."""
        gas_meter_result, _ = upload_meter_data
        POTENTIAL_INTERVENTIONS = [[], [InterventionEnum.Loft], [InterventionEnum.DoubleGlazing], [InterventionEnum.Cladding]]
        background_tasks = []
        start_ts = datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2022, month=2, day=1, tzinfo=datetime.UTC)

        bundle_id = uuid7()
        bundle_resp = await client.post(
            "/create-bundle",
            json={
                "bundle_id": str(bundle_id),
                "name": "test_create_and_get_heatloads",
                "site_id": "demo_london",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert bundle_resp.is_success

        async with asyncio.TaskGroup() as tg:
            for idx, intervention in enumerate(POTENTIAL_INTERVENTIONS):
                background_tasks.append(
                    tg.create_task(
                        client.post(
                            "/generate-heating-load",
                            json={
                                "dataset_id": gas_meter_result["dataset_id"],
                                "start_ts": start_ts.isoformat(),
                                "end_ts": end_ts.isoformat(),
                                "interventions": intervention,
                                "bundle_metadata": {
                                    "bundle_id": str(bundle_id),
                                    "dataset_id": str(uuid7()),
                                    "dataset_type": "HeatingLoad",
                                    "dataset_subtype": intervention,
                                    "dataset_order": idx,
                                },
                            },
                        )
                    )
                )
        listed_datasets_result = await client.post(
            "/list-latest-datasets",
            json={
                "site_id": "demo_london",
                "start_ts": "1970-01-01T00:00:00Z",
                "end_ts": datetime.datetime.now(datetime.UTC).isoformat(),
            },
        )
        assert listed_datasets_result.is_success, listed_datasets_result.text
        listed_data = listed_datasets_result.json()
        assert len(listed_data["HeatingLoad"]) == 4

        got_datasets = await client.post(
            "/get-dataset-bundle",
            params={
                "bundle_id": str(bundle_id),
            },
        )
        assert got_datasets.is_success, got_datasets.text
        heating_data = got_datasets.json()["heat"]["data"]
        for idx in [1, 2, 3]:
            assert heating_data[0]["reduced_hload"] != heating_data[idx]["reduced_hload"]

        assert len({item["cost"] for item in heating_data}) == 4, "Must have four different costs"
        assert heating_data[0]["cost"] == 0, "First entry must be zero cost baseline"


class TestDatasetBundles:
    """Test that we can enter, list and retrieve bundles."""

    @pytest.mark.asyncio
    async def test_can_enter_bundle_meta_only(self, client: httpx.AsyncClient) -> None:
        """Test that we can enter a valid bundle with only metadata."""
        DEMO_UUID = uuid.UUID(int=1, version=4)
        pool = await get_pool_hack(client)
        test_bundle = DatasetBundleMetadata(
            bundle_id=DEMO_UUID,
            name="Test Bundle",
            start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
            end_ts=datetime.datetime(year=2023, month=1, day=1, tzinfo=datetime.UTC),
            site_id="demo_london",
        )
        res = await insert_dataset_bundle(bundle_metadata=test_bundle, pool=pool)
        assert res == DEMO_UUID

    @pytest.mark.asyncio
    async def test_can_enter_bundle_with_data(self, client: httpx.AsyncClient) -> None:
        """Test that we can enter a valid bundle with metadata and datasets."""
        DEMO_UUID = uuid.UUID(int=1, version=4)
        pool = await get_pool_hack(client)
        test_bundle = DatasetBundleMetadata(
            bundle_id=DEMO_UUID,
            name="Test Bundle",
            start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
            end_ts=datetime.datetime(year=2023, month=1, day=1, tzinfo=datetime.UTC),
            site_id="demo_london",
        )
        res = await insert_dataset_bundle(
            bundle_metadata=test_bundle,
            pool=pool,
        )
        assert res == DEMO_UUID

    @pytest.mark.asyncio
    async def test_can_list_bundles(self, client: httpx.AsyncClient) -> None:
        """Test that we can enter a valid bundle with metadata and datasets."""
        DEMO_UUID = uuid.UUID(int=1, version=4)
        pool = await get_pool_hack(client)
        test_bundle = DatasetBundleMetadata(
            bundle_id=DEMO_UUID,
            name="Test Bundle",
            start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
            end_ts=datetime.datetime(year=2023, month=1, day=1, tzinfo=datetime.UTC),
            site_id="demo_london",
        )
        _ = await insert_dataset_bundle(
            bundle_metadata=test_bundle,
            pool=pool,
        )

        DEMO_UUID_2 = uuid.UUID(int=10, version=4)
        test_bundle = DatasetBundleMetadata(
            bundle_id=DEMO_UUID_2,
            name="Test Bundle 2",
            start_ts=datetime.datetime(year=2021, month=1, day=1, tzinfo=datetime.UTC),
            end_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
            site_id="demo_london",
        )
        _ = await insert_dataset_bundle(
            bundle_metadata=test_bundle,
            pool=pool,
        )

        result = await client.post(
            "list-dataset-bundles",
            json={
                "site_id": "demo_london",
                "start_ts": datetime.datetime(year=2000, month=1, day=1, tzinfo=datetime.UTC).isoformat(),
                "end_ts": datetime.datetime.now(datetime.UTC).isoformat(),
            },
        )
        assert result.status_code == 200, result.text
        data = result.json()
        assert len(data) == 2
        assert {item["bundle_id"] for item in data} == {str(DEMO_UUID), str(DEMO_UUID_2)}
        assert all(item["is_complete"] for item in data)
        assert all(not item["is_error"] for item in data)


class TestBundleHints:
    """Test that we can get hints about bundles."""

    @pytest.mark.asyncio
    async def test_empty_bundle_hints(self, client: httpx.AsyncClient) -> None:
        """Test that we can get boring hints for an empty bundle."""
        DEMO_UUID = uuid.UUID(int=1, version=4)
        pool = await get_pool_hack(client)
        test_bundle = DatasetBundleMetadata(
            bundle_id=DEMO_UUID,
            name="Test Bundle",
            start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
            end_ts=datetime.datetime(year=2023, month=1, day=1, tzinfo=datetime.UTC),
            site_id="demo_london",
        )
        res = await insert_dataset_bundle(bundle_metadata=test_bundle, pool=pool)
        assert res == DEMO_UUID

        hints_resp = await get_bundle_hints(bundle_id=DEMO_UUID, pool=pool)
        assert hints_resp.baseline is None
        assert hints_resp.heating is None
        assert hints_resp.tariffs is None
        assert hints_resp.renewables is None
