"""
Tests for other, nonspecific utility functions.

Ideally put these in their own relevant python files!
"""

# ruff: noqa: D101, D102
import datetime

import numpy as np
import pandas as pd

from app.internal.utils import split_into_sessions


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
