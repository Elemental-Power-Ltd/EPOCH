"""Tests for electrical data synthesis."""

# ruff: noqa: D101, D102
import datetime
import json

import httpx
import numpy as np
import pandas as pd
import pytest
from app.internal.gas_meters import parse_half_hourly
from app.internal.utils.uuid import uuid7


class TestUploadMeterData:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_upload_hh_and_generate(self, client: httpx.AsyncClient) -> None:
        """Test that we can upload half hourly data and generate a new dataset."""
        raw_data = parse_half_hourly("./tests/data/test_elec.csv")
        raw_data["start_ts"] = raw_data.index
        metadata = {
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "dataset_id": str(uuid7()),
            "fuel_type": "elec",
            "site_id": "demo_london",
            "reading_type": "halfhourly",
        }
        records = json.loads(raw_data.to_json(orient="records"))
        meta_result = await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})
        assert meta_result.is_success, meta_result.text

        meta_data = meta_result.json()
        elec_result = await client.post(
            "/generate-electricity-load",
            json={
                "dataset_id": meta_data["dataset_id"],
                "start_ts": "2019-01-01T00:00:00Z",
                "end_ts": "2020-01-01T00:00:00Z",
            },
        )
        assert elec_result.is_success, elec_result.text

        new_id = elec_result.json()["dataset_id"]
        result = await client.post(
            "/get-electricity-load",
            json={
                "dataset_id": new_id,
                "start_ts": "2019-01-01T00:00:00Z",
                "end_ts": "2020-01-01T00:00:00Z",
            },
        )
        assert result.is_success, result.text
        assert all(item > 0 for item in result.json()["data"]), "Got negative results"

    @pytest.mark.asyncio
    async def test_upload_pre_parsed_with_specified(self, client: httpx.AsyncClient) -> None:
        """Test that we can upload and parse monthly-ish data and get reasonable results out."""
        raw_data = parse_half_hourly("./tests/data/test_elec.csv")
        data = raw_data[["consumption"]].resample(pd.Timedelta(days=29)).sum()
        data["start_ts"] = data.index
        data["end_ts"] = data.index + pd.Timedelta(days=29)
        metadata = {
            "created_at": "2024-08-14T10:31:00Z",
            "dataset_id": "1db34dd6-0e3a-4ed1-8a2a-a84e74550ae4",
            "fuel_type": "elec",
            "site_id": "demo_london",
            "reading_type": "manual",
        }
        records = json.loads(data.to_json(orient="records"))
        meta_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

        elec_result = await client.post(
            "/generate-electricity-load",
            json={
                "dataset_id": meta_result["dataset_id"],
                "start_ts": "2019-01-01T00:00:00Z",
                "end_ts": "2020-01-01T00:00:00Z",
            },
        )
        assert elec_result.status_code == 200

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
        data["end_ts"] = np.minimum(
            month_ends.to_numpy()[:, 0],
            (data.index + pd.offsets.MonthEnd() + pd.Timedelta(days=1)).to_numpy(),  # type: ignore
        )
        data["start_ts"] = np.maximum(month_starts.to_numpy()[:, 0], (data.index).to_numpy())
        metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "manual"}

        demo_start_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
        demo_end_ts = datetime.datetime(year=2021, month=1, day=1, tzinfo=datetime.UTC)
        records = list(json.loads(data.to_json(orient="index")).values())
        upload_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()
        generate_result = await client.post(
            "/generate-electricity-load",
            json={
                "dataset_id": upload_result["dataset_id"],
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        assert generate_result.status_code == 200, generate_result.json()
        get_result = await client.post(
            "/get-electricity-load",
            json={
                "dataset_id": generate_result.json()["dataset_id"],
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        assert get_result.status_code == 200, get_result.json()
        timestamps = get_result.json()["timestamps"]
        first_ts = datetime.datetime.fromisoformat(timestamps[0])
        assert first_ts.hour == 0, "First entry isn't 00:00"
        assert first_ts.minute == 0, "First entry isn't 00:00"
        assert first_ts == demo_start_ts
        last_ts = datetime.datetime.fromisoformat(timestamps[-1])
        assert last_ts.hour == 23, "Last entry isn't 23:30"
        assert last_ts.minute == 30, "Last entry isn't 23:30"
        assert last_ts == (demo_end_ts - datetime.timedelta(minutes=30))
        assert (
            len(timestamps) == len(item) == int((demo_end_ts - demo_start_ts) / datetime.timedelta(minutes=30))
            for item in get_result.json()["data"]
        )


class TestGetBlendedData:
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_can_get_blended_data(self, client: httpx.AsyncClient) -> None:
        elec_data = parse_half_hourly("./tests/data/test_elec.csv")
        elec_data["start_ts"] = elec_data.index
        metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "halfhourly"}
        records = json.loads(elec_data.to_json(orient="records"))
        elec_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

        demo_start_ts = elec_data.start_ts.min().replace(month=1, day=1)
        demo_end_ts = elec_data.start_ts.min().replace(month=12, day=31)
        generate_request = await client.post(
            "/generate-electricity-load",
            json={
                "dataset_id": elec_result["dataset_id"],
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        assert generate_request.status_code == 200, generate_request.text

        blended_result = await client.post(
            "/get-blended-electricity-load",
            json={
                "real_params": {
                    "dataset_id": elec_result["dataset_id"],
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
                "synthetic_params": {
                    "dataset_id": generate_request.json()["dataset_id"],
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
            },
        )

        _ = await client.post(
            "/get-electricity-load",
            json={
                "dataset_id": elec_result["dataset_id"],
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        synthetic_result = await client.post(
            "/get-electricity-load",
            json={
                "dataset_id": generate_request.json()["dataset_id"],
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        assert len(synthetic_result.json()) == len(blended_result.json())
