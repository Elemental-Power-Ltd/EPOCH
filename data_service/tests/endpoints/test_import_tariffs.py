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
            len(tariff_result) == (demo_end_ts - demo_start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
        )
        assert all(not pd.isna(item["Tariff"]) for item in tariff_result)

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
        metadata = (
            await client.post(
                "/generate-import-tariffs",
                json={
                    "site_id": "demo_london",
                    "tariff_name": tariff_name,
                    "start_ts": start_ts.isoformat(),
                    "end_ts": end_ts.isoformat(),
                },
            )
        ).json()
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
        assert len(tariff_result) == (end_ts - start_ts).total_seconds() / datetime.timedelta(minutes=30).total_seconds()
        assert all(not pd.isna(item["Tariff"]) for item in tariff_result)
