"""Endpoint testing for carbon intensity endpoints."""

# ruff: noqa: D101
import datetime
import itertools

import pydantic
import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.internal.utils.uuid import uuid7
from app.routers.carbon_intensity import fetch_carbon_intensity

from .conftest import get_internal_client_hack, get_pool_hack


@pytest.fixture
def demo_start_ts() -> datetime.datetime:
    """Provide a boring start datetime with good data around it."""
    return datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.UTC)


@pytest.fixture
def demo_end_ts() -> datetime.datetime:
    """Provide a boring end datetime with good data around it, more than 14 days after the start."""
    return datetime.datetime(year=2024, month=2, day=11, tzinfo=datetime.UTC)


@pytest.fixture
def demo_site_id() -> str:
    """Provide a site ID with a postcode in the database for regional data."""
    return "demo_london"


@pytest_asyncio.fixture
async def grid_co2_metadata(
    client: AsyncClient, demo_site_id: str, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
) -> pydantic.Json:
    """Generate a consistent set of carbon intensity data and add it to the DB."""
    # We don't use a fixture for the bundle because in some cases the start and end timestamps will differ
    # which we need to know at bundle creation time.
    bundle_id = str(uuid7())
    bundle_resp = await client.post(
        "/create-bundle",
        json={
            "bundle_id": bundle_id,
            "name": "Carbon Intensity Test",
            "site_id": "demo_london",
            "start_ts": demo_start_ts.isoformat(),
            "end_ts": demo_end_ts.isoformat(),
        },
    )
    assert bundle_resp.is_success

    result = await client.post(
        "/generate-grid-co2",
        json={
            "site_id": demo_site_id,
            "start_ts": demo_start_ts.isoformat(),
            "end_ts": demo_end_ts.isoformat(),
            "bundle_metadata": {
                "bundle_id": bundle_id,
                "dataset_id": str(uuid7()),
                "dataset_type": "CarbonIntensity",
                "dataset_subtype": None,
            },
        },
    )
    assert result.is_success, result.text
    return result.json()


