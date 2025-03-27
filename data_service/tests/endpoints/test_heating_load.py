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
    @pytest.mark.slow
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
        assert any(heating_load_result.json()["data"]) > 0
        assert any(heating_load_result.json()["data"]) != 0

        assert generated_metadata.json()["site_id"] == "demo_london"
        assert generated_metadata.json()["params"]["solar_gain"] >= 0
        assert 0.8 <= generated_metadata.json()["params"]["r2_score"] < 1.0
        assert 0 <= generated_metadata.json()["params"]["smoothing"] <= 1.0
        assert generated_metadata.json()["params"]["heating_kwh"] > 0

    @pytest.mark.asyncio
    @pytest.mark.external
    @pytest.mark.slow
    async def test_generate_and_get_with_intervention(
        self, uploaded_meter_data: pydantic.Json, client: httpx.AsyncClient
    ) -> None:
        dataset_id = uploaded_meter_data["dataset_id"]

        no_intervention_metadata = await client.post(
            "/generate-heating-load",
            json={
                "dataset_id": dataset_id,
                "start_ts": "2023-01-01T00:00:00Z",
                "end_ts": "2023-02-01T00:00:00Z",
                "interventions": [],
            },
        )
        with_intervention_metadata = await client.post(
            "/generate-heating-load",
            json={
                "dataset_id": dataset_id,
                "start_ts": "2023-01-01T00:00:00Z",
                "end_ts": "2023-02-01T00:00:00Z",
                "interventions": ["cladding"],
            },
        )

        no_intervention_result = await client.post(
            "/get-heating-load", json={"dataset_id": no_intervention_metadata.json()["dataset_id"]}
        )
        with_intervention_result = await client.post(
            "/get-heating-load", json={"dataset_id": with_intervention_metadata.json()["dataset_id"]}
        )
        assert (
            no_intervention_metadata.json()["params"]["heating_kwh"]
            > with_intervention_metadata.json()["params"]["heating_kwh"]
        )
        no_intervention_total = sum(no_intervention_result.json()["data"][0]["reduced_hload"])
        with_intervention_total = sum(with_intervention_result.json()["data"][0]["reduced_hload"])
        assert with_intervention_total < no_intervention_total

    @pytest.mark.asyncio
    @pytest.mark.external
    @pytest.mark.slow
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

        timestamps = heating_load_result.json()["timestamps"]
        first_ts = datetime.datetime.fromisoformat(timestamps[0])
        assert first_ts.hour == 0, "First entry isn't 00:00"
        assert first_ts.minute == 0, "First entry isn't 00:00"
        assert first_ts == start_ts
        last_ts = datetime.datetime.fromisoformat(timestamps[-1])
        assert last_ts.hour == 23, "Last entry isn't 23:30"
        assert last_ts.minute == 30, "Last entry isn't 23:30"
        assert last_ts == (end_ts - datetime.timedelta(minutes=30))
        assert (
            len(timestamps)
            == len(heating_load_result.json()["data"][0]["reduced_hload"])
            == int((end_ts - start_ts) / datetime.timedelta(minutes=30))
        )


class TestFabricInterventionCost:
    @pytest.mark.asyncio
    async def test_no_intervention(self, client: httpx.AsyncClient) -> None:
        """Check that doing nothing costs nothing."""
        no_interventions_res = await client.post("/get-intervention-cost", json={"site_id": "demo_london"})
        assert no_interventions_res.status_code == 200
        assert no_interventions_res.json()["total"] == 0.0
        assert not no_interventions_res.json()["breakdown"]

    @pytest.mark.asyncio
    async def test_loft_intervention(self, client: httpx.AsyncClient) -> None:
        """Check that lofts cost more than nothing."""
        loft_interventions_res = await client.post(
            "/get-intervention-cost", json={"site_id": "demo_london", "interventions": ["loft"]}
        )
        assert loft_interventions_res.status_code == 200
        assert loft_interventions_res.json()["total"] > 0
        assert list(loft_interventions_res.json()["breakdown"].keys()) == ["loft"]

    @pytest.mark.asyncio
    async def test_multi_intervention(self, client: httpx.AsyncClient) -> None:
        """Check that two interventions cost more than one."""
        loft_interventions_res = await client.post(
            "/get-intervention-cost", json={"site_id": "demo_london", "interventions": ["loft"]}
        )
        two_interventions_res = await client.post(
            "/get-intervention-cost", json={"site_id": "demo_london", "interventions": ["loft", "double_glazing"]}
        )
        three_interventions_res = await client.post(
            "/get-intervention-cost",
            json={"site_id": "demo_london", "interventions": ["loft", "double_glazing", "cladding"]},
        )
        assert two_interventions_res.status_code == 200
        assert two_interventions_res.json()["total"] > loft_interventions_res.json()["total"]
        assert three_interventions_res.json()["total"] > two_interventions_res.json()["total"]
        assert set(two_interventions_res.json()["breakdown"].keys()) == {"loft", "double_glazing"}
        assert set(three_interventions_res.json()["breakdown"].keys()) == {"loft", "double_glazing", "cladding"}

    @pytest.mark.asyncio
    async def test_two_intervention(self, client: httpx.AsyncClient) -> None:
        """Check that two interventions cost more than one."""
        bad_interventions_res = await client.post(
            "/get-intervention-cost",
            json={"site_id": "demo_london", "interventions": ["extremely bad nonexistent intervention"]},
        )
        assert bad_interventions_res.status_code == 422
        assert "extremely bad nonexistent intervention" in bad_interventions_res.json()["detail"][0]["input"]
