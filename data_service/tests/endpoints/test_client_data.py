"""Endpoint testing for client data endpoints."""

# ruff: noqa: D101, D102

import json

import pytest
from httpx import AsyncClient

from app.internal.utils.uuid import uuid7
from app.models.core import ClientData, SiteData

from .conftest import get_pool_hack


class TestClientData:
    @pytest.mark.asyncio
    async def test_list_clients(self, client: AsyncClient) -> None:
        response = await client.post("/list-clients")
        assert response.status_code == 200
        assert response.json()[0]["client_id"] == "demo"

    @pytest.mark.asyncio
    async def test_add_client(self, client: AsyncClient) -> None:
        client_data = ClientData(client_id="new_client", name="New Client")
        response = await client.post("/add-client", json=client_data.model_dump())
        assert response.is_success
        assert response.json() == client_data.model_dump()

    @pytest.mark.asyncio
    async def test_add_client_duplicate(self, client: AsyncClient) -> None:
        client_data = ClientData(client_id="duplicate_client", name="Demo Client")
        response = await client.post("/add-client", json=client_data.model_dump())
        response = await client.post("/add-client", json=client_data.model_dump())

        assert response.status_code == 400
        assert response.json()["detail"] == "Client ID duplicate_client already exists in the database."

    @pytest.mark.asyncio
    async def test_list_sites(self, client: AsyncClient) -> None:
        response = await client.post("/list-sites", json={"client_id": "demo"})
        assert response.is_success
        assert len(response.json()) == 2
        assert response.json()[0]["site_id"] == "demo_cardiff"
        assert response.json()[1]["site_id"] == "demo_london"

    @pytest.mark.asyncio
    async def test_add_site(self, client: AsyncClient) -> None:
        site_data = SiteData(
            client_id="demo",
            site_id="new_site",
            name="New Site",
            location="Worksop",
            coordinates=(51.4789, -1.2345),
            address="123 Demo Street, Worksop, DN12 3AB",
        )
        response = await client.post("/add-site", json=site_data.model_dump())
        assert response.is_success
        assert SiteData(**response.json()[0]) == site_data

    @pytest.mark.asyncio
    async def test_add_site_duplicate(self, client: AsyncClient) -> None:
        site_data = SiteData(
            client_id="demo",
            site_id="demo_duplicate_site",
            name="Demo Site 1",
            location="Worksop",
            coordinates=(51.4789, -1.2345),
            address="123 Demo Street, Worksop, DN12 3AB",
        )
        response = await client.post("/add-site", json=site_data.model_dump())
        response = await client.post("/add-site", json=site_data.model_dump())
        assert response.status_code == 400
        assert response.json()["detail"] == "Site ID `demo_duplicate_site` already exists in the database."

    @pytest.mark.asyncio
    async def test_cant_add_bad_postcode(self, client: AsyncClient) -> None:
        """Test that we can't add a site with a bad postcode."""
        site_data = {
            "client_id": "demo",
            "site_id": "demo_bad_postcode",
            "name": "Demo Bad Postcode",
            "location": "Worksop",
            "coordinates": (51.4789, -1.2345),
            "address": "123 Demo Street, Worksop, BAD POSTCODE",
        }
        response = await client.post("/add-site", json=site_data)
        assert response.status_code == 422
        assert "postcode" in response.text

    @pytest.mark.asyncio
    async def test_cant_add_no_postcode(self, client: AsyncClient) -> None:
        """Test that we can't add a site without postcode."""
        site_data = {
            "client_id": "demo",
            "site_id": "demo_bad_postcode",
            "name": "Demo Bad Postcode",
            "location": "Worksop",
            "coordinates": (51.4789, -1.2345),
            "address": "123 Demo Street",
        }
        response = await client.post("/add-site", json=site_data)
        assert response.status_code == 422
        assert "postcode" in response.text

    @pytest.mark.asyncio
    async def test_add_site_client_not_found(self, client: AsyncClient) -> None:
        site_data = SiteData(
            client_id="unknown_client",
            site_id="new_site",
            name="New Site",
            location="Worksop",
            coordinates=(51.4789, -1.2345),
            address="123 Demo Street, Worksop, DN12 3AB",
        )
        response = await client.post("/add-site", json=site_data.model_dump())
        assert response.status_code == 400
        assert response.json()["detail"] == "No such client `unknown_client` exists in the database. Please create one."

    @pytest.mark.asyncio
    async def test_get_location(self, client: AsyncClient) -> None:
        response = await client.post("/get-location", json={"site_id": "demo_london"})
        assert response.is_success
        assert response.json() == "London"

    @pytest.mark.asyncio
    async def test_get_location_not_in_db(self, client: AsyncClient) -> None:
        response = await client.post("/get-location", json={"site_id": "unknown_site"})
        assert response.status_code == 400
        assert response.json()["detail"] == "Site ID `unknown_site` has no location in the database."


