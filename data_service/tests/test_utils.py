"""
Tests for other, nonspecific utility functions.

Ideally put these in their own relevant python files!
"""

# ruff: noqa: D101, D102
import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from app.internal.utils import check_latitude_longitude, chunk_time_period, split_into_sessions
from app.internal.utils.bank_holidays import UKCountryEnum, get_bank_holidays
from app.internal.utils.database_utils import get_migration_files


def test_get_migration_files() -> None:
    """Check that we get a single migration file correctly."""
    assert get_migration_files(Path("./migrations"), end=3) == [
        Path("./migrations/000001_initial_schemas.up.sql").absolute(),
        Path("./migrations/000002_change_objectives.up.sql").absolute(),
    ]


class TestChunkTimePeriod:
    def test_single_year_boundry(self) -> None:
        """Test that we chunk a time period correctly over a year, if necessary."""
        start_ts = datetime.datetime(year=2024, month=12, day=30, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2025, month=1, day=2, tzinfo=datetime.UTC)
        chunks = chunk_time_period(start_ts=start_ts, end_ts=end_ts, freq=datetime.timedelta(days=14), split_years=True)

        year_split = datetime.datetime(year=2025, month=1, day=1, hour=0, minute=0, tzinfo=datetime.UTC)
        assert chunks == [(start_ts, year_split), (year_split, end_ts)]

    def test_unsplit_not_on_year(self) -> None:
        """Test that we don't split a short period if it's not necessary."""
        start_ts = datetime.datetime(year=2024, month=11, day=30, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2024, month=12, day=2, tzinfo=datetime.UTC)
        chunks = chunk_time_period(start_ts=start_ts, end_ts=end_ts, freq=datetime.timedelta(days=14), split_years=True)

        assert chunks == [(start_ts, end_ts)]

    def test_split_days(self) -> None:
        """Test that we split a short period into useful days."""
        start_ts = datetime.datetime(year=2024, month=11, day=30, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2024, month=12, day=2, tzinfo=datetime.UTC)
        chunks = chunk_time_period(start_ts=start_ts, end_ts=end_ts, freq=datetime.timedelta(days=1), split_years=True)

        assert chunks[0][0] == start_ts
        assert chunks[-1][1] == end_ts
        assert len(chunks) == 3

    def test_split_days_over_year(self) -> None:
        """Test that we split a short period into useful days over a year boundary, with an extra one."""
        start_ts = datetime.datetime(year=2024, month=12, day=30, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2025, month=1, day=2, tzinfo=datetime.UTC)
        chunks = chunk_time_period(start_ts=start_ts, end_ts=end_ts, freq=datetime.timedelta(days=1), split_years=True)

        assert chunks[0][0] == start_ts
        assert chunks[-1][1] == end_ts
        assert len(chunks) == 5  # extra days for the additional split


class TestGetBankHolidays:
    @pytest.mark.asyncio
    async def test_england_bank_holidays(self) -> None:
        result = get_bank_holidays(UKCountryEnum.England)
        assert datetime.date(year=2020, month=12, day=25) in result  # Christmas
        assert datetime.date(year=2019, month=7, day=12) not in result  # battle of the boyne
        assert datetime.date(year=2022, month=11, day=30) not in result  # St Andrew's Day
        assert datetime.date(year=2025, month=4, day=21) in result  # Easter Monday

    @pytest.mark.asyncio
    async def test_wales_bank_holidays(self) -> None:
        result = get_bank_holidays(UKCountryEnum.Wales)
        assert datetime.date(year=2020, month=12, day=25) in result  # Christmas
        assert datetime.date(year=2019, month=7, day=12) not in result  # battle of the boyne
        assert datetime.date(year=2022, month=11, day=30) not in result  # St Andrew's Day
        assert datetime.date(year=2025, month=4, day=21) in result  # Easter Monday

    @pytest.mark.asyncio
    async def test_scotland_bank_holidays(self) -> None:
        result = get_bank_holidays(UKCountryEnum.Scotland)
        assert datetime.date(year=2020, month=12, day=25) in result  # Christmas
        assert datetime.date(year=2019, month=7, day=12) not in result  # battle of the boyne
        assert datetime.date(year=2022, month=11, day=30) in result  # St Andrew's Day
        assert datetime.date(year=2025, month=4, day=21) not in result  # Easter Monday

    @pytest.mark.asyncio
    async def test_northern_ireland_bank_holidays(self) -> None:
        result = get_bank_holidays(UKCountryEnum.NorthernIreland)
        assert datetime.date(year=2020, month=12, day=25) in result  # Christmas
        assert datetime.date(year=2019, month=7, day=12) in result  # battle of the boyne
        assert datetime.date(year=2022, month=11, day=30) not in result  # St Andrew's Day
        assert datetime.date(year=2025, month=4, day=21) in result  # Easter Monday


