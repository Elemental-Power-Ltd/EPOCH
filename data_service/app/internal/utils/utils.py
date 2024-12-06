"""
General utility functions, which don't fit anywhere else.

Please don't fill this section with junk, and try to make sure there's no other home
for the functions that go in here.
"""

import datetime
import itertools
import logging
from collections.abc import Sequence
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

logger = logging.getLogger("default")


def typename(x: Any) -> str:
    """
    Get a string representation of the name of a class.

    Parameters
    ----------
    x
        Any python object

    Returns
    -------
        String of the name, e.g. typename(1) == "int"
    """
    return type(x).__name__


def hour_of_year(ts: pd.Timestamp) -> float:
    """
    Convert a given timestamp to being the indexed hour of year (starting at 1).

    YYYY-01-01 00:00 is hour 1 (to mimic Excel numbering).
    Watch out for varying timezones and DST as you go through the year.

    Note that this will drop partial times, e.g. hour_of_year(... 00:30) == 1

    Parameters
    ----------
    ts
        Pandas timestamp or datetime, with a timezone

    Returns
    -------
        one-indexed hour of year
    """
    soy_ts = pd.Timestamp(year=ts.year, month=1, day=1, hour=0, minute=0, tzinfo=ts.tzinfo)
    # watch out for this off-by-one error!
    return 1 + ((ts - soy_ts).total_seconds() / 3600)


def get_with_fallback[T](dictionary: dict[T, Any], keys: list[T]) -> Any:
    """
    Get a value from a dictionary from the first of these keys that is there.

    For example, if you have a dictionary {"spam": "eggs"} and you provide keys ["spim", "spom", "spam"]
    this will try the keys in order and return "eggs".
    Especially helpful if you have dictionary keys that are similar but slightly misspelt (and no risk of retrieving
    the wrong value!)

    Parameters
    ----------
    dictionary
        Dictionary that may have one of the keys in keys
    keys
        Dictionary keys to try in order

    Returns
    -------
        Dictionary key matching the first one we find from keys

    Raises
    ------
    KeyError
        If we can't find any of them in keys
    """
    for key in keys:
        if key in dictionary:
            return dictionary[key]
    raise KeyError(str(keys))


def last_day_of_month(date: datetime.datetime) -> datetime.datetime:
    """
    Get the last day of a month.

    This is useful for date parsing.

    Parameters
    ----------
    date
        Some day within a month (might be useful for it to be the first)

    Returns
    -------
        last day of the corresponding month.
    """
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month + 1, day=1) - datetime.timedelta(days=1)


def check_latitude_longitude(latitude: float, longitude: float) -> bool:
    """
    Check if a pair of coordinates are appropriate latitude and longitude for the UK.

    This function is here because I keep forgetting which way round latitude and longitude go.

    Parameters
    ----------
    latitude
        Number that is probably a latitude or maybe a longitude? This is +90 north of the Equator

    longitude
        Number that is probably a longitude, or maybe a latitude? This is 0 around the Greenwich meridian.
    """
    if longitude < -7.57216793459:
        return False

    if longitude > 1.68153079591:
        return False

    if latitude < 49.959999905:
        return False

    if latitude > 58.6350001085:
        return False

    return True


def split_into_sessions[T: (float, int, datetime.datetime, datetime.date, pd.Timestamp)](
    arr: Sequence[T] | npt.NDArray | pd.Series, max_diff: float | int | datetime.timedelta | pd.Timedelta
) -> list[list[T]]:
    """
    Split this sorted iterable into runs with adjacent gaps no more than max_diff.

    Parameters
    ----------
    arr
        A pre sorted array of numbers, timestamps etc
    max_diff
        The maximum difference between adjacent elements to count as a 'session'

    Returns
    -------
    sessions
        List of lists, where each sublist is sorted in the original order
    """
    if len(arr) == 0:
        return []

    if isinstance(arr[0], datetime.datetime | datetime.date | pd.Timestamp):
        assert isinstance(max_diff, datetime.timedelta | pd.Timedelta), (
            "Must provide a timedelta difference if working with times"
        )
    else:
        assert isinstance(max_diff, float | int)

    sessions: list[list[T]] = []
    curr_session: list[T] = [arr[0]]  # type: ignore

    for first, second in itertools.pairwise(arr):
        if (second - first) <= max_diff:  # pyright: ignore
            curr_session.append(second)
        else:
            sessions.append(curr_session)
            curr_session = [second]
    # Make sure we get the last one as well!
    sessions.append(curr_session)
    return sessions


def add_epoch_fields(non_epoch_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add EPOCH date and time columns to a given dataframe.

    EPOCH currently needs the columns 'Date', 'StartTime' and 'HourOfYear',
    although it doesn't read all of them.
    This may change in future, so the additions are grouped together here.

    """
    assert isinstance(non_epoch_df.index, pd.DatetimeIndex), (
        f"Dataframes for EPOCH must have a DateTimeIndex but got {type(non_epoch_df.index)}"
    )

    non_epoch_df["Date"] = non_epoch_df.index.strftime("%d-%b")
    non_epoch_df["StartTime"] = non_epoch_df.index.strftime("%H:%M")
    non_epoch_df["HourOfYear"] = non_epoch_df.index.map(hour_of_year)

    return non_epoch_df


def symlog[T: (float, npt.NDArray[np.floating])](x: T, c: float = 1.0 / np.log(10.0)) -> T:
    """
    Symmetric function with log-like properties.

    This function is useful for graphing, as it means that large negative numbers
    and large positive numbers can both be represented symmetrically about the y=0 line.
    This is linear in a small region around x = 0, with a range dictated by the constant `c`.

    Parameters
    ----------
    x
        Array or float to scale
    c
        Range of the linear region in the centre

    Returns
    -------
    symmetric log scaled value
    """
    return np.sign(x) * np.log(1.0 + np.abs(x / c))
