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
        all_datasets_response = await client.post("/list-latest-datasets", json={"site_id": "demo_london"})
        all_json = all_datasets_response.json()
        assert sum(int(bool(all_json[key])) for key in DatasetTypeEnum) == 2

        get_datasets_response = await client.post(
            "/get-latest-tariffs",
            json={"site_id": "demo_london", "start_ts": start_ts.isoformat(), "loc": "remote", "duration": "year"},
        )
        assert get_datasets_response.status_code == 200, get_datasets_response.text
        got_datasets = get_datasets_response.json()
        assert all(np.isfinite(item["Tariff"]) for item in got_datasets)
        assert all(np.isfinite(item["Tariff1"]) for item in got_datasets)

        # We haven't filled these ones in, deliberately
        assert all(item["Tariff2"] is None for item in got_datasets)
        assert all(item["Tariff3"] is None for item in got_datasets)

        # These shouldn't be identical
        assert any(item["Tariff"] != item["Tariff1"] for item in got_datasets)


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
            len(data_json["eload"])
            == len(data_json["heat"])
            == len(data_json["rgen"])
            == len(data_json["import_tariffs"])
            == len(data_json["grid_co2"])
        )

        # Check that we got multiple tariffs here, without having to generate all again
        tariff_data = data_json["import_tariffs"]

        assert all(np.isfinite(item["Tariff"]) for item in tariff_data), "Tariff is empty or NaN"
        assert all(np.isfinite(item["Tariff1"]) for item in tariff_data), "Tariff1 is empty or NaN"
        assert all(np.isfinite(item["Tariff2"]) for item in tariff_data), "Tariff2 is empty or NaN"
        assert all(np.isfinite(item["Tariff3"]) for item in tariff_data), "Tariff3 is empty or NaN"

        assert all(item["Tariff"] == tariff_data[0]["Tariff"] for item in tariff_data), "First entry must be fixed tariff"
        assert any(item["Tariff"] != item["Tariff1"] for item in tariff_data), "Tariffs must be different"

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
            json={
                "site_id": "demo_london",
            },
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
            },
        )
        assert list_result_with_blend.status_code == 200
        list_data = list_result_with_blend.json()
        assert list_data["ElectricityMeterData"] is not None
        assert list_data["ElectricityMeterDataSynthesised"] is not None

        get_result = await client.post("get-specific-datasets", json=list_data)
        assert get_result.status_code == 200
        assert len(get_result.json()["eload"]) == 1536


class TestListAllDatasets:
    @pytest.mark.asyncio
    async def test_has_metadata(self, client: httpx.AsyncClient, upload_meter_data: tuple) -> None:
        """Test that we get some metadata from uploaded datasets."""
        _, _ = upload_meter_data
        list_result = await client.post(
            "/list-datasets",
            json={
                "site_id": "demo_london",
            },
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
            json={
                "site_id": "demo_london",
            },
        )
        assert list_result.status_code == 200
        assert list_result.json()[DatasetTypeEnum.ElectricityMeterData.value]["dataset_id"]
        get_result = await client.post("/get-specific-datasets", json=list_result.json())
        assert get_result.status_code == 200
        data = get_result.json()
        assert len(data) == 7
        assert data["eload"] is not None
        assert len(data["eload"]) > 0

    @pytest.mark.asyncio
    async def test_hand_back_just_datasets(self, client: httpx.AsyncClient, upload_meter_data: tuple) -> None:
        """Test that we can hand back just the dataset IDs from "list-latest-datasets" back."""
        _, _ = upload_meter_data
        list_result = await client.post(
            "/list-latest-datasets",
            json={
                "site_id": "demo_london",
            },
        )
        assert list_result.status_code == 200
        dataset_id = list_result.json()[DatasetTypeEnum.ElectricityMeterData.value]["dataset_id"]
        get_result = await client.post(
            "/get-specific-datasets", json={"site_id": "demo_london", "ElectricityMeterData": dataset_id}
        )
        assert get_result.status_code == 200, get_result.text
        data = get_result.json()
        assert len(data) == 7
        assert data["eload"] is not None
        assert len(data["eload"]) > 0
