"""Tests for heating load calculation."""

# ruff: noqa: D101, D102, D103
import datetime
import json
from pathlib import Path
from typing import cast

import httpx
import pytest
import pytest_asyncio

from app.internal.epl_typing import Jsonable
from app.internal.gas_meters import parse_half_hourly


@pytest_asyncio.fixture
async def uploaded_meter_data(client: httpx.AsyncClient) -> dict[str, Jsonable]:
    data = parse_half_hourly("./tests/data/test_gas.csv")
    data["start_ts"] = data.index
    metadata = {"fuel_type": "gas", "site_id": "demo_london", "reading_type": "halfhourly"}
    records = json.loads(data.to_json(orient="records"))
    upload_result = (await client.post("/upload-meter-entries", json={"metadata": metadata, "data": records})).json()
    return cast(dict[str, Jsonable], upload_result)


class TestHeatingLoad:
    @pytest.mark.asyncio
    @pytest.mark.external
    @pytest.mark.slow
    async def test_generate_and_get_heating_load(
        self, uploaded_meter_data: dict[str, Jsonable], client: httpx.AsyncClient
    ) -> None:
        dataset_id = uploaded_meter_data["dataset_id"]

        generated_metadata = await client.post(
            "/generate-heating-load",
            json={"dataset_id": dataset_id, "start_ts": "2023-01-01T00:00:00Z", "end_ts": "2023-02-01T00:00:00Z"},
        )
        assert generated_metadata.status_code == 200, generated_metadata.text
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
        self, uploaded_meter_data: dict[str, Jsonable], client: httpx.AsyncClient
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
    async def test_generate_THIRD_PARTY(self, uploaded_meter_data: dict[str, Jsonable], client: httpx.AsyncClient) -> None:
        dataset_id = uploaded_meter_data["dataset_id"]

        no_intervention_result = await client.post(
            "/generate-heating-load",
            json={
                "dataset_id": dataset_id,
                "start_ts": "2023-01-01T00:00:00Z",
                "end_ts": "2023-02-01T00:00:00Z",
                "interventions": [],
                "savings_percentage": 0.0,
                "model_type": "regression",
                "surveyed_sizes": {"total_floor_area": 200, "exterior_wall_area": 100},
            },
        )
        assert no_intervention_result.status_code == 200, no_intervention_result.text
        with_intervention_metadata = await client.post(
            "/generate-heating-load",
            json={
                "dataset_id": dataset_id,
                "start_ts": "2023-01-01T00:00:00Z",
                "end_ts": "2023-02-01T00:00:00Z",
                "interventions": ["Fineo Glazing", "Insulation to ceiling void"],
                "savings_percentage": 0.12,
                "surveyed_sizes": {"total_floor_area": 88, "exterior_wall_area": 100},
            },
        )

        with_intervention_result = await client.post(
            "/get-heating-load", json={"dataset_id": with_intervention_metadata.json()["dataset_id"]}
        )
        assert with_intervention_result.status_code == 200, with_intervention_result.text
        data = with_intervention_result.json()
        assert len(data["data"][0]["reduced_hload"]) == 1488
        assert data["data"][0]["cost"] > 1000

        listed_metadata = await client.post(
            "/list-latest-datasets",
            json={
                "site_id": "demo_london",
                "start_ts": "2023-01-01T00:00:00Z",
                "end_ts": "2023-02-01T00:00:00Z",
            },
        )
        assert listed_metadata.status_code == 200, listed_metadata.text
        final_id = with_intervention_metadata.json()["dataset_id"]
        assert final_id in listed_metadata.text

        got_metadata = await client.post(
            "/get-latest-datasets",
            json={
                "site_id": "demo_london",
                "start_ts": "2023-01-01T00:00:00Z",
                "end_ts": "2023-02-01T00:00:00Z",
            },
        )
        assert got_metadata.status_code == 200, got_metadata.text
        got_datasets = got_metadata.json()
        assert "heat" in got_datasets, got_datasets.keys()
        print(got_metadata.json()["heat"]["data"])
        assert len(got_datasets["heat"]["data"]) == 2
        assert got_datasets["heat"]["data"][1]["cost"] > 100
        assert len(got_datasets["heat"]["data"][1]["reduced_hload"]) == 1488

    @pytest.mark.asyncio
    @pytest.mark.external
    @pytest.mark.slow
    async def test_heating_load_right_length(self, uploaded_meter_data: dict[str, Jsonable], client: httpx.AsyncClient) -> None:
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


class TestPHPPHeatingLoad:
    """Test generating heating loads from a PHPP."""

    @pytest_asyncio.fixture
    async def uploaded_phpp(self, client: httpx.AsyncClient, phpp_fpath: Path) -> dict[str, Jsonable]:
        """Upload a PHPP for use elsewhere."""
        with phpp_fpath.open("rb") as fi:
            resp = await client.post(
                "/upload-phpp",
                files={
                    "file": (phpp_fpath.stem, fi, "application/vnd.ms-excel"),
                },
                data={"site_id": "demo_london"},
            )
        assert resp.status_code == 200
        return cast(dict[str, Jsonable], resp.json())

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_auto_phpp(
        self, client: httpx.AsyncClient, uploaded_meter_data: dict[str, Jsonable], uploaded_phpp: dict[str, Jsonable]
    ) -> None:
        """Test that an automatic generate heating load will create a PHPP load."""
        meter_data, _ = uploaded_meter_data, uploaded_phpp

        start_ts = datetime.datetime(year=2023, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2023, month=2, day=1, tzinfo=datetime.UTC)

        generated_resp = await client.post(
            "/generate-heating-load",
            json={"dataset_id": meter_data["dataset_id"], "start_ts": start_ts.isoformat(), "end_ts": end_ts.isoformat()},
        )
        assert generated_resp.status_code == 200, generated_resp.text
        generated_metadata = generated_resp.json()
        assert generated_metadata["generation_method"] == "phpp"

        hload_resp = await client.post("/get-heating-load", json={"dataset_id": generated_metadata["dataset_id"]})
        hload_data = hload_resp.json()["data"][0]
        assert hload_data["cost"] == 0, "Cost is zero with no interventions"
        assert hload_data["peak_hload"] > 150, "Peak hload too low in response"
        assert all(item >= 0 for item in hload_data["reduced_hload"])

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_auto_phpp_intervention(
        self, client: httpx.AsyncClient, uploaded_meter_data: dict[str, Jsonable], uploaded_phpp: dict[str, Jsonable]
    ) -> None:
        """Test that an automatic generate heating load will create a PHPP load with interventions."""
        meter_data, _ = uploaded_meter_data, uploaded_phpp

        start_ts = datetime.datetime(year=2023, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2023, month=2, day=1, tzinfo=datetime.UTC)

        generated_resp = await client.post(
            "/generate-heating-load",
            json={
                "dataset_id": meter_data["dataset_id"],
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
                "interventions": ["Fineo Glazing"],
            },
        )
        assert generated_resp.status_code == 200, generated_resp.text
        generated_metadata = generated_resp.json()
        assert generated_metadata["generation_method"] == "phpp"

        hload_resp = await client.post("/get-heating-load", json={"dataset_id": generated_metadata["dataset_id"]})
        hload_data = hload_resp.json()["data"][0]
        assert hload_data["cost"] > 10_000, "Cost should be big"
        assert hload_data["peak_hload"] < 191, "Peak hload should be lower than non-intervention"
        assert all(item >= 0 for item in hload_data["reduced_hload"])
