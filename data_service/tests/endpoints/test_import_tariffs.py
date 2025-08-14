"""Tests for octopus tariff endpoints."""

# ruff: noqa: D101, D102, D103
import datetime

import httpx
import pandas as pd
import pytest

from app.dependencies import get_db_pool, get_http_client
from app.internal.import_tariffs.re24 import get_re24_approximate_ppa
from app.models.core import SiteIDWithTime


@pytest.fixture
def demo_start_ts() -> datetime.datetime:
    return datetime.datetime(year=2024, month=1, day=1, hour=0, minute=0, second=0, tzinfo=datetime.UTC)


@pytest.fixture
def demo_end_ts() -> datetime.datetime:
    return datetime.datetime(year=2024, month=6, day=30, hour=0, minute=0, second=0, tzinfo=datetime.UTC)


class TestSyntheticTariffs:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_agile(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        metadata = await client.post(
            "/generate-import-tariffs",
            json={
                "site_id": "demo_london",
                "tariff_name": "agile",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        assert metadata.status_code == 200, metadata.text
        result = await client.post("/get-import-tariffs", json={"dataset_id": metadata.json()["dataset_id"]})
        assert result.status_code == 200, result.text

        timestamps = result.json()["timestamps"]
        first_ts = datetime.datetime.fromisoformat(timestamps[0])
        assert first_ts.hour == 0, "First entry isn't 00:00"
        assert first_ts.minute == 0, "First entry isn't 00:00"
        assert first_ts == demo_start_ts
        last_ts = datetime.datetime.fromisoformat(timestamps[-1])
        assert last_ts.hour == 23, "Last entry isn't 23:30"
        assert last_ts.minute == 30, "Last entry isn't 23:30"
        assert last_ts == (demo_end_ts - datetime.timedelta(minutes=30))
        assert (
            len(timestamps) == len(item) == int((demo_end_ts - demo_start_ts) / datetime.timedelta(minutes=30))
            for item in result.json()["data"]
        )

        assert all(len(set(data)) > 10 for data in result.json()["data"])

    @pytest.mark.asyncio
    async def test_generate_fixed(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        metadata = await client.post(
            "/generate-import-tariffs",
            json={
                "site_id": "demo_london",
                "tariff_name": "fixed",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        assert metadata.status_code == 200, metadata.text
        result = await client.post("/get-import-tariffs", json={"dataset_id": metadata.json()["dataset_id"]})
        assert result.status_code == 200, result.text

        timestamps = result.json()["timestamps"]
        first_ts = datetime.datetime.fromisoformat(timestamps[0])
        assert first_ts.hour == 0, "First entry isn't 00:00"
        assert first_ts.minute == 0, "First entry isn't 00:00"
        assert first_ts == demo_start_ts
        last_ts = datetime.datetime.fromisoformat(timestamps[-1])
        assert last_ts.hour == 23, "Last entry isn't 23:30"
        assert last_ts.minute == 30, "Last entry isn't 23:30"
        assert last_ts == (demo_end_ts - datetime.timedelta(minutes=30))
        assert (
            len(timestamps) == len(item) == int((demo_end_ts - demo_start_ts) / datetime.timedelta(minutes=30))
            for item in result.json()["data"]
        )

        assert all(len(set(data)) == 1 for data in result.json()["data"])

    @pytest.mark.asyncio
    async def test_generate_overnight(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        metadata = await client.post(
            "/generate-import-tariffs",
            json={
                "site_id": "demo_london",
                "tariff_name": "overnight",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        assert metadata.status_code == 200, metadata.text
        result = await client.post("/get-import-tariffs", json={"dataset_id": metadata.json()["dataset_id"]})
        assert result.status_code == 200, result.text

        timestamps = result.json()["timestamps"]
        first_ts = datetime.datetime.fromisoformat(timestamps[0])
        assert first_ts.hour == 0, "First entry isn't 00:00"
        assert first_ts.minute == 0, "First entry isn't 00:00"
        assert first_ts == demo_start_ts
        last_ts = datetime.datetime.fromisoformat(timestamps[-1])
        assert last_ts.hour == 23, "Last entry isn't 23:30"
        assert last_ts.minute == 30, "Last entry isn't 23:30"
        assert last_ts == (demo_end_ts - datetime.timedelta(minutes=30))
        assert (
            len(timestamps) == len(item) == int((demo_end_ts - demo_start_ts) / datetime.timedelta(minutes=30))
            for item in result.json()["data"]
        )

        assert all(len(set(data)) == 2 for data in result.json()["data"])

    @pytest.mark.asyncio
    async def test_generate_peak(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        metadata = await client.post(
            "/generate-import-tariffs",
            json={
                "site_id": "demo_london",
                "tariff_name": "peak",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        assert metadata.status_code == 200, metadata.text
        result = await client.post("/get-import-tariffs", json={"dataset_id": metadata.json()["dataset_id"]})
        assert result.status_code == 200, result.text

        timestamps = result.json()["timestamps"]
        first_ts = datetime.datetime.fromisoformat(timestamps[0])
        assert first_ts.hour == 0, "First entry isn't 00:00"
        assert first_ts.minute == 0, "First entry isn't 00:00"
        assert first_ts == demo_start_ts
        last_ts = datetime.datetime.fromisoformat(timestamps[-1])
        assert last_ts.hour == 23, "Last entry isn't 23:30"
        assert last_ts.minute == 30, "Last entry isn't 23:30"
        assert last_ts == (demo_end_ts - datetime.timedelta(minutes=30))
        assert (
            len(timestamps) == len(item) == int((demo_end_ts - demo_start_ts) / datetime.timedelta(minutes=30))
            for item in result.json()["data"]
        )

        assert all(len(set(data)) == 3 for data in result.json()["data"])


class TestImportTariffs:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_import_tariff(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        response = await client.post(
            "/generate-import-tariffs",
            json={
                "site_id": "demo_london",
                "tariff_name": "AGILE-24-04-03",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
            timeout=10,
        )
        assert response.status_code == 200, response.text
        metadata = response.json()
        assert metadata["site_id"] == "demo_london"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_and_get_import_tariff(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        response = await client.post(
            "/generate-import-tariffs",
            json={
                "site_id": "demo_london",
                "tariff_name": "AGILE-24-04-03",
                "start_ts": demo_start_ts.isoformat(),
                "end_ts": demo_end_ts.isoformat(),
            },
        )
        assert response.status_code == 200, response.text
        metadata = response.json()
        tariff_result = (
            await client.post(
                "/get-import-tariffs",
                json={
                    "dataset_id": metadata["dataset_id"],
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
                timeout=10,
            )
        ).json()
        expected_len = int((demo_end_ts - demo_start_ts) / pd.Timedelta(minutes=30))
        assert len(tariff_result["timestamps"]) == expected_len
        assert all(len(tariff_result["timestamps"]) == len(data) for data in tariff_result["data"])
        assert all(not pd.isna(data).any() for data in tariff_result["data"])

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_and_get_agile(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        start_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2020, month=2, day=1, tzinfo=datetime.UTC)
        response = await client.post(
            "/generate-import-tariffs",
            json={
                "site_id": "demo_london",
                "tariff_name": "agile",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
            timeout=10,
        )
        assert response.status_code == 200, response.text
        metadata = response.json()
        tariff_result = (
            await client.post(
                "/get-import-tariffs",
                json={
                    "dataset_id": metadata["dataset_id"],
                    "start_ts": start_ts.isoformat(),
                    "end_ts": end_ts.isoformat(),
                },
            )
        ).json()
        expected_len = (end_ts - start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
        assert len(tariff_result["timestamps"]) == expected_len
        assert all(len(tariff_result["timestamps"]) == len(data) for data in tariff_result["data"])
        assert all(not pd.isna(data).any() for data in tariff_result["data"])
        for data in tariff_result["data"]:
            assert len(set(data)) >= 23

    @pytest.mark.asyncio
    async def test_generate_and_get_peak(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        start_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2020, month=2, day=1, tzinfo=datetime.UTC)
        response = await client.post(
            "/generate-import-tariffs",
            json={
                "site_id": "demo_london",
                "tariff_name": "peak",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert response.status_code == 200, response.text
        metadata = response.json()
        tariff_result = (
            await client.post(
                "/get-import-tariffs",
                json={
                    "dataset_id": metadata["dataset_id"],
                    "start_ts": start_ts.isoformat(),
                    "end_ts": end_ts.isoformat(),
                },
            )
        ).json()

        expected_len = (end_ts - start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
        assert len(tariff_result["timestamps"]) == expected_len
        assert all(len(tariff_result["timestamps"]) == len(data) for data in tariff_result["data"])
        assert all(not pd.isna(data).any() for data in tariff_result["data"])
        assert all(len(set(data)) == 3 for data in tariff_result["data"])

        for data in tariff_result["data"]:
            lo, mid, hi = sorted(set(data))
            assert hi == pytest.approx(mid * 1.5)
            assert lo == pytest.approx(mid * 0.49)

    @pytest.mark.asyncio
    async def test_generate_and_get_ppa(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can generate and get a PPA synthetic tariff."""
        start_ts = datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2022, month=2, day=1, tzinfo=datetime.UTC)
        response = await client.post(
            "/generate-import-tariffs",
            json={
                "site_id": "demo_london",
                "tariff_name": "power_purchase_agreement",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert response.status_code == 200, response.text
        metadata = response.json()
        tariff_result = (
            await client.post(
                "/get-import-tariffs",
                json={
                    "dataset_id": metadata["dataset_id"],
                    "start_ts": start_ts.isoformat(),
                    "end_ts": end_ts.isoformat(),
                },
            )
        ).json()

        expected_len = (end_ts - start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
        assert len(tariff_result["timestamps"]) == expected_len
        assert all(len(tariff_result["timestamps"]) == len(data) for data in tariff_result["data"])
        assert all(not pd.isna(data).any() for data in tariff_result["data"])
        assert all(len(set(data)) == 3 for data in tariff_result["data"])

    @pytest.mark.asyncio
    async def test_list_import_tariffs(self, client: httpx.AsyncClient) -> None:
        start_ts = datetime.datetime(year=2019, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
        tariff_result = await client.post(
            "/list-import-tariffs",
            json={
                "site_id": "demo_london",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert tariff_result.status_code == 200, tariff_result.text
        assert len(tariff_result.json()) > 2
        selected_result = await client.post(
            "/select-arbitrary-tariff",
            json={
                "site_id": "demo_london",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert selected_result.status_code == 200, selected_result.text
        assert len(selected_result.json()) > 2

    @pytest.mark.asyncio
    async def test_generate_past_import_tariff(self, client: httpx.AsyncClient) -> None:
        start_ts = datetime.datetime(year=2019, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
        tariff_name = (
            await client.post(
                "/select-arbitrary-tariff",
                json={
                    "site_id": "demo_london",
                    "start_ts": start_ts.isoformat(),
                    "end_ts": end_ts.isoformat(),
                },
            )
        ).json()
        metadata = await client.post(
            "/generate-import-tariffs",
            json={
                "site_id": "demo_london",
                "tariff_name": tariff_name,
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert metadata.status_code == 200, metadata.text
        tariff_result = (
            await client.post(
                "/get-import-tariffs",
                json={
                    "dataset_id": metadata.json()["dataset_id"],
                    "start_ts": start_ts.isoformat(),
                    "end_ts": end_ts.isoformat(),
                },
            )
        ).json()

        expected_len = (end_ts - start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
        assert len(tariff_result["timestamps"]) == expected_len
        assert all(len(tariff_result["timestamps"]) == len(data) for data in tariff_result["data"])
        assert all(not pd.isna(data).any() for data in tariff_result["data"])

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_get_one_of_each(self, client: httpx.AsyncClient) -> None:
        start_ts = datetime.datetime(year=2023, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.UTC)
        tariff_uuids = {}
        for tariff_type in ["fixed", "overnight", "peak", "agile"]:
            response = await client.post(
                "/generate-import-tariffs",
                json={
                    "site_id": "demo_london",
                    "tariff_name": tariff_type,
                    "start_ts": start_ts.isoformat(),
                    "end_ts": end_ts.isoformat(),
                },
            )
            assert response.status_code == 200, response.text
            metadata = response.json()
            tariff_uuids[tariff_type] = metadata["dataset_id"]

        assert len(tariff_uuids) == 4
        tariff_response = await client.post(
            "/get-import-tariffs",
            json={
                "dataset_id": list(tariff_uuids.values()),
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert tariff_response.status_code == 200
        tariff_result = tariff_response.json()
        expected_len = (end_ts - start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
        assert len(tariff_result["timestamps"]) == expected_len
        assert all(len(tariff_result["timestamps"]) == len(data) for data in tariff_result["data"])
        assert all(not pd.isna(data).any() for data in tariff_result["data"])


class TestRE24PPA:
    @pytest.mark.asyncio
    async def test_units_correct(self, client: httpx.AsyncClient) -> None:
        """Test that we get the units correct in p / kWh."""
        pool = await client._transport.app.dependency_overrides[get_db_pool]().__anext__()  # type: ignore
        inner_client = client._transport.app.dependency_overrides[get_http_client]()  # type: ignore
        result = await get_re24_approximate_ppa(
            params=SiteIDWithTime(
                site_id="demo_london",
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=2, day=1, tzinfo=datetime.UTC),
            ),
            pool=pool,
            http_client=inner_client,
            grid_tariff=100,
        )
        assert all(result.cost <= 100.0)
        assert all(result.cost > 1.0)

    @pytest.mark.asyncio
    async def test_get_three(self, client: httpx.AsyncClient) -> None:
        """Test that we get three tiers of prices."""
        pool = await client._transport.app.dependency_overrides[get_db_pool]().__anext__()  # type: ignore
        inner_client = client._transport.app.dependency_overrides[get_http_client]()  # type: ignore
        result = await get_re24_approximate_ppa(
            params=SiteIDWithTime(
                site_id="demo_london",
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2022, month=2, day=1, tzinfo=datetime.UTC),
            ),
            pool=pool,
            http_client=inner_client,
            grid_tariff=100,
        )
        assert len(result.cost.unique()) == 3

    @pytest.mark.asyncio
    async def test_dataframe_grid(self, client: httpx.AsyncClient) -> None:
        """Test that we can handle a grid dataframe tariff."""
        pool = await client._transport.app.dependency_overrides[get_db_pool]().__anext__()  # type: ignore
        inner_client = client._transport.app.dependency_overrides[get_http_client]()  # type: ignore
        start_ts = datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2022, month=2, day=1, tzinfo=datetime.UTC)
        grid_tariff = pd.DataFrame(index=pd.date_range(start_ts, end_ts, freq=pd.Timedelta(minutes=30)), data={"cost": [100.0]})
        result = await get_re24_approximate_ppa(
            params=SiteIDWithTime(site_id="demo_london", start_ts=start_ts, end_ts=end_ts),
            pool=pool,
            http_client=inner_client,
            grid_tariff=grid_tariff,
        )
        assert len(result.cost.unique()) == 3
        assert not result["cost"].isna().any()

    @pytest.mark.asyncio
    async def test_dataframe_varying_grid(self, client: httpx.AsyncClient) -> None:
        """Test that we can handle a varying grid dataframe tariff."""
        pool = await client._transport.app.dependency_overrides[get_db_pool]().__anext__()  # type: ignore
        inner_client = client._transport.app.dependency_overrides[get_http_client]()  # type: ignore
        start_ts = datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2022, month=2, day=1, tzinfo=datetime.UTC)
        grid_tariff = pd.DataFrame(index=pd.date_range(start_ts, end_ts, freq=pd.Timedelta(minutes=30)), data={"cost": [100.0]})
        grid_tariff.loc[::2, "cost"] = 1.0
        result = await get_re24_approximate_ppa(
            params=SiteIDWithTime(site_id="demo_london", start_ts=start_ts, end_ts=end_ts),
            pool=pool,
            http_client=inner_client,
            grid_tariff=grid_tariff,
        )
        assert len(result.cost.unique()) == 4
        assert not result["cost"].isna().any()
