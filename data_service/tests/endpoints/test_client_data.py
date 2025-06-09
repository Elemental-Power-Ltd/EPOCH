"""Endpoint testing for client data endpoints."""

# ruff: noqa: D101, D102

import json
import uuid

import pytest
from httpx import AsyncClient

from app.dependencies import get_db_pool
from app.models.core import ClientData, SiteData


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
        assert response.status_code == 200
        assert response.json()[0] == client_data.model_dump()

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
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["site_id"] == "demo_cardiff"
        assert response.json()[1]["site_id"] == "demo_london"

    # @pytest.mark.asyncio
    # async def test_list_datasets(self, client: AsyncClient) -> None:
    #    response = await client.post("/list-datasets", json={"site_id": "demo_london"})
    #    assert response.status_code == 200
    #    assert len(response.json()) >= 1

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
        assert response.status_code == 200
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
        assert response.status_code == 200
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
        assert response.status_code == 200

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
            "renewables": {"yield_scalars": [100, 200]},
            "heat_pump": {"heat_power": 300},
        }
        response = await client.post(
            "/add-site-baseline", json={"site_id": {"site_id": "demo_london"}, "baseline": baseline}
        )
        assert response.status_code == 200, response.text
        response = await client.post("/get-site-baseline", json={"site_id": "demo_london"})
        assert response.status_code == 200, response.text
        returned_baseline = response.json()
        for key, val in baseline.items():
            assert key in returned_baseline
            for subkey, subval in val.items():  # type: ignore
                assert subkey in returned_baseline[key]
                assert returned_baseline[key][subkey] == subval

    @pytest.mark.asyncio
    async def test_cant_retrieve_bad_baseline(self, client: AsyncClient) -> None:
        """Test that we retrieve the stored baseline correctly."""
        baseline = {"bad_component": {"bad_subkey": "bad_value"}}
        # TODO (2025-03-03): This is an absolutely filthy way to get the testing database
        # pool connection! Do it properly with a DB fixture or a called endpoint.
        pool = await client._transport.app.dependency_overrides[get_db_pool]().__anext__()  # type: ignore
        await pool.execute(
            """INSERT INTO client_info.site_baselines (baseline_id, site_id, baseline) VALUES ($1, $2, $3)""",
            uuid.uuid4(),
            "demo_london",
            json.dumps(baseline),
        )
        response = await client.post("/get-site-baseline", json={"site_id": "demo_london"})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_cant_retrieve_bad_baseline_subkey(self, client: AsyncClient) -> None:
        """Test that we fail if a subkey is wrong."""
        baseline = {"grid": {"bad_subkey": "bad_value"}}
        # TODO (2025-03-03): This is an absolutely filthy way to get the testing database
        # pool connection! Do it properly with a DB fixture or a called endpoint.
        pool = await client._transport.app.dependency_overrides[get_db_pool]().__anext__()  # type: ignore
        await pool.execute(
            """INSERT INTO client_info.site_baselines (baseline_id, site_id, baseline) VALUES ($1, $2, $3)""",
            uuid.uuid4(),
            "demo_london",
            json.dumps(baseline),
        )
        response = await client.post("/get-site-baseline", json={"site_id": "demo_london"})
        assert response.status_code == 400
