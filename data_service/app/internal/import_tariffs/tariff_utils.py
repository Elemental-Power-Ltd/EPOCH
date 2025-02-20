"""Miscellaneous tariff utility functions."""

import datetime
from collections.abc import Collection

import numpy as np
import pandas as pd

from ...models.import_tariffs import GSPEnum


def combine_tariffs(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Combine a set of tariff dataframes across time.

    This doesn't do any quality checking, so please make sure
    that your dataframes are of consistent frequencies and
    in the same time zones.
    This assumes that a client always switches on to the maximum tariff
    the moment it becomes available.

    Parameters
    ----------
    dfs
        List of parameters with datetime indexes

    Returns
    -------
        Tariff dataframe like the passed in ones, with maximum costs at each ts.
    """
    if len(dfs) == 1:
        return dfs[0]
    total_df = pd.concat(dfs, axis=0)
    assert isinstance(total_df.index, pd.DatetimeIndex)

    return total_df.groupby(level=0).max()


def resample_to_range(
    df: pd.DataFrame,
    freq: pd.Timedelta | None = None,
    start_ts: datetime.datetime | None = None,
    end_ts: datetime.datetime | None = None,
) -> pd.DataFrame:
    """
    Resample a dataframe to a given frequency between two times.

    This will forward and backward fill to have an index
    of the form [start_ts + i * freq] up to end_ts.

    Parameters
    ----------
    df
        Dataframe with DatetimeIndex to resample
    freq
        Time gap between new samples. If None, defaults to 30 minutes.
    start_ts
        Earliest time you want, if None will use the earliest start_ts in df
    end_ts
        Latest time you want, if None will use the latest end_ts in df

    Returns
    -------
        df with evenly spaced sampled at `freq` between `start_ts` and `end_ts`.
    """
    if freq is None:
        freq = pd.Timedelta(minutes=30)
    reindex_start = datetime.datetime.now(datetime.UTC)
    if start_ts is not None:
        reindex_start = start_ts
    elif (not pd.isna(df.start_ts.min())) and df.start_ts.min() < reindex_start:
        reindex_start = df.start_ts.min()
    else:
        raise ValueError(f"Couldn't get a reasonable start from {start_ts=} and {df.start_ts.min()}")

    if end_ts is not None:
        reindex_end = end_ts
    elif (not pd.isna(df.end_ts.max())) and df.end_ts.max() > reindex_start:
        reindex_end = df.end_ts.max()
    else:
        reindex_end = reindex_start + pd.Timedelta(days=7)

    new_starts = pd.date_range(reindex_start, reindex_end, freq=freq, inclusive="both")
    df = df.resample(freq).max().reindex(new_starts).ffill().bfill()
    df["start_ts"] = df.index
    df["end_ts"] = df.index + freq

    mask = np.ones(len(df.index), dtype=bool)
    if start_ts is not None:
        mask = np.logical_and(df.start_ts >= start_ts, mask)
    if end_ts is not None:
        mask = np.logical_and(df.end_ts <= end_ts, mask)
    return df[mask]


def tariff_to_new_timestamps(tariff_df: pd.DataFrame, date_range: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Take a tariff and turn it to a new set of timestamps.

    This might be useful if e.g. you have an old tariff that you want to work
    with EPOCH and needs to line up with the new set of dates.
    This will check for each timestamp if we've got a value from the days in the week
    either side, or failing that, if we've got a value from the same time in a previous year.

    This is currently a bit slow and there is room to optimise it.

    Parameters
    ----------
    tariff_df
        Dataframe with cost column and datetime index
    date_range
        Datetime index that you want the new df to have

    Returns
    -------
    pd.DataFrame
        New dataframe with date_range as the index and costs from tariff_df
    """
    old_tariff_timestamps = frozenset(tariff_df.index)

    def check_timestamp(ts: pd.Timestamp | datetime.datetime, tariff_df: pd.DataFrame = tariff_df) -> pd.Timestamp:
        if ts in old_tariff_timestamps:
            val: pd.Timestamp = tariff_df.at[ts, "cost"]
            return val

        all_offsets = [ts + pd.DateOffset(days=day_offset) for day_offset in range(-7, 7, 1)] + [
            ts + pd.DateOffset(years=year_offset) for year_offset in range(5, -5, -1)
        ]
        for new_ts in all_offsets:
            if new_ts in tariff_df.index:
                return tariff_df.at[new_ts, "cost"]

        raise ValueError(f"Could not find an offset for {ts} in {all_offsets} in {tariff_df.index}")

    new_costs = [check_timestamp(item) for item in date_range]
    return pd.DataFrame(index=date_range, data={"cost": new_costs})


def region_or_first_available(region_code: GSPEnum, keys: Collection[str]) -> str:
    """
    Get the tariff region, or the first available if it's not in there.

    Parameters
    ----------
    region_code
        Grid supply point enum for this region (A-K)
    keys
        Container of keys, probably like dict_keys(["_C", "_D"]) etc.

    Returns
    -------
    dict key of this region like "_C"
    """
    if region_code.value in keys:
        return region_code.value
    return next(iter(keys))
