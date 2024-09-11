"""Tests for electrical data synthesis."""

# ruff: noqa: D101, D102, D103
import json

import httpx
import pandas as pd
import pytest
import numpy as np
from app.internal.gas_meters import parse_half_hourly
import datetime

class TestUploadMeterData:
    @pytest.mark.asyncio
    async def test_upload_pre_parsed_with_specified(self, client: httpx.AsyncClient) -> None:
        raw_data = parse_half_hourly("./tests/data/test_elec.csv")
        data = raw_data[["consumption"]].resample(pd.Timedelta(days=29)).sum()
        data["start_ts"] = data.index
        data["end_ts"] = data.index + pd.Timedelta(days=29)
        metadata = {
            "created_at": "2024-08-14T10:31:00Z",
            "dataset_id": "1db34dd6-0e3a-4ed1-8a2a-a84e74550ae4",
            "fuel_type": "elec",
            "site_id": "demo_london",
            "reading_type": "halfhourly",
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
        data["end_ts"] = np.minimum(month_ends.to_numpy()[:, 0], (data.index + pd.offsets.MonthEnd()).to_numpy())
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
                "end_ts": demo_end_ts.isoformat()
            },
        )
        assert generate_result.status_code == 200, generate_result.json()
        get_result = await client.post(
            "/get-electricity-load",
            json={
                "dataset_id": generate_result.json()["dataset_id"],
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat()
            },
        )
        assert get_result.status_code == 200, get_result.json()
        assert get_result.json()[-1]["StartTime"] == "23:30"
        assert get_result.json()[0]["Date"] == demo_start_ts.strftime("%d-%b")
        assert get_result.json()[-1]["Date"] == (demo_end_ts - pd.Timedelta(minutes=30)).strftime("%d-%b")
        expected_len = int((demo_end_ts - demo_start_ts) / pd.Timedelta(minutes=30))
        assert len(get_result.json()) == expected_len

class TestGetBlendedData:
    @pytest.mark.asyncio
    async def test_can_get_blended_data(self, client: httpx.AsyncClient) -> None:
        elec_data = parse_half_hourly("./tests/data/test_elec.csv")
        elec_data["start_ts"] = elec_data.index
        metadata = {"fuel_type": "elec", "site_id": "demo_london", "reading_type": "halfhourly"}
        records = json.loads(elec_data.to_json(orient="records"))
        elec_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()

        demo_start_ts = elec_data.start_ts.min().replace(month=1, day=1)
        demo_end_ts =  elec_data.start_ts.min().replace(month=12, day=31)
        generate_request = await client.post("/generate-electricity-load",
                                             json={"dataset_id": elec_result["dataset_id"],
                                                   "start_ts": demo_start_ts.isoformat(),
                                                   "end_ts": demo_end_ts.isoformat()})
        assert generate_request.status_code == 200, generate_request.text

        blended_result = await client.post("/get-blended-electricity-load",
                                         json={"real_params": {"dataset_id": elec_result["dataset_id"],
                                                               "start_ts": demo_start_ts.isoformat(),
                                                                "end_ts": demo_end_ts.isoformat()},
                                                                "synthetic_params": {"dataset_id": generate_request.json()["dataset_id"],
                                                               "start_ts": demo_start_ts.isoformat(),
                                                                "end_ts": demo_end_ts.isoformat()}})
        
        real_result = await client.post("/get-electricity-load",
                                         json={"dataset_id": elec_result["dataset_id"],
                                                               "start_ts": demo_start_ts.isoformat(),
                                                                "end_ts": demo_end_ts.isoformat()})
        synthetic_result = await client.post("/get-electricity-load",
                                         json={"dataset_id": generate_request.json()["dataset_id"],
                                            "start_ts": demo_start_ts.isoformat(),
                                            "end_ts": demo_end_ts.isoformat()})
        assert len(synthetic_result.json()) == len(blended_result.json())