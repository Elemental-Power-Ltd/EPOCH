"""Endpoint testing for client data endpoints."""

# ruff: noqa: D101, D102

import pytest
from httpx import AsyncClient

from app.models.core import ClientData, SiteData

# from tests.endpoints.conftest import client


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

    @pytest.mark.asyncio
    async def test_list_datasets(self, client: AsyncClient) -> None:
        response = await client.post("/list-datasets", json={"site_id": "amcott_house"})
        assert response.status_code == 200
        assert len(response.json()) >= 2

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
