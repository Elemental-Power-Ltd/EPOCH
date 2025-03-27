"""Tests for import tariff internal functions."""

# ruff: noqa: D101, D102
import datetime

import httpx
import numpy as np
import pandas as pd
import pytest

import app.internal.import_tariffs as it
from app.models.import_tariffs import GSPEnum
from tests.endpoints.conftest import MockedHttpClient


class TestCombineDataFrames:
    def test_combine_simple(self) -> None:
        idx_1 = pd.date_range(
            datetime.datetime(year=2024, month=9, day=25, tzinfo=datetime.UTC),
            datetime.datetime(year=2024, month=10, day=2, tzinfo=datetime.UTC),
            freq=pd.Timedelta(minutes=30),
        )
        idx_2 = pd.date_range(
            datetime.datetime(year=2024, month=10, day=1, tzinfo=datetime.UTC),
            datetime.datetime(year=2024, month=10, day=10, tzinfo=datetime.UTC),
            freq=pd.Timedelta(minutes=30),
        )

        df_1 = pd.DataFrame(index=idx_1, data={"cost": [1 for _ in idx_1]})
        df_2 = pd.DataFrame(index=idx_2, data={"cost": [2 for _ in idx_2]})

        res = it.combine_tariffs([df_1, df_2])
        assert np.all(np.logical_or(res["cost"] == 1, res["cost"] == 2))
        mask = res.index > max(idx_1)
        assert np.all(res.loc[mask, "cost"] == 2)


class TestTariffToNewDates:
    def test_new_dates_yearly(self) -> None:
        old_idx = pd.date_range(
            datetime.datetime(year=2023, month=9, day=1, tzinfo=datetime.UTC),
            datetime.datetime(year=2023, month=10, day=1, tzinfo=datetime.UTC),
            freq=pd.Timedelta(minutes=30),
        )
        old_df = pd.DataFrame(index=old_idx, data={"cost": [1.0 for _ in old_idx]})
        new_idx = pd.date_range(
            datetime.datetime(year=2024, month=9, day=1, tzinfo=datetime.UTC),
            datetime.datetime(year=2024, month=10, day=1, tzinfo=datetime.UTC),
            freq=pd.Timedelta(minutes=30),
        )
        new_costs = it.tariff_utils.tariff_to_new_timestamps(old_df, new_idx)

        assert np.all(it.tariff_utils.tariff_to_new_timestamps(old_df, new_idx) == 1.0)
        assert np.all(new_costs.index == new_idx)
        assert np.all(new_costs.index != old_idx)


class TestGetFixedRates:
    @pytest.mark.asyncio
    async def test_loyalty_tariff(self) -> None:
        """Test that we get good day rates for a known loyalty tariff."""
        async with MockedHttpClient() as client:
            result = await it.get_fixed_rates("EP-LOYAL-FIX-12M-23-09-14", region_code=GSPEnum.C, client=client)
        assert pytest.approx(27.0745) == result

    @pytest.mark.asyncio
    async def test_bad_tariff(self) -> None:
        """Test that we raise the correct error for a bad tariff.."""
        with pytest.raises(ValueError, match="NOT_A_REAL_TARIFF"):
            async with MockedHttpClient() as client:
                _ = await it.get_fixed_rates("NOT_A_REAL_TARIFF", region_code=GSPEnum.C, client=client)

    @pytest.mark.asyncio
    async def test_agile_tariff(self) -> None:
        """Test that we don't try to get single costs for agile tariffs."""
        with pytest.raises(ValueError, match=r"use `get_octopus_tariff` for agile or varying tariffs."):
            async with MockedHttpClient() as client:
                _ = await it.get_fixed_rates("AGILE-FLEX-22-11-25", region_code=GSPEnum.C, client=client)


