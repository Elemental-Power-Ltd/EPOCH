"""Tests for renewables generation endpoints."""

# ruff: noqa: D101, D102, D103
import datetime
import uuid

import httpx
import pytest


@pytest.fixture
def demo_start_ts() -> datetime.datetime:
    return datetime.datetime(year=2020, month=1, day=1, hour=0, minute=0, second=0, tzinfo=datetime.UTC)


@pytest.fixture
def demo_end_ts() -> datetime.datetime:
    return datetime.datetime(year=2021, month=1, day=1, hour=0, minute=0, second=0, tzinfo=datetime.UTC)


class TestRenewables:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_renewables_metadata(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        result = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": 178,
                    "tilt": 30,
                    "tracking": False,
                },
            )
        ).json()
        assert "dataset_id" in result
        assert (
            datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=1)
            <= datetime.datetime.fromisoformat(result["created_at"])
            <= datetime.datetime.now(datetime.UTC)
        )
        assert result["parameters"]["azimuth"] == 178
        assert result["parameters"]["tilt"] == 30
        assert result["site_id"] == "demo_london"

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_renewables_without_optima(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        result = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": None,
                    "tilt": None,
                    "tracking": False,
                },
            )
        ).json()
        assert "dataset_id" in result
        assert (
            datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=1)
            <= datetime.datetime.fromisoformat(result["created_at"])
            <= datetime.datetime.now(datetime.UTC)
        )
        assert result["parameters"]["azimuth"] == pytest.approx(176, rel=5)
        assert result["parameters"]["tilt"] == pytest.approx(40, rel=5)
        assert result["site_id"] == "demo_london"

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_and_get_renewables(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        metadata = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": None,
                    "tilt": None,
                    "tracking": False,
                },
            )
        ).json()
        results = (
            await client.post(
                "/get-renewables-generation",
                json={
                    "dataset_id": metadata["dataset_id"],
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
            )
        ).json()

        assert all(
            len(results["timestamps"])
            == len(item)
            == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
            for item in results["data"]
        )
        assert all(all(item) >= 0 for item in results["data"])

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_and_get_renewables_not_full_year(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        start_ts = demo_start_ts - datetime.timedelta(days=99)
        end_ts = demo_end_ts - datetime.timedelta(days=101)
        metadata = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": start_ts.isoformat(),
                    "end_ts": end_ts.isoformat(),
                    "azimuth": None,
                    "tilt": None,
                    "tracking": False,
                },
            )
        ).json()
        results = (
            await client.post(
                "/get-renewables-generation",
                json={
                    "dataset_id": metadata["dataset_id"],
                    "start_ts": start_ts.isoformat(),
                    "end_ts": end_ts.isoformat(),
                },
            )
        ).json()

        assert all(
            len(results["timestamps"])
            == len(item)
            == (end_ts - start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
            for item in results["data"]
        )
        assert all(results["data"][0]) >= 0


class TestMultipleRenewables:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_and_get_repeated(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        """Test that we can get many copies of the same dataset."""
        metadata = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": None,
                    "tilt": None,
                    "tracking": False,
                },
            )
        ).json()
        results = (
            await client.post(
                "/get-renewables-generation",
                json={
                    "dataset_id": [metadata["dataset_id"] for _ in range(4)],
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
            )
        ).json()

        assert all(
            len(results["timestamps"])
            == len(item)
            == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
            for item in results["data"]
        )
        assert all(all(item) >= 0 for item in results["data"])
        assert all(item == results["data"][0] for item in results["data"])

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_and_get_different(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        """Test that we can get many copies of the same dataset."""
        metadata_1 = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": 175,
                    "tilt": 35,
                    "tracking": False,
                },
            )
        ).json()

        metadata_2 = (
            await client.post(
                "/generate-renewables-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "azimuth": 190,
                    "tilt": 45,
                    "tracking": True,
                },
            )
        ).json()
        results = (
            await client.post(
                "/get-renewables-generation",
                json={
                    "dataset_id": [metadata_1["dataset_id"], metadata_2["dataset_id"]],
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
            )
        ).json()

        assert all(
            len(results["timestamps"])
            == len(item)
            == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
            for item in results["data"]
        )
        assert all(all(item) >= 0 for item in results["data"])
        assert all(any(item) > 0 for item in results["data"])
        assert not all(item == results["data"][0] for item in results["data"])


class TestRenewablesErrors:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_useful_error_messages(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        """Test that we can get many copies of the same dataset."""
        bad_uuid = uuid.uuid4()
        results = await client.post(
            "/get-renewables-generation",
            json={
                "dataset_id": str(bad_uuid),
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )

        assert results.status_code == 400
        assert "dataset_id" in results.json()["detail"]
        assert str(bad_uuid) in results.json()["detail"]


class TestWindRenewables:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_generate_renewables_wind(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        result = (
            await client.post(
                "/generate-wind-generation",
                json={
                    "site_id": "demo_london",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                    "height": 80,
                    "turbine": "Enercon E101 3000",
                },
            )
        ).json()
        assert "dataset_id" in result
        assert (
            datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=1)
            <= datetime.datetime.fromisoformat(result["created_at"])
            <= datetime.datetime.now(datetime.UTC)
        )
        assert result["parameters"]["height"] == 80
        assert result["parameters"]["turbine"] == "Enercon E101 3000"
        assert result["site_id"] == "demo_london"
