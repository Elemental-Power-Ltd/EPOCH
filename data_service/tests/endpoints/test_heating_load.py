"""Tests for heating load calculation."""

# ruff: noqa: D101, D102, D103
import datetime
import json

import httpx
import pydantic
import pytest
import pytest_asyncio

from app.internal.gas_meters import parse_half_hourly


@pytest_asyncio.fixture
async def uploaded_meter_data(client: httpx.AsyncClient) -> pydantic.Json:
    data = parse_half_hourly("./tests/data/test_gas.csv")
    data["start_ts"] = data.index
    metadata = {"fuel_type": "gas", "site_id": "demo_london", "reading_type": "halfhourly"}
    records = json.loads(data.to_json(orient="records"))
    upload_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()
    return upload_result


class TestHeatingLoad:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_and_get_heating_load(self, uploaded_meter_data: pydantic.Json, client: httpx.AsyncClient) -> None:
        dataset_id = uploaded_meter_data["dataset_id"]

        generated_metadata = await client.post(
            "/generate-heating-load",
            json={"dataset_id": dataset_id, "start_ts": "2023-01-01T00:00:00Z", "end_ts": "2023-02-01T00:00:00Z"},
        )
        heating_load_result = await client.post(
            "/get-heating-load", json={"dataset_id": generated_metadata.json()["dataset_id"]}
        )
        assert datetime.datetime.fromisoformat(generated_metadata.json()["created_at"]) > datetime.datetime.now(
            datetime.UTC
        ) - datetime.timedelta(minutes=1)
        assert any(item["HLoad1"] > 0 for item in heating_load_result.json())
        assert any(item["AirTemp"] != 0 for item in heating_load_result.json())

        assert generated_metadata.json()["site_id"] == "demo_london"
        assert generated_metadata.json()["params"]["solar_gain"] >= 0
        assert 0 <= generated_metadata.json()["params"]["r2_score"] < 1.0
        assert 0 <= generated_metadata.json()["params"]["smoothing"] < 1.0
        assert generated_metadata.json()["params"]["heating_kwh"] > 0

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_heating_load_right_length(self, uploaded_meter_data: pydantic.Json, client: httpx.AsyncClient) -> None:
        """Check that we've got the right length of dataset and haven't dropped the last entry."""
        dataset_id = uploaded_meter_data["dataset_id"]

        start_ts = datetime.datetime(year=2023, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2023, month=2, day=1, tzinfo=datetime.UTC)
        generated_metadata = await client.post(
            "/generate-heating-load",
            json={"dataset_id": dataset_id, "start_ts": start_ts.isoformat(), "end_ts": end_ts.isoformat()},
        )
        heating_load_result = await client.post(
            "/get-heating-load", json={"dataset_id": generated_metadata.json()["dataset_id"]}
        )
        assert datetime.datetime.fromisoformat(generated_metadata.json()["created_at"]) > datetime.datetime.now(
            datetime.UTC
        ) - datetime.timedelta(minutes=1)

        assert heating_load_result.json()[0]["Date"] == start_ts.date().strftime("%d-%b")
        assert heating_load_result.json()[-1]["Date"] == (end_ts - datetime.timedelta(minutes=30)).date().strftime("%d-%b")
        assert heating_load_result.json()[0]["StartTime"] == "00:00", "First entry isn't 00:00"
        assert heating_load_result.json()[-1]["StartTime"] == "23:30", "Last entry isn't 23:30"
        assert len(heating_load_result.json()) == int((end_ts - start_ts) / datetime.timedelta(minutes=30))