class TestSiteBaseline:
    """Test that we can store and retrieve baseline configurations."""

    @pytest.mark.asyncio
    async def test_get_baseline_real_site(self, client: AsyncClient) -> None:
        """Test that we can get the baseline for a real site."""
        response = await client.post("/get-site-baseline", json={"site_id": "demo_london"})
        assert response.is_success

    @pytest.mark.asyncio
    async def test_get_baseline_fake_site(self, client: AsyncClient) -> None:
        """Test that we fail sensibly for the baseline for a fake site."""
        response = await client.post("/get-site-baseline", json={"site_id": "unknown_site"})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_baseline_fake_site(self, client: AsyncClient) -> None:
        """Test that we fail sensibly for the baseline for a fake site."""
        response = await client.post(
            "/add-site-baseline",
            json={"site_id": {"site_id": "unknown_site"}, "baseline": {"grid": {"grid_import": 100, "grid_export": 100}}},
        )
        assert response.status_code == 400, response.text

    @pytest.mark.asyncio
    async def test_add_baseline_real_site(self, client: AsyncClient) -> None:
        """Test that we retrieve the stored baseline correctly."""
        baseline = {
            "grid": {"grid_import": 100, "grid_export": 100},
            "solar_panels": [{"yield_scalar": 100, "yield_index": 0}, {"yield_scalar": 200, "yield_index": 1}],
            "heat_pump": {"heat_power": 300},
        }
        response = await client.post(
            "/add-site-baseline", json={"site_id": {"site_id": "demo_london"}, "baseline": baseline}
        )
        assert response.is_success, response.text
        response = await client.post("/get-site-baseline", json={"site_id": "demo_london"})
        assert response.is_success, response.text
        returned_baseline = response.json()
        for key, val in baseline.items():
            assert key in returned_baseline

            if isinstance(val, list):
                for i, component in enumerate(val):
                    for subkey, subval in component.items():
                        assert subkey in returned_baseline[key][i]
                        assert returned_baseline[key][i][subkey] == subval
            else:
                for subkey, subval in val.items():  # type: ignore
                    assert subkey in returned_baseline[key]
                    assert returned_baseline[key][subkey] == subval

    @pytest.mark.asyncio
    async def test_cant_retrieve_bad_baseline(self, client: AsyncClient) -> None:
        """Test that we retrieve the stored baseline correctly."""
        baseline = {"bad_component": {"bad_subkey": "bad_value"}}
        pool = await get_pool_hack(client)
        await pool.execute(
            """INSERT INTO client_info.site_baselines (baseline_id, site_id, baseline) VALUES ($1, $2, $3)""",
            uuid7(),
            "demo_london",
            json.dumps(baseline),
        )
        response = await client.post("/get-site-baseline", json={"site_id": "demo_london"})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_cant_retrieve_bad_baseline_subkey(self, client: AsyncClient) -> None:
        """Test that we fail if a subkey is wrong."""
        baseline = {"grid": {"bad_subkey": "bad_value"}}
        pool = await get_pool_hack(client)
        await pool.execute(
            """INSERT INTO client_info.site_baselines (baseline_id, site_id, baseline) VALUES ($1, $2, $3)""",
            uuid7(),
            "demo_london",
            json.dumps(baseline),
        )
        response = await client.post("/get-site-baseline", json={"site_id": "demo_london"})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_baseline_floor_area(self, client: AsyncClient) -> None:
        """Test that we insert and get out floor areas."""
        baseline = {
            "building": {"floor_area": 89.0},
        }
        response = await client.post(
            "/add-site-baseline", json={"site_id": {"site_id": "demo_london"}, "baseline": baseline}
        )
        response = await client.post("/get-site-baseline", json={"site_id": "demo_london"})
        assert response.is_success
        data = response.json()
        assert data["building"]["floor_area"] == 89.0


