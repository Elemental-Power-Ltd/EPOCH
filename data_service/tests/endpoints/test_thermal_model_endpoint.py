"""Unit and end to end tests for the thermal model."""

import datetime
import json
import uuid

import httpx
import pytest

from typing import Awaitable
from app.internal.gas_meters import parse_half_hourly


@pytest.fixture
async def uploaded_elec_data(client: httpx.AsyncClient) -> httpx.Response:
    """Upload elec meter as a fixture."""
    data = parse_half_hourly("./tests/data/test_elec.csv")
    data["start_ts"] = data.index
    metadata = {
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "dataset_id": str(uuid.uuid4()),
        "fuel_type": "elec",
        "site_id": "demo_london",
        "reading_type": "halfhourly",
        "is_synthetic": False,
    }
    records = json.loads(data.to_json(orient="records"))
    return await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})


@pytest.fixture
async def uploaded_gas_data(client: httpx.AsyncClient) -> httpx.Response:
    """Upload gas meter as a fixture."""
    data = parse_half_hourly("./tests/data/test_gas.csv")
    data["start_ts"] = data.index
    metadata = {
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "dataset_id": str(uuid.uuid4()),
        "fuel_type": "gas",
        "site_id": "demo_london",
        "reading_type": "halfhourly",
        "is_synthetic": False,
    }
    records = json.loads(data.to_json(orient="records"))
    return await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})


@pytest.fixture
async def uploaded_meter_data(
    uploaded_elec_data: Awaitable[httpx.Response], uploaded_gas_data: Awaitable[httpx.Response]
) -> tuple[httpx.Response, httpx.Response]:
    """Upload gas and electricity meter as a fixture."""
    return (await uploaded_elec_data, await uploaded_gas_data)


class TestThermalModelEndpoint:
    """Test that the Thermal Model endpoint works all the way through."""

    @pytest.mark.asyncio
    async def test_send_request(
        self, client: httpx.AsyncClient, uploaded_meter_data: Awaitable[tuple[httpx.Response, httpx.Response]]
    ) -> None:
        """Test that we can fit a simple thermal model of Matt's house."""
        _, _ = await uploaded_meter_data

        response = await client.post(
            "/fit-thermal-model",
            json={
                "site_id": "demo_london",
                "start_ts": datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.UTC).isoformat(),
                "end_ts": datetime.datetime(year=2025, month=1, day=1, tzinfo=datetime.UTC).isoformat(),
            },
        )
        assert response.status_code == 200, response.text

        mdl_response = await client.post(
            "/get-thermal-model",
            json={"dataset_id": response.json()["task_id"]},
        )
        assert mdl_response.status_code == 200, mdl_response.text
        params = mdl_response.json()
        for val in params.values():
            assert val > 0
