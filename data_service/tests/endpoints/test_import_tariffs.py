"""Tests for octopus tariff endpoints."""

# ruff: noqa: D101, D102, D103
import datetime

import httpx
import pandas as pd
import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def demo_start_ts() -> datetime.datetime:
    return datetime.datetime(year=2024, month=1, day=1, hour=0, minute=0, second=0, tzinfo=datetime.UTC)


@pytest_asyncio.fixture
async def demo_end_ts() -> datetime.datetime:
    return datetime.datetime(year=2024, month=6, day=30, hour=0, minute=0, second=0, tzinfo=datetime.UTC)


class TestImportTariffs:
    @pytest.mark.asyncio
    async def test_generate_import_tariff(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        metadata = (
            await client.post(
                "/generate-import-tariffs",
                json={
                    "site_id": "demo_london",
                    "tariff_name": "AGILE-24-04-03",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
            )
        ).json()
        print(metadata)
        assert metadata["site_id"] == "demo_london"

    @pytest.mark.asyncio
    async def test_generate_and_get_import_tariff(
        self, client: httpx.AsyncClient, demo_start_ts: datetime.datetime, demo_end_ts: datetime.datetime
    ) -> None:
        metadata = (
            await client.post(
                "/generate-import-tariffs",
                json={
                    "site_id": "demo_london",
                    "tariff_name": "AGILE-24-04-03",
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
            )
        ).json()
        tariff_result = (
            await client.post(
                "/get-import-tariffs",
                json={
                    "dataset_id": metadata["dataset_id"],
                    "start_ts": demo_start_ts.isoformat(),
                    "end_ts": demo_end_ts.isoformat(),
                },
            )
        ).json()
        assert (
            len(tariff_result) == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(minutes=60).total_seconds()
        )
        assert all(not pd.isna(item["Tariff"]) for item in tariff_result)