class TestSplitIntoSessions:
    def test_sessions_float(self) -> None:
        example_data = [0.1, 0.2, 0.3, 10.1, 10.2, 10.3, 100.1, 100.2, 100.3]
        result = split_into_sessions(example_data, max_diff=1)

        assert result == [[0.1, 0.2, 0.3], [10.1, 10.2, 10.3], [100.1, 100.2, 100.3]]

    def test_sessions_pandas(self) -> None:
        example_data = pd.Series([0.1, 0.2, 0.3, 10.1, 10.2, 10.3, 100.1, 100.2, 100.3])
        result = split_into_sessions(example_data, max_diff=1)

        assert result == [[0.1, 0.2, 0.3], [10.1, 10.2, 10.3], [100.1, 100.2, 100.3]]

    def test_sessions_numpy(self) -> None:
        example_data = np.array([0.1, 0.2, 0.3, 10.1, 10.2, 10.3, 100.1, 100.2, 100.3])
        result = split_into_sessions(example_data, max_diff=1)

        assert result == [[0.1, 0.2, 0.3], [10.1, 10.2, 10.3], [100.1, 100.2, 100.3]]

    def test_all_different_sessions(self) -> None:
        example_data = [0.1, 2.2, 3.3, 4.4, 5.5]
        result = split_into_sessions(example_data, max_diff=1)

        assert result == [[0.1], [2.2], [3.3], [4.4], [5.5]]

    def test_empty_list(self) -> None:
        assert split_into_sessions([], 1) == []

    def test_single_elem(self) -> None:
        assert split_into_sessions([1], 1) == [[1]]

    def test_sessions_timestamps(self) -> None:
        example_data = [
            datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.UTC),
            datetime.datetime(year=2024, month=1, day=2, tzinfo=datetime.UTC),
            datetime.datetime(year=2024, month=1, day=3, tzinfo=datetime.UTC),
            datetime.datetime(year=2024, month=2, day=1, tzinfo=datetime.UTC),
            datetime.datetime(year=2024, month=2, day=2, tzinfo=datetime.UTC),
            datetime.datetime(year=2024, month=2, day=3, tzinfo=datetime.UTC),
        ]
        assert split_into_sessions(example_data, datetime.timedelta(days=1)) == [
            [
                datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.UTC),
                datetime.datetime(year=2024, month=1, day=2, tzinfo=datetime.UTC),
                datetime.datetime(year=2024, month=1, day=3, tzinfo=datetime.UTC),
            ],
            [
                datetime.datetime(year=2024, month=2, day=1, tzinfo=datetime.UTC),
                datetime.datetime(year=2024, month=2, day=2, tzinfo=datetime.UTC),
                datetime.datetime(year=2024, month=2, day=3, tzinfo=datetime.UTC),
            ],
        ]


class TestCheckLatitudeLongitude:
    """Check the function that makes sure we're in the UK.

    This is because I forget which one is latitude and which one is longitude.
    """

    def test_check_france(self) -> None:
        assert not check_latitude_longitude(latitude=48.86738299177877, longitude=2.3502601661414366)
        assert not check_latitude_longitude(longitude=48.86738299177877, latitude=2.3502601661414366)

    def test_check_ireland(self) -> None:
        assert not check_latitude_longitude(latitude=52.66971806024086, longitude=-8.637994648879422)
        assert not check_latitude_longitude(longitude=52.66971806024086, latitude=-8.637994648879422)

    def test_check_germany(self) -> None:
        assert not check_latitude_longitude(latitude=52.54583693080573, longitude=13.381149735676821)
        assert not check_latitude_longitude(longitude=52.54583693080573, latitude=13.381149735676821)

    def test_check_london(self) -> None:
        assert check_latitude_longitude(latitude=51.50598850138515, longitude=-0.14010784279887725)
        assert not check_latitude_longitude(longitude=51.50598850138515, latitude=-0.14010784279887725)
