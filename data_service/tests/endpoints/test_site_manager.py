"""Test that the generate all function works."""
# ruff: noqa: D101, D102, D103
import datetime
import json

import httpx
import pytest
import pytest_asyncio

from app.internal.gas_meters import parse_half_hourly
from app.internal.site_manager.site_manager import fetch_blended_electricity_load, fetch_electricity_load


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


class TestGenerateAll:
    @pytest.mark.slow
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_all_same_length(self, client: httpx.AsyncClient, upload_meter_data: tuple) -> None:
        elec_result, gas_result = upload_meter_data
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
