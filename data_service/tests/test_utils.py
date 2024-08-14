"""
Tests for other, nonspecific utility functions.

Ideally put these in their own relevant python files!
"""

# ruff: noqa: D101, D102
import datetime

import numpy as np
import pandas as pd

from app.internal.utils import check_latitude_longitude, split_into_sessions


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
