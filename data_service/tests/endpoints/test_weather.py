"""Tests for weather endpoints."""

# ruff: noqa: D101, D102, D103
import datetime

import httpx
import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def demo_start_ts() -> datetime.datetime:
    return datetime.datetime(year=2024, month=1, day=1, hour=0, minute=0, second=0, tzinfo=datetime.UTC)


@pytest_asyncio.fixture
async def demo_end_ts() -> datetime.datetime:
    return datetime.datetime(year=2024, month=2, day=8, hour=0, minute=0, second=0, tzinfo=datetime.UTC)


class TestGetVisualCrossing:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_cardiff(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        result = await client.post(
            "/get-visual-crossing",
            json={"location": "Cardiff", "start_ts": demo_start_ts.isoformat(), "end_ts": demo_end_ts.isoformat()},
        )
        assert len(result.json()) == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(hours=1).total_seconds()
        for key in ["temp", "timestamp", "humidity", "windspeed"]:
            assert key in result.json()[0]

        assert max(
            datetime.datetime.fromisoformat(item["timestamp"]) for item in result.json()
        ) == demo_end_ts - datetime.timedelta(hours=1)
        assert min(datetime.datetime.fromisoformat(item["timestamp"]) for item in result.json()) == demo_start_ts


class TestGetWeather:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_all_from_vc(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        """Test that we've got all the weather we expect from VisualCrossing."""
        result = await client.post(
            "/get-weather",
            json={"location": "Cardiff", "start_ts": demo_start_ts.isoformat(), "end_ts": demo_end_ts.isoformat()},
        )

        vc_result = await client.post(
            "/get-visual-crossing",
            json={"location": "Cardiff", "start_ts": demo_start_ts.isoformat(), "end_ts": demo_end_ts.isoformat()},
        )

        db_timestamps = {item["timestamp"] for item in result.json()}
        vc_timestamps = {item["timestamp"] for item in vc_result.json()}
        assert max(
            datetime.datetime.fromisoformat(item["timestamp"]) for item in result.json()
        ) == demo_end_ts - datetime.timedelta(hours=1)
        assert min(datetime.datetime.fromisoformat(item["timestamp"]) for item in result.json()) == demo_start_ts

        assert db_timestamps == vc_timestamps

        assert len(result.json()) == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(hours=1).total_seconds()
        for key in ["temp", "timestamp", "humidity", "windspeed"]:
            assert key in result.json()[0]

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_idempotent(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        """Test that we can request the same weather twice in a row."""
        result = await client.post(
            "/get-weather",
            json={"location": "Cardiff", "start_ts": demo_start_ts.isoformat(), "end_ts": demo_end_ts.isoformat()},
        )

        again_result = await client.post(
            "/get-weather",
            json={"location": "Cardiff", "start_ts": demo_start_ts.isoformat(), "end_ts": demo_end_ts.isoformat()},
        )

        assert result.json() == again_result.json()

    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_can_get_missing(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        """Test that we can request an extra period and don't squash any original data."""
        result = await client.post(
            "/get-weather",
            json={"location": "Cardiff", "start_ts": demo_start_ts.isoformat(), "end_ts": demo_end_ts.isoformat()},
        )

        larger_result = await client.post(
            "/get-weather",
            json={
                "location": "Cardiff",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": (demo_end_ts + datetime.timedelta(days=7)).isoformat(),
            },
        )

        assert len(larger_result.json()) == (len(result.json()) + 7 * 24)

        result_again = await client.post(
            "/get-weather",
            json={"location": "Cardiff", "start_ts": demo_start_ts.isoformat(), "end_ts": demo_end_ts.isoformat()},
        )
        # and that we didn't screw up the original data
        assert result.json() == result_again.json()