class TestGetDayNightRates:
    @pytest.mark.asyncio
    async def test_loyalty_tariff(self) -> None:
        """Test that we get good day rates for a known loyalty tariff."""
        async with MockedHttpClient() as client:
            night, day = await it.get_day_and_night_rates("EP-LOYAL-FIX-12M-23-09-14", region_code=GSPEnum.C, client=client)
        assert pytest.approx(14.4314) == night
        assert pytest.approx(34.1549) == day

    @pytest.mark.asyncio
    async def test_bad_tariff(self) -> None:
        """Test that we raise the correct error for a bad tariff.."""
        with pytest.raises(ValueError, match="NOT_A_REAL_TARIFF"):
            async with MockedHttpClient() as client:
                _ = await it.get_day_and_night_rates("NOT_A_REAL_TARIFF", region_code=GSPEnum.C, client=client)

    @pytest.mark.asyncio
    async def test_agile_tariff(self) -> None:
        """Test that we can't get day/night costs for agile tariffs."""
        with pytest.raises(ValueError, match="AGILE-FLEX-22-11-25"):
            async with MockedHttpClient() as client:
                _ = await it.get_day_and_night_rates("AGILE-FLEX-22-11-25", region_code=GSPEnum.C, client=client)


class TestSyntheticTariffs:
    def test_create_fixed(self) -> None:
        fixed_cost = 26.0
        dates = pd.date_range(
            start=datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.UTC),
            end=datetime.datetime(year=2025, month=1, day=1, tzinfo=datetime.UTC),
            freq=pd.Timedelta(minutes=30),
        )
        df = it.create_fixed_tariff(timestamps=dates, fixed_cost=fixed_cost)
        assert all(x == y for x, y in zip(dates, df.index, strict=True))
        assert all(df["cost"] == fixed_cost)

    def test_create_day_and_night(self) -> None:
        fixed_cost = 26.0
        night_cost = 10.0
        dates = pd.date_range(
            start=datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.UTC),
            end=datetime.datetime(year=2025, month=1, day=1, tzinfo=datetime.UTC),
            freq=pd.Timedelta(minutes=30),
        )
        df = it.create_day_and_night_tariff(timestamps=dates, day_cost=fixed_cost, night_cost=night_cost)
        assert all(x == y for x, y in zip(dates, df.index, strict=True))
        assert np.all(np.logical_or(df["cost"] == fixed_cost, df["cost"] == night_cost))

    def test_create_peaky(self) -> None:
        fixed_cost = 26.0
        night_cost = 10.0
        peak_premium = 12.0
        dates = pd.date_range(
            start=datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.UTC),
            end=datetime.datetime(year=2025, month=1, day=1, tzinfo=datetime.UTC),
            freq=pd.Timedelta(minutes=30),
        )
        df = it.create_peak_tariff(timestamps=dates, day_cost=fixed_cost, night_cost=night_cost, peak_cost=peak_premium)
        assert all(x == y for x, y in zip(dates, df.index, strict=True))
        assert np.all(
            np.logical_or.reduce([df["cost"] == fixed_cost, df["cost"] == night_cost, df["cost"] == fixed_cost + peak_premium])
        )


class TestTariffUtils:
    def test_region_code_is_in(self) -> None:
        """Test that we get a region code that exists in a dict."""
        code = GSPEnum.C
        example_dict = {"_C": None, "_D": None, "_E": None}
        result = it.region_or_first_available(code, example_dict.keys())
        assert result == code.value

    def test_region_code_is_not_in(self) -> None:
        """Test that we get a region code that isn't in the dict."""
        code = GSPEnum.F
        example_dict = {"_C": None, "_D": None, "_E": None}
        result = it.region_or_first_available(code, example_dict.keys())
        assert result == "_C"

    def test_region_code_in_list(self) -> None:
        """Test that we get a region code that is in a list."""
        code = GSPEnum.F
        example_list = ["_C", "_D", "_E", "_F"]
        result = it.region_or_first_available(code, example_list)
        assert result == code.value


class TestGetWholesale:
    @pytest.mark.asyncio
    async def test_works_with_dates(self) -> None:
        async with httpx.AsyncClient() as client:
            df = await it.get_wholesale_costs(
                datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.UTC),
                datetime.datetime(year=2024, month=2, day=1, tzinfo=datetime.UTC),
                client=client,
            )
        assert np.all(df["cost"] != 0.0)
        assert len(df) >= 31 * 2 * 24
