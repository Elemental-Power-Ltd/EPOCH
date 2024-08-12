"""
General utility functions, which don't fit anywhere else.

Please don't fill this section with junk, and try to make sure there's no other home
for the functions that go in here.
"""
import logging
import datetime
import itertools
import os
import pathlib
from collections.abc import Sequence
from typing import Any

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


def hour_of_year(ts: pd.Timestamp) -> int:
    """
    Convert a given timestamp to being the indexed hour of year (starting at 1).

    YYYY-01-01 00:00 is hour 1 (to mimic Excel numbering).
    Watch out for varying timezones and DST as you go through the year.

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
    return 1 + (int((ts - soy_ts).total_seconds()) // 3600)


def load_dotenv(fname: os.PathLike = pathlib.Path(".env")) -> dict[str, str]:
    """
    Load a set of environment variables from an .env file.

    Mutates the environment variables for this python process, and
    returns them as a dictionary just in case.

    Parameters
    ----------
    fname
        Path to the environment file to load (it's probably ".env")

    Returns
    -------
        environment dictionary, with new keys added.
    """
    fpath = pathlib.Path(fname).resolve()
    if not fpath.is_file():
        file_name = fpath.name
        for parent in fpath.parents:
            parent_path = parent.joinpath(file_name)
            if parent_path.is_file():
                fpath = parent_path
                break
        else:
            logger.warning(f"Could not find {fname} in the specified location {fpath} or its parents.")
            return {}
            

    with open(fpath) as fi:
        for line in fi:
            key, value = line.strip().split("=", 1)
            os.environ[key] = value
    # turn this into a dict to prevent any trouble with weird types
    return dict(os.environ.items())


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
        assert isinstance(
            max_diff, datetime.timedelta | pd.Timedelta
        ), "Must provide a timedelta difference if working with times"
    else:
        assert isinstance(max_diff, float | int)

    sessions: list[list[T]] = []
    curr_session: list[T] = [arr[0]]  # type: ignore

    for first, second in itertools.pairwise(arr):
        if (second - first) <= max_diff:
            curr_session.append(second)
        else:
            sessions.append(curr_session)
            curr_session = [second]
    # Make sure we get the last one as well!
    sessions.append(curr_session)
    return sessions
