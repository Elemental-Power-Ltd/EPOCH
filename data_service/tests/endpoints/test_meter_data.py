"""Tests for uploading and parsing meter data."""

# ruff: noqa: D101, D102, D103
import datetime
import json
import uuid

import httpx
import numpy as np
import pandas as pd
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
        }
        records = json.loads(data.to_json(orient="records"))
        result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

        assert result["dataset_id"] == "1db34dd6-0e3a-4ed1-8a2a-a84e74550ae4"
        assert result["created_at"] == "2024-08-14T10:31:00Z"
        assert result["fuel_type"] == "elec"

    @pytest.mark.asyncio
    async def test_upload_pre_parsed_without_specified(self, client: httpx.AsyncClient) -> None:
        data = parse_half_hourly("./tests/data/test_elec.csv")
        data["start_ts"] = data.index
        metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "halfhourly"}
        records = json.loads(data.to_json(orient="records"))
        result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()
        print(result)
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
        assert len(result) > 100
        assert any(item["FixLoad1"] > 0 for item in result)

    @pytest.mark.asyncio
    async def test_timestamps_too_far(self, client: httpx.AsyncClient) -> None:
        data = parse_half_hourly("./tests/data/test_elec.csv")
        data["start_ts"] = data.index
        metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "halfhourly"}
        records = json.loads(data.to_json(orient="records"))
        upload_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

        result = await client.post(
            "/get-electricity-load",
            json={
                "dataset_id": upload_result["dataset_id"],
                "start_ts": "2021-09-01T00:00:00Z",
                "end_ts": "2023-09-01T00:00:00Z",
            },
        )
        assert result.status_code == 400
        assert "more than 1 year apart" in result.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_and_get_electricity_load_non_hh(self, client: httpx.AsyncClient) -> None:
        data = parse_half_hourly("./tests/data/test_elec.csv")
        data["start_ts"] = data.index
        metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "manual"}
        records = json.loads(data.to_json(orient="records"))
        upload_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

        result = await client.post(
            "/get-electricity-load",
            json={
                "dataset_id": upload_result["dataset_id"],
                "start_ts": data.index.min().isoformat(),
                "end_ts": data.index.max().isoformat(),
            },
        )
        print(result.json())
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_cant_get_elec_from_gas(self, client: httpx.AsyncClient) -> None:
        data = parse_half_hourly("./tests/data/test_gas.csv")
        data["start_ts"] = data.index
        metadata = {"fuel_type": "gas", "site_id": "demo_london", "reading_type": "halfhourly"}
        records = json.loads(data.to_json(orient="records"))
        upload_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

        result = await client.post(
            "/get-electricity-load",
            json={
                "dataset_id": upload_result["dataset_id"],
                "start_ts": data.index.min().isoformat(),
                "end_ts": data.end_ts.max().isoformat(),
            },
        )
        assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_and_get_resampled_electricity_load(self, client: httpx.AsyncClient) -> None:
        raw_data = parse_half_hourly("./tests/data/test_elec.csv")
        raw_data["start_ts"] = raw_data.index
        month_starts = raw_data[["start_ts"]].resample("1MS").min()
        month_ends = raw_data[["end_ts"]].resample("1MS").max()
        data = raw_data[["consumption"]].resample("1MS").sum()
        data["end_ts"] = np.minimum(month_ends.to_numpy()[:, 0], (data.index + pd.offsets.MonthEnd()).to_numpy())
        data["start_ts"] = np.maximum(month_starts.to_numpy()[:, 0], (data.index).to_numpy())
        metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "manual"}

        records = list(json.loads(data.to_json(orient="index")).values())
        upload_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()
        result = await client.post(
            "/get-electricity-load",
            json={
                "dataset_id": upload_result["dataset_id"],
                "start_ts": data.start_ts.min().isoformat(),
                "end_ts": data.end_ts.max().isoformat(),
            },
        )
        assert result.status_code == 200
        assert result.json()[-1]["StartTime"] == "23:00"
        assert result.json()[0]["Date"] == data.start_ts.min().strftime("%d-%b")
        assert result.json()[-1]["Date"] == (data.end_ts.max() - pd.Timedelta(minutes=30)).strftime("%d-%b")
        expected_len = int((data.end_ts.max() - data.start_ts.min()) / pd.Timedelta(minutes=60))
        assert len(result.json()) == expected_len
