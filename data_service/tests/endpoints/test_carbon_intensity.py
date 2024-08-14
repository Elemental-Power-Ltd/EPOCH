"""Endpoint testing for carbon intensity endpoints."""

# ruff: noqa: D101, D102, D103
import datetime

import pydantic
import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def demo_start_ts() -> datetime.datetime:
    return datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.UTC)


@pytest_asyncio.fixture
async def demo_end_ts() -> datetime.datetime:
    return datetime.datetime(year=2024, month=2, day=11, tzinfo=datetime.UTC)


@pytest_asyncio.fixture
async def demo_site_id() -> str:
    return "demo_london"


@pytest_asyncio.fixture
async def grid_co2_metadata(
    client: AsyncClient, demo_site_id: str, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
) -> pydantic.Json:
    result = await client.post(
        "/generate-grid-co2",
        json={"site_id": demo_site_id, "start_ts": demo_start_ts.isoformat(), "end_ts": demo_end_ts.isoformat()},
    )

    return result.json()


@pytest.mark.slow
class TestCarbonItensity:
    @pytest.mark.asyncio
    async def test_generate(self, grid_co2_metadata: pydantic.Json, demo_site_id: str) -> None:
        assert datetime.datetime.fromisoformat(grid_co2_metadata["created_at"]) > datetime.datetime.now(
            datetime.UTC
        ) - datetime.timedelta(minutes=1)
        assert grid_co2_metadata["site_id"] == demo_site_id
        assert grid_co2_metadata["is_regional"]

    @pytest.mark.asyncio
    async def test_generate_and_retrieve(
        self,
        grid_co2_metadata: pydantic.Json,
        client: AsyncClient,
        demo_start_ts: datetime.datetime,
        demo_end_ts: datetime.datetime,
    ) -> None:
        grid_co2_result = (
            await client.post(
                "/get-grid-co2",
                json={
                    "dataset_id": grid_co2_metadata["dataset_id"],
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
            )
        ).json()
        assert all(item["GridCO2"] > 0 for item in grid_co2_result)
        assert (
            len(grid_co2_result)
            == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(minutes=60).total_seconds()
        ), "Not enough entries in set"