@pytest.mark.slow
class TestCarbonIntensity:
    @pytest.mark.asyncio
    async def test_nonzero_seconds(self, client: AsyncClient, demo_site_id: str) -> None:
        """
        Test that we handle a case with nonzero seconds correctly.

        If there are two times too close to one another (same hour?), then the CarbonIntensity API complains.
        """
        result = await client.post(
            "/generate-grid-co2",
            json={"site_id": demo_site_id, "start_ts": "2022-12-31T00:00:00Z", "end_ts": "2023-01-01T00:00:59Z"},
        )
        assert result.status_code == 200, result.text

    @pytest.mark.asyncio
    async def test_nonzero_minutes(self, client: AsyncClient, demo_site_id: str) -> None:
        """
        Test that we handle a case with nonzero minutes correctly.

        If there are two times too close to one another (same hour?), then the CarbonIntensity API complains.
        """
        result = await client.post(
            "/generate-grid-co2",
            json={"site_id": demo_site_id, "start_ts": "2022-12-31T00:00:00Z", "end_ts": "2023-01-01T00:37:00Z"},
        )
        assert result.status_code == 200, result.text

    @pytest.mark.asyncio
    async def test_nonzero_hours(self, client: AsyncClient, demo_site_id: str) -> None:
        """
        Test that we handle a case with nonzero hours correctly.

        If there are two times too close to one another (same hour?), then the CarbonIntensity API complains.
        """
        result = await client.post(
            "/generate-grid-co2",
            json={"site_id": demo_site_id, "start_ts": "2022-12-31T00:00:00Z", "end_ts": "2023-01-01T13:00:00Z"},
        )
        assert result.status_code == 200, result.text

    @pytest.mark.asyncio
    async def test_generate(self, grid_co2_metadata: pydantic.Json, demo_site_id: str) -> None:
        """Test that the generation succeeds and returns some sensible metadata."""
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
        """Test that we can generate some data and retrieve it correctly, with sensible values."""
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
        assert all(item > 0 for item in grid_co2_result["data"])
        expected_entries = (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
        assert len(grid_co2_result["data"]) == expected_entries, "Not enough entries in set"
        assert len(grid_co2_result["timestamps"]) == expected_entries, "Not enough entries in timestamps"

    @pytest.mark.asyncio
    async def test_check_right_length(
        self,
        grid_co2_metadata: pydantic.Json,
        client: AsyncClient,
        demo_start_ts: datetime.datetime,
        demo_end_ts: datetime.datetime,
        demo_site_id: str,
    ) -> None:
        """Check that we get data of the correct length, with interpolation performed properly."""
        _ = grid_co2_metadata
        grid_co2_result = await client.post(
            "/list-latest-datasets",
            json={"site_id": demo_site_id, "start_ts": demo_start_ts.isoformat(), "end_ts": demo_end_ts.isoformat()},
        )
        assert grid_co2_result.status_code == 200, grid_co2_result.text
        grid_co2_entry = grid_co2_result.json()["CarbonIntensity"]

        assert datetime.datetime.fromisoformat(grid_co2_entry["start_ts"]) == demo_start_ts
        assert datetime.datetime.fromisoformat(grid_co2_entry["end_ts"]) == demo_end_ts
        assert (
            grid_co2_entry["num_entries"]
            == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
        )  # This will be off-by-one if we haven't interpolated right.


class TestCarbonIntensityChunking:
    """Test the chunking algorithm in the requests, which should split requests into 14 day chunks and over year boundaries."""

    @pytest.mark.asyncio
    async def test_check_right_length_at_end_of_year(
        self,
        client: AsyncClient,
        demo_site_id: str,
    ) -> None:
        """Test that we get the right number of entries if the last entry is in next year."""
        start_ts = datetime.datetime(year=2024, month=12, day=24, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2025, month=1, day=1, hour=0, minute=0, tzinfo=datetime.UTC)
        bundle_id = str(uuid7())
        bundle_resp = await client.post(
            "/create-bundle",
            json={
                "bundle_id": bundle_id,
                "name": "Carbon Intensity Test",
                "site_id": "demo_london",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert bundle_resp.is_success

        result = await client.post(
            "/generate-grid-co2",
            json={
                "site_id": demo_site_id,
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
                "bundle_metadata": {
                    "bundle_id": bundle_id,
                    "dataset_id": str(uuid7()),
                    "dataset_type": "CarbonIntensity",
                    "dataset_subtype": None,
                },
            },
        )

        assert result.status_code == 200

        grid_co2_result = (
            await client.post(
                "/list-latest-datasets",
                json={"site_id": demo_site_id, "start_ts": start_ts.isoformat(), "end_ts": end_ts.isoformat()},
            )
        ).json()

        grid_co2_entry = grid_co2_result["CarbonIntensity"]

        assert datetime.datetime.fromisoformat(grid_co2_entry["start_ts"]) == start_ts
        assert datetime.datetime.fromisoformat(grid_co2_entry["end_ts"]) == end_ts
        assert (
            grid_co2_entry["num_entries"]
            == (end_ts - start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
        )

    @pytest.mark.asyncio
    async def test_check_right_length_one_day_into_next_year(
        self,
        client: AsyncClient,
        demo_site_id: str,
    ) -> None:
        """Test that we get the right number of entries if the last entry is a day into the next year."""
        start_ts = datetime.datetime(year=2024, month=12, day=24, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2025, month=1, day=2, hour=0, minute=0, tzinfo=datetime.UTC)

        bundle_id = str(uuid7())
        bundle_resp = await client.post(
            "/create-bundle",
            json={
                "bundle_id": bundle_id,
                "name": "Carbon Intensity Test",
                "site_id": "demo_london",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert bundle_resp.is_success

        result = await client.post(
            "/generate-grid-co2",
            json={
                "site_id": demo_site_id,
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
                "bundle_metadata": {
                    "bundle_id": bundle_id,
                    "dataset_id": str(uuid7()),
                    "dataset_type": "CarbonIntensity",
                    "dataset_subtype": None,
                },
            },
        )

        assert result.status_code == 200
        grid_co2_result = (
            await client.post(
                "/list-latest-datasets",
                json={"site_id": demo_site_id, "start_ts": start_ts.isoformat(), "end_ts": end_ts.isoformat()},
            )
        ).json()

        grid_co2_entry = grid_co2_result["CarbonIntensity"]
        assert datetime.datetime.fromisoformat(grid_co2_entry["start_ts"]) == start_ts
        assert datetime.datetime.fromisoformat(grid_co2_entry["end_ts"]) == end_ts
        assert (
            grid_co2_entry["num_entries"]
            == (end_ts - start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
        )


class TestFetchCarbonIntensity:
    """Tests for the specific fetching function."""

    @pytest.mark.asyncio
    async def test_bad_dates(self, client: AsyncClient) -> None:
        """Test that we fill in missing data between 2023-10-20T21:30:00Z and 2023-10-22T15:00:00Z."""
        bad_start_ts = datetime.datetime(year=2023, month=10, day=20, hour=0, minute=0, tzinfo=datetime.UTC)
        bad_end_ts = datetime.datetime(year=2023, month=10, day=23, hour=0, minute=0, tzinfo=datetime.UTC)
        res = await fetch_carbon_intensity(
            http_client=get_internal_client_hack(client),
            postcode="SW1A",
            start_ts=bad_start_ts,
            end_ts=bad_end_ts,
            pool=await get_pool_hack(client),
        )
        for first, second in itertools.pairwise(res):
            assert first["end_ts"] == second["start_ts"]
        assert len(res) == 3 * 48, "Not enough results in response"

    @pytest.mark.asyncio
    async def test_not_use_regional(self, client: AsyncClient) -> None:
        """Test that we fill in missing data between 2023-10-20T21:30:00Z and 2023-10-22T15:00:00Z without regional data."""
        bad_start_ts = datetime.datetime(year=2024, month=10, day=20, hour=0, minute=0, tzinfo=datetime.UTC)
        bad_end_ts = datetime.datetime(year=2024, month=10, day=23, hour=0, minute=0, tzinfo=datetime.UTC)

        res = await fetch_carbon_intensity(
            http_client=get_internal_client_hack(client),
            postcode=None,
            start_ts=bad_start_ts,
            end_ts=bad_end_ts,
            pool=await get_pool_hack(client),
        )
        for first, second in itertools.pairwise(res):
            assert first["end_ts"] == second["start_ts"]

    @pytest.mark.asyncio
    async def test_use_regional(self, client: AsyncClient) -> None:
        """Test that we get good regional data for a period without holes."""
        start_ts = datetime.datetime(year=2024, month=10, day=20, hour=0, minute=0, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2024, month=10, day=23, hour=0, minute=0, tzinfo=datetime.UTC)

        res = await fetch_carbon_intensity(
            http_client=get_internal_client_hack(client),
            postcode="SW1A 0AA",
            start_ts=start_ts,
            end_ts=end_ts,
            pool=await get_pool_hack(client),
        )
        for first, second in itertools.pairwise(res):
            assert first["end_ts"] == second["start_ts"]

    @pytest.mark.asyncio
    async def test_caching_faster(self, client: AsyncClient) -> None:
        """Test that making a second request is faster."""
        start_ts = datetime.datetime(year=2024, month=10, day=20, hour=0, minute=0, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2024, month=10, day=23, hour=0, minute=0, tzinfo=datetime.UTC)

        start_entries = await (await get_pool_hack(client)).fetchval("""SELECT COUNT(*) FROM carbon_intensity.grid_co2_cache""")
        t1 = datetime.datetime.now(datetime.UTC)
        res_1 = await fetch_carbon_intensity(
            http_client=get_internal_client_hack(client),
            postcode="SW1A 0AA",
            start_ts=start_ts,
            end_ts=end_ts,
            pool=await get_pool_hack(client),
        )
        t2 = datetime.datetime.now(datetime.UTC)
        res_2 = await fetch_carbon_intensity(
            http_client=get_internal_client_hack(client),
            postcode="SW1A 0AA",
            start_ts=start_ts,
            end_ts=end_ts,
            pool=await get_pool_hack(client),
        )
        t3 = datetime.datetime.now(datetime.UTC)

        end_entries = await (await get_pool_hack(client)).fetchval("""SELECT COUNT(*) FROM carbon_intensity.grid_co2_cache""")
        assert start_entries == 0
        assert end_entries >= 48 * 3, "Wrong number of cache entries"
        assert len(res_1) == len(res_2)
        # Add a bit of wiggle room here to prevent this being a flaky test!
        assert (t2 - t1) + datetime.timedelta(seconds=10) > t3 - t2, "Second cached call was slower than first uncached call"

    @pytest.mark.asyncio
    async def test_caching_overlaps(self, client: AsyncClient) -> None:
        """Test that getting cached overlaps is fine."""
        start_1 = datetime.datetime(year=2024, month=10, day=20, hour=0, minute=0, tzinfo=datetime.UTC)
        end_1 = datetime.datetime(year=2024, month=10, day=30, hour=0, minute=0, tzinfo=datetime.UTC)

        start_2 = datetime.datetime(year=2024, month=10, day=25, hour=0, minute=0, tzinfo=datetime.UTC)
        end_2 = datetime.datetime(year=2024, month=11, day=5, hour=0, minute=0, tzinfo=datetime.UTC)
        await fetch_carbon_intensity(
            http_client=get_internal_client_hack(client),
            postcode="SW1A 0AA",
            start_ts=start_1,
            end_ts=end_1,
            pool=await get_pool_hack(client),
        )
        res_2 = await fetch_carbon_intensity(
            http_client=get_internal_client_hack(client),
            postcode="SW1A 0AA",
            start_ts=start_2,
            end_ts=end_2,
            pool=await get_pool_hack(client),
        )
        for first, second in itertools.pairwise(res_2):
            assert first["end_ts"] == second["start_ts"]
