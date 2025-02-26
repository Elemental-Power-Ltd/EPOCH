"""Tests for uploading and parsing meter data."""

# ruff: noqa: D101, D102, D103
import datetime
import json
import uuid

import httpx
import pytest

from app.internal.gas_meters import parse_half_hourly


class TestUploadMeterData:
    @pytest.mark.asyncio
    async def test_upload_pre_parsed_with_specified(self, client: httpx.AsyncClient) -> None:
        data = parse_half_hourly("./tests/data/test_elec.csv")
        data["start_ts"] = data.index
        metadata = {
            "created_at": "2024-08-14T10:31:00Z",
            "dataset_id": "1db34dd6-0e3a-4ed1-8a2a-a84e74550ae4",
            "fuel_type": "elec",
            "site_id": "demo_london",
            "reading_type": "halfhourly",
            "is_synthetic": False,
        }
        records = json.loads(data.to_json(orient="records"))
        result = await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})

        assert result.status_code == 200, result.text
        assert result.json()["dataset_id"] == "1db34dd6-0e3a-4ed1-8a2a-a84e74550ae4"
        assert result.json()["created_at"] == "2024-08-14T10:31:00Z"
        assert result.json()["fuel_type"] == "elec"

    @pytest.mark.asyncio
    async def test_upload_pre_parsed_without_specified(self, client: httpx.AsyncClient) -> None:
        data = parse_half_hourly("./tests/data/test_elec.csv")
        data["start_ts"] = data.index
        metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "halfhourly"}
        records = json.loads(data.to_json(orient="records"))
        result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()
        assert datetime.datetime.fromisoformat(result["created_at"]) > datetime.datetime.now(datetime.UTC) - datetime.timedelta(
            minutes=1
        )
        assert result["fuel_type"] == "elec"

    @pytest.mark.asyncio
    async def test_upload_and_get_without_date(self, client: httpx.AsyncClient) -> None:
        data = parse_half_hourly("./tests/data/test_elec.csv")
        data["start_ts"] = data.index
        metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "halfhourly"}
        records = json.loads(data.to_json(orient="records"))
        upload_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

        result = (await client.post("/get-meter-data", json={"dataset_id": upload_result["dataset_id"]})).json()
        assert pytest.approx(sum(item["consumption"] for item in result)) == data["consumption"].sum()

    @pytest.mark.asyncio
    async def test_get_non_existent_dataset(self, client: httpx.AsyncClient) -> None:
        result = await client.post(
            "/get-meter-data",
            json={"dataset_id": str(uuid.uuid4()), "start_ts": "2023-01-01T00:00:00Z", "end_ts": "2023-02-01T00:00:00Z"},
        )
        assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_and_get_electricity_load(self, client: httpx.AsyncClient) -> None:
        data = parse_half_hourly("./tests/data/test_elec.csv")
        data["start_ts"] = data.index
        metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "halfhourly"}
        records = json.loads(data.to_json(orient="records"))
        upload_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

        result = (
            await client.post(
                "/get-electricity-load",
                json={
                    "dataset_id": upload_result["dataset_id"],
                    "start_ts": "2023-09-01T00:00:00Z",
                    "end_ts": "2024-06-30T00:00:00Z",
                },
            )
        ).json()
        assert len(result["data"]) > 100
        assert any(value > 0 for value in result["data"])

    @pytest.mark.asyncio
    async def test_upload_and_get_electricity_load_non_hh(self, client: httpx.AsyncClient) -> None:
        data = parse_half_hourly("./tests/data/test_elec.csv")
        data["start_ts"] = data.index
        metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "manual"}
        records = json.loads(data.to_json(orient="records"))
        upload_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

        result = await client.post(
            "/get-meter-data",
            json={
                "dataset_id": upload_result["dataset_id"],
                "start_ts": data.index.min().isoformat(),
                "end_ts": data.index.max().isoformat(),
            },
        )
        assert result.status_code == 200
