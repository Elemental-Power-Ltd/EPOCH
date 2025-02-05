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
        assert len(all_datasets_response.json()) == 2

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
        demo_end_ts = datetime.datetime(year=2021, month=1, day=1, tzinfo=datetime.UTC)
        generate_result = await client.post(
            "/generate-all",
            json={
                "site_id": "demo_london",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )

        assert generate_result.status_code == 200, generate_result.text

        data_result = await client.post(
            "/get-latest-datasets",
            json={
                "loc": "remote",
                "site_id": "demo_london",
                "start_ts": demo_start_ts.isoformat(),
                "duration": "year",
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


class TestListAllDatasets:
    @pytest.mark.asyncio
    async def test_has_metadata(self, client: httpx.AsyncClient, upload_meter_data: tuple) -> None:
        _, _ = upload_meter_data
        list_result = await client.post(
            "/list-datasets",
            json={
                "site_id": "demo_london",
            },
        )

        assert list_result.status_code == 200, list_result.text

        list_data = list_result.json()
        assert len(list_data) == 3
        print(list_data)
        for dataset_entry in list_data:
            if dataset_entry["dataset_type"] == "ASHPData":
                # skip this one as it's a dummy dataset
                continue
            assert dataset_entry["start_ts"] <= dataset_entry["end_ts"], dataset_entry
            assert dataset_entry["num_entries"] > 1
