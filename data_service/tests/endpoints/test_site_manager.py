"""Test that the generate all function works."""

# ruff: noqa: D101, D102, D103
import asyncio
import datetime
import json

import httpx
import numpy as np
import pytest
import pytest_asyncio

from app.internal.gas_meters import parse_half_hourly
from app.models.core import DatasetTypeEnum
from app.models.heating_load import InterventionEnum


@pytest_asyncio.fixture
async def upload_meter_data(client: httpx.AsyncClient) -> tuple:
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
        assert all_datasets_response.status_code == 200
        all_json = all_datasets_response.json()
        assert sum(int(bool(all_json[key])) for key in DatasetTypeEnum) == 2

        get_datasets_response = await client.post(
            "/get-latest-tariffs",
            json={
                "site_id": "demo_london",
                "start_ts": start_ts.isoformat(),
                "loc": "remote",
                "end_ts": end_ts.isoformat(),
            },
        )
        assert get_datasets_response.status_code == 200, get_datasets_response.text
        got_datasets = get_datasets_response.json()
        assert all(all(np.isfinite(item)) for item in got_datasets["data"]), "Tariff is empty or NaN"

        # These shouldn't be identical
        assert got_datasets["data"][0] != got_datasets["data"][1]


class TestGenerateAll:
    @pytest.mark.slow
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_all_same_length(self, client: httpx.AsyncClient, upload_meter_data: tuple) -> None:
        _, _ = upload_meter_data
        demo_start_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
        demo_end_ts = datetime.datetime(year=2020, month=2, day=1, tzinfo=datetime.UTC)
        generate_result = await client.post(
            "/generate-all",
            json={
                "site_id": "demo_london",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )

        assert generate_result.status_code == 200, generate_result.text
        list_result = await client.post(
            "/list-latest-datasets",
            json={
                "site_id": "demo_london",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        assert list_result.status_code == 200, list_result.text
        assert list_result.json()["ElectricityMeterDataSynthesised"] is not None

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

        assert len(set(tariff_data["data"][0])) == 1, "First tariff must be fixed"
        assert len(set(tariff_data["data"][1])) > 48, "Second tariff must be agile"
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
    async def test_get_blended_latest_elec(self, client: httpx.AsyncClient, upload_meter_data: tuple) -> None:
        """Test that we can generate some electrical data, and then get it via the list- and get- pair."""
        _, _ = upload_meter_data
        start_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2020, month=2, day=1, tzinfo=datetime.UTC)
        list_result = await client.post(
            "/list-latest-datasets",
            json={"site_id": "demo_london", "start_ts": "1970-01-01T00:00:00Z", "end_ts": "2025-01-01T00:00:00Z"},
        )
        assert list_result.status_code == 200
        generate_request = await client.post(
            "/generate-electricity-load",
            json={
                "dataset_id": list_result.json()["ElectricityMeterData"]["dataset_id"],
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
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
        assert list_result_with_blend.status_code == 200
        list_data = list_result_with_blend.json()
        assert list_data["ElectricityMeterData"] is not None
        assert list_data["ElectricityMeterDataSynthesised"] is not None

        get_result = await client.post("get-specific-datasets", json=list_data)
        assert get_result.status_code == 200
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
        start_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2020, month=2, day=1, tzinfo=datetime.UTC)

        # If we allow the background tasks to get the weather, then they'll overwrite each
        # other and cause terrible trouble, so let's get it here first.
        await client.post(
            "/get-weather",
            json={"location": "London", "start_ts": start_ts.isoformat(), "end_ts": end_ts.isoformat()},
        )
        await client.post(
            "/get-weather",
            json={
                "location": "London",
                "start_ts": gas_meter_result["start_ts"],
                "end_ts": gas_meter_result["end_ts"],
            },
        )
        async with asyncio.TaskGroup() as tg:
            for intervention in POTENTIAL_INTERVENTIONS:
                background_tasks.append(  # noqa: PERF401
                    tg.create_task(
                        client.post(
                            "/generate-heating-load",
                            json={
                                "dataset_id": gas_meter_result["dataset_id"],
                                "start_ts": start_ts.isoformat(),
                                "end_ts": end_ts.isoformat(),
                                "interventions": intervention,
                            },
                        )
                    )
                )
        # keep references to the tasks to avoid a horrible Heisenbug (argh!)
        # then wait for them all to be done.
        _ = [task.result() for task in background_tasks]

        listed_datasets_result = await client.post(
            "/list-latest-datasets",
            json={
                "site_id": "demo_london",
                "start_ts": "1970-01-01T00:00:00Z",
                "end_ts": datetime.datetime.now(datetime.UTC).isoformat(),
            },
        )
        assert listed_datasets_result.status_code == 200
        listed_data = listed_datasets_result.json()
        assert len(listed_data["HeatingLoad"]) == 4

        got_datasets = await client.post(
            "/get-specific-datasets",
            json={
                "site_id": "demo_london",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
                "HeatingLoad": listed_data["HeatingLoad"],
            },
        )
        assert got_datasets.status_code == 200, got_datasets.text
        heating_data = got_datasets.json()["heat"]["data"]
        for idx in [1, 2, 3]:
            assert heating_data[0]["reduced_hload"] != heating_data[idx]["reduced_hload"]

        assert len({item["cost"] for item in heating_data}) == 4, "Must have four different costs"
        assert heating_data[0]["cost"] == 0, "First entry must be zero cost baseline"


class TestListAllDatasets:
    @pytest.mark.asyncio
    async def test_has_metadata(self, client: httpx.AsyncClient, upload_meter_data: tuple) -> None:
        """Test that we get some metadata from uploaded datasets."""
        _, _ = upload_meter_data
        list_result = await client.post(
            "/list-datasets",
            json={"site_id": "demo_london", "start_ts": "1970-01-01T00:00:00Z", "end_ts": "2025-01-01T00:00:00Z"},
        )

        assert list_result.status_code == 200, list_result.text

        list_data = list_result.json()
        assert sum(int(bool(val)) for val in list_data.values()) == 3
        for dataset_type, dataset_entry in list_data.items():
            if dataset_type == "ASHPData" or not dataset_entry:
                # skip this one as it's a dummy dataset
                continue
            for subitem in dataset_entry:
                assert subitem["start_ts"] <= subitem["end_ts"]
                assert subitem["num_entries"] > 1

    @pytest.mark.asyncio
    async def test_hand_list_latest_back(self, client: httpx.AsyncClient, upload_meter_data: tuple) -> None:
        """Test that we can hand the result from "list-latest-datasets" back."""
        _, _ = upload_meter_data
        list_result = await client.post(
            "/list-latest-datasets",
            json={"site_id": "demo_london", "start_ts": "1970-01-01T00:00:00Z", "end_ts": "2025-01-01T00:00:00Z"},
        )
        assert list_result.status_code == 200
        assert list_result.json()[DatasetTypeEnum.ElectricityMeterData.value]["dataset_id"]
        get_result = await client.post("/get-specific-datasets", json=list_result.json())
        assert get_result.status_code == 200
        data = get_result.json()
        assert len(data) == 9
        assert data["eload"] is not None
        assert len(data["eload"]["data"]) > 0

    @pytest.mark.asyncio
    async def test_hand_back_just_datasets(self, client: httpx.AsyncClient, upload_meter_data: tuple) -> None:
        """Test that we can hand back just the dataset IDs from "list-latest-datasets" back."""
        _, _ = upload_meter_data
        list_result = await client.post(
            "/list-latest-datasets",
            json={"site_id": "demo_london", "start_ts": "1970-01-01T00:00:00Z", "end_ts": "2025-01-01T00:00:00Z"},
        )
        assert list_result.status_code == 200
        dataset_id = list_result.json()[DatasetTypeEnum.ElectricityMeterData.value]["dataset_id"]
        get_result = await client.post(
            "/get-specific-datasets", json={"site_id": "demo_london", "ElectricityMeterData": dataset_id}
        )
        assert get_result.status_code == 200, get_result.text
        data = get_result.json()
        assert len(data) == 9
        assert data["eload"] is not None
        assert len(data["eload"]["data"]) > 0
