"""Unit and end to end tests for the thermal model."""

import datetime
import json

import httpx
import numpy as np
import pytest
import pytest_asyncio
from app.internal.gas_meters import parse_half_hourly
from app.internal.utils.uuid import uuid7
from app.models.core import DatasetTypeEnum
from app.models.heating_load import HeatingLoadRequest, ThermalModelResult
from app.routers.heating_load.thermal_model import file_params_with_db

from .conftest import get_pool_hack


@pytest_asyncio.fixture
async def uploaded_elec_data(client: httpx.AsyncClient) -> httpx.Response:
    """Upload elec meter as a fixture."""
    data = parse_half_hourly("./tests/data/test_elec.csv")
    data["start_ts"] = data.index
    metadata = {
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "dataset_id": str(uuid7()),
        "fuel_type": "elec",
        "site_id": "demo_london",
        "reading_type": "halfhourly",
        "is_synthetic": False,
    }
    records = json.loads(data.to_json(orient="records"))
    return await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})


@pytest_asyncio.fixture
async def uploaded_gas_data(client: httpx.AsyncClient) -> httpx.Response:
    """Upload gas meter as a fixture."""
    data = parse_half_hourly("./tests/data/test_gas.csv")
    data["start_ts"] = data.index
    metadata = {
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "dataset_id": str(uuid7()),
        "fuel_type": "gas",
        "site_id": "demo_london",
        "reading_type": "halfhourly",
        "is_synthetic": False,
    }
    records = json.loads(data.to_json(orient="records"))
    return await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})


@pytest.fixture
def thermal_model_result() -> ThermalModelResult:
    """Get a pre-generated thermal model for demo_london."""
    return ThermalModelResult(
        scale_factor=0.7757,
        ach=1.27,
        u_value=1.746,
        boiler_power=6.546e03,
        setpoint=18.0,
        dhw_usage=0.6576,
    )


@pytest_asyncio.fixture
async def uploaded_meter_data(
    uploaded_elec_data: httpx.Response, uploaded_gas_data: httpx.Response
) -> tuple[httpx.Response, httpx.Response]:
    """Upload gas and electricity meter as a fixture."""
    return (uploaded_elec_data, uploaded_gas_data)


class TestThermalModelEndpoint:
    """Test that the Thermal Model endpoint works all the way through."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.skip(reason="Thermal model too flaky")
    async def test_send_request(
        self, client: httpx.AsyncClient, uploaded_meter_data: tuple[httpx.Response, httpx.Response]
    ) -> None:
        """Test that we can fit a simple thermal model of Matt's house."""
        _, _ = uploaded_meter_data

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
        for key, val in params.items():
            if key != "r2_score":
                # We've picked a nonsense set of parameters here, so the r2 score will likely be very bad.
                assert val > 0, f"{key} is out of valid range"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.skip(reason="Thermal model too flaky")
    async def test_create_heat_load(
        self,
        client: httpx.AsyncClient,
        uploaded_meter_data: tuple[httpx.Response, httpx.Response],
        thermal_model_result: ThermalModelResult,
    ) -> None:
        """Test that we can fit a simple thermal model of Matt's house."""
        gas, elec = uploaded_meter_data

        start_ts = datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2025, month=1, day=1, tzinfo=datetime.UTC)
        task_id = uuid7()
        pool = await get_pool_hack(client)
        await file_params_with_db(
            pool=pool,
            site_id="demo_london",
            task_id=task_id,
            results=thermal_model_result,
            datasets={
                DatasetTypeEnum.GasMeterData: str(gas.json()["dataset_id"]),  # type: ignore
                DatasetTypeEnum.ElectricityMeterData: str(elec.json()["dataset_id"]),  # type: ignore
            },
        )
        hl_gen_response = await client.post(
            "/generate-thermal-model-heating-load",
            json=json.loads(
                HeatingLoadRequest(
                    dataset_id=uuid7(),
                    site_id="demo_london",
                    start_ts=start_ts,
                    end_ts=end_ts,
                    structure_id=task_id,
                    seed=int(np.pi * 10**9),
                ).model_dump_json()
            ),
        )
        assert hl_gen_response.status_code == 200, hl_gen_response.text
        data = hl_gen_response.json()
        # assert data["num_entries"] == 17568  # it was a leap year

        hl_data_response = await client.post(
            "/get-heating-load",
            json={"dataset_id": data["dataset_id"], "start_ts": start_ts.isoformat(), "end_ts": end_ts.isoformat()},
        )
        assert hl_data_response.status_code == 200
        heatload = hl_data_response.json()["data"][0]["reduced_hload"]
        assert all(item >= 0 for item in heatload), heatload
