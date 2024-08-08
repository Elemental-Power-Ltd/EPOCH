"""Endpoint testing for client data endpoints."""

# ruff: noqa: D101, D102
from typing import AsyncGenerator

import pytest
import pytest_asyncio
import testing.postgresql  # type: ignore
from fastapi.testclient import TestClient

from app.database import Database, DBConnection, get_db_conn
from app.main import app
from app.models.core import ClientData, SiteData

pytest_plugins = ("pytest_asyncio",)

db_factory = testing.postgresql.PostgresqlFactory()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[TestClient, None]:
    """
    Get a FastAPI client for a single test.

    Each time a test requests this fixture, it'll create a new database (which can be slow)
    and populate it with some test data.
    It then overrides the `get_db_conn` for all the endpoints deeper in, using mysterious FastAPI magic.
    """
    underlying_db = db_factory()
    db = Database(dsn=underlying_db.url())

    await db.create_pool()
    assert db.pool is not None, "Could not create database pool"
    conn = await db.pool.acquire()
    await conn.execute("""CREATE ROLE python""")
    with open("./elementaldb_tables.sql") as fi:
        await conn.execute(fi.read())
    with open("./elementaldb_client_info.sql") as fi:
        await conn.execute(fi.read())

    async def override_get_db_conn() -> AsyncGenerator[DBConnection, None]:
        await db.create_pool()
        assert db.pool is not None, "Could not create database pool"
        conn = await db.pool.acquire()
        try:
            yield conn
        finally:
            await db.pool.release(conn)

    app.dependency_overrides[get_db_conn] = override_get_db_conn
    client = TestClient(app)
    yield client
    del app.dependency_overrides[get_db_conn]


@pytest.mark.asyncio
class TestClientData:
    async def test_list_clients(self, client: TestClient) -> None:
        response = client.post("/list-clients")
        assert response.status_code == 200
        assert response.json()[0]["client_id"] == "demo"

    async def test_add_client(self, client: TestClient) -> None:
        client_data = ClientData(client_id="new_client", name="New Client")
        response = client.post("/add-client", json=client_data.model_dump())
        assert response.status_code == 200
        assert response.json()[0] == client_data.model_dump()

    async def test_add_client_duplicate(self, client: TestClient) -> None:
        client_data = ClientData(client_id="duplicate_client", name="Demo Client")
        response = client.post("/add-client", json=client_data.model_dump())
        response = client.post("/add-client", json=client_data.model_dump())

        assert response.status_code == 400
        assert response.json()["detail"] == "Client ID duplicate_client already exists in the database."

    async def test_list_sites(self, client: TestClient) -> None:
        response = client.post("/list-sites", json={"client_id": "demo"})
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["site_id"] == "demo_cardiff"
        assert response.json()[1]["site_id"] == "demo_london"

    async def test_add_site(self, client: TestClient) -> None:
        site_data = SiteData(
            client_id="demo",
            site_id="new_site",
            name="New Site",
            location="Worksop",
            coordinates=(51.4789, -1.2345),
            address="123 Demo Street, Worksop, DN12 3AB",
        )
        response = client.post("/add-site", json=site_data.model_dump())
        assert response.status_code == 200
        assert SiteData(**response.json()[0]) == site_data

    async def test_add_site_duplicate(self, client: TestClient) -> None:
        site_data = SiteData(
            client_id="demo",
            site_id="demo_duplicate_site",
            name="Demo Site 1",
            location="Worksop",
            coordinates=(51.4789, -1.2345),
            address="123 Demo Street, Worksop, DN12 3AB",
        )
        response = client.post("/add-site", json=site_data.model_dump())
        response = client.post("/add-site", json=site_data.model_dump())
        assert response.status_code == 400
        assert response.json()["detail"] == "Site ID `demo_duplicate_site` already exists in the database."

    async def test_add_site_client_not_found(self, client: TestClient) -> None:
        site_data = SiteData(
            client_id="unknown_client",
            site_id="new_site",
            name="New Site",
            location="Worksop",
            coordinates=(51.4789, -1.2345),
            address="123 Demo Street, Worksop, DN12 3AB",
        )
        response = client.post("/add-site", json=site_data.model_dump())
        assert response.status_code == 400
        assert response.json()["detail"] == "No such client `unknown_client` exists in the database. Please create one."

    async def test_get_location(self, client: TestClient) -> None:
        response = client.post("/get-location", json={"site_id": "demo_london"})
        assert response.status_code == 200
        assert response.json() == "London"

    async def test_get_location_not_in_db(self, client: TestClient) -> None:
        response = client.post("/get-location", json={"site_id": "unknown_site"})
        assert response.status_code == 400
        assert response.json()["detail"] == "Site ID `unknown_site` has no location in the database."