class TestBaselineTariff:
    @pytest.mark.asyncio
    async def test_add_baseline_tariff(self, client: AsyncClient) -> None:
        """Test that we can insert a baseline tariff."""
        baseline = {
            "building": {"floor_area": 89.0},
        }
        response = await client.post(
            "/add-site-baseline", json={"site_id": {"site_id": "demo_london"}, "baseline": baseline}
        )
        assert response.is_success
        baseline_id = response.json()
        response = await client.post("/get-site-baseline", json={"dataset_id": baseline_id})
        assert response.is_success
        data = response.json()
        response = await client.post(
            "/add-baseline-tariff",
            json={
                "tariff_req": {
                    "site_id": "demo_london",
                    "start_ts": "2022-01-01T00:00:00Z",
                    "end_ts": "2022-02-01T00:00:00Z",
                    "tariff_name": "fixed",
                    "day_cost": 100.0,
                },
                "baseline_id": {"dataset_id": baseline_id},
            },
        )
        assert response.is_success, response.text
        data = response.json()
        assert data["day_cost"] == 100.0

    @pytest.mark.asyncio
    async def test_pass_tariff_forward(self, client: AsyncClient) -> None:
        """Test that we can carry a baseline tariff forward.s."""
        baseline = {
            "building": {"floor_area": 89.0},
        }
        response = await client.post(
            "/add-site-baseline", json={"site_id": {"site_id": "demo_london"}, "baseline": baseline}
        )
        assert response.is_success
        baseline_id = response.json()

        tariff_response = await client.post(
            "/add-baseline-tariff",
            json={
                "tariff_req": {
                    "site_id": "demo_london",
                    "start_ts": "2022-01-01T00:00:00Z",
                    "end_ts": "2022-02-01T00:00:00Z",
                    "tariff_name": "fixed",
                    "day_cost": 100.0,
                },
                "baseline_id": {"dataset_id": baseline_id},
            },
        )
        assert tariff_response.is_success, tariff_response.text

        baseline = {
            "building": {"floor_area": 90.0},
        }
        response = await client.post(
            "/add-site-baseline", json={"site_id": {"site_id": "demo_london"}, "baseline": baseline}
        )
        list_resp = await client.post("/list-site-baselines", json={"site_id": "demo_london"})
        assert list_resp.is_success, list_resp.text
        list_data = list_resp.json()
        assert list_data[0]["tariff_id"] == tariff_response.json()["dataset_id"], "Tariff ID missing from new entry"
        assert list_data[1]["tariff_id"] == tariff_response.json()["dataset_id"], "Tariff ID missing from new entry"


class TestSolarLocations:
    @pytest.mark.asyncio
    async def test_get_none_locations(self, client: AsyncClient) -> None:
        """Test that we get an empty list if there are no locations."""
        response = await client.post("/get-solar-locations", json={"site_id": "demo_london"})
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_add_and_get_locations(self, client: AsyncClient) -> None:
        """Test that we can add and retrieve a location."""
        solar_data = {
            "site_id": "demo_london",
            "name": "Main Roof",
            "renewables_location_id": "demo_london_mainroof",
            "tilt": 35,
            "azimuth": 178,
            "maxpower": 6.0,
        }
        add_response = await client.post("/add-solar-location", json=solar_data)
        assert add_response.status_code == 200, add_response.text

        get_response = await client.post("/get-solar-locations", json={"site_id": "demo_london"})
        assert get_response.status_code == 200, get_response.text
        got_data = get_response.json()[0]
        for key, val in solar_data.items():
            assert key in got_data
            assert val == got_data[key]

    @pytest.mark.asyncio
    async def test_cant_add_bad_id(self, client: AsyncClient) -> None:
        """Test that we can't add a site with a bad ID."""
        solar_data = {
            "site_id": "demo_london",
            "name": "Main Roof",
            "renewables_location_id": "BAD_LOCATION_ID",
            "tilt": 35,
            "azimuth": 178,
            "maxpower": 6.0,
        }
        add_response = await client.post("/add-solar-location", json=solar_data)
        assert add_response.status_code == 422, add_response.text

    @pytest.mark.asyncio
    async def test_cant_add_repeated(self, client: AsyncClient) -> None:
        """Test that we can't add a site twice."""
        solar_data = {
            "site_id": "demo_london",
            "name": "Main Roof",
            "renewables_location_id": "demo_london_mainroof",
            "tilt": 35,
            "azimuth": 178,
            "maxpower": 6.0,
        }
        add_response = await client.post("/add-solar-location", json=solar_data)
        assert add_response.status_code == 200, add_response.text

        add_response_2 = await client.post("/add-solar-location", json=solar_data)
        assert add_response_2.status_code == 400, add_response.text
