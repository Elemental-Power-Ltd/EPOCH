"""Generate some reasonable synthetic tariffs to match input time series."""

import datetime

import numpy as np
import pandas as pd


def create_fixed_tariff(timestamps: pd.DatetimeIndex, fixed_cost: float) -> pd.DataFrame:
    """
    Create a dataframe representing a fixed tariff that costs the same at every timestep.

    Parameters
    ----------
    timestamps
        DatetimeIndex you want to create entries at (most likely half hourly)
    fixed_cost
        Tariff fixed cost in p / kWh

    Returns
    -------
        Dataframe with cost column and timestamp index.
    """
    return pd.DataFrame(index=timestamps, data={"cost": [fixed_cost for _ in timestamps]})


def create_day_and_night_tariff(timestamps: pd.DatetimeIndex, day_cost: float, night_cost: float) -> pd.DataFrame:
    """
    Create a dataframe representing a fixed tariff that has a different day and night cost.

    This mimics an Economy 7 tariff which is cheap from 00:30 UTC to 07:30 UTC (watch out for daylight savings)
    and expensive in day hours from 07:30 to 00:30.

    Parameters
    ----------
    timestamps
        DatetimeIndex you want to create entries at (most likely half hourly)
    day_cost
        Tariff day cost in p / kWh (07:30 to 00:30)
    day_cost
        Tariff night cost in p / kWh (00:30 to 07:30)

    Returns
    -------
        Dataframe with cost column and timestamp index.
    """
    df = pd.DataFrame(index=timestamps, data={"cost": [day_cost for _ in timestamps]})
    utc_times = timestamps.tz_convert(datetime.UTC)
    is_night_mask = np.logical_and(
        utc_times.time > datetime.time(hour=0, minute=0), utc_times.time <= datetime.time(hour=7, minute=0)
    )
    df.loc[is_night_mask, "cost"] = night_cost
    return df


def create_peak_tariff(
    timestamps: pd.DatetimeIndex, day_cost: float, night_cost: float | None = None, peak_cost: float = 12.0
) -> pd.DataFrame:
    """
    Create a tariff with a peak time premum, and optionally cheap night rates.

    This creates either a two tier (fixed, peak) or three tier (night, day, peak) tariff.
    The night period is always 00:30 to 07:30 UTC, but could be the same cost as the day
    period if not specified.
    The peak period is always 16:00 to 19:00 UTC, and has an extra premium added.

    Parameters
    ----------
    timestamps
        DatetimeIndex you want to create entries at (most likely half hourly)
    day_cost
        Tariff day cost in p / kWh (07:30 to 00:30)
    night_cost
        Tariff night cost in p / kWh (00:30 to 07:30). If None, day costs the same as night.
    peak_cost
        Tariff night peak in p / kWh charged from 16:00 to 19:00. Not a delta, but the absolute cost.

    Returns
    -------
        Dataframe with cost column and timestamp index.
    """
    df = pd.DataFrame(index=timestamps, data={"cost": [day_cost for _ in timestamps]})

    if night_cost is None:
        night_cost = day_cost

    utc_times = timestamps.tz_convert(datetime.UTC)
    cosy_periods = [
        (datetime.time(hour=4, minute=0), datetime.time(hour=7, minute=0)),
        (datetime.time(hour=13, minute=0), datetime.time(hour=16, minute=0)),
        (datetime.time(hour=22, minute=0), datetime.time(hour=23, minute=59, second=59)),
    ]
    for start_ts, end_ts in cosy_periods:
        is_cosy_mask = np.logical_and(start_ts <= utc_times.time, utc_times.time < end_ts)
        df.loc[is_cosy_mask, "cost"] = night_cost

    is_peak_mask = np.logical_and(
        datetime.time(hour=16, minute=0) <= utc_times.time, utc_times.time < datetime.time(hour=19, minute=0)
    )
    df.loc[is_peak_mask, "cost"] = peak_cost
    return df


def create_shapeshifter_tariff(
    timestamps: pd.DatetimeIndex, day_cost: float, night_cost: float, peak_cost: float
) -> pd.DataFrame:
    """
    Create a ShapeShifter Trio tariff with a peak time premium and cheap night rates.

    This creates a three tier (night, day, peak) tariff.
    The night period is always 00:00 to 07:00 UTC.
    The peak period is always 16:00 to 19:00 UTC, and has an extra premium added.
    https://octopus.energy/smart/shape-shifters/

    Parameters
    ----------
    timestamps
        DatetimeIndex you want to create entries at (most likely half hourly)
    day_cost
        Tariff day cost in p / kWh (07:00 to 16:00 and 19:00 - 24:00)
    night_cost
        Tariff night cost in p / kWh (00:00 to 07:00).
    peak_cost
        Tariff night cost in p / kWh (16:00 to 19:90).

    Returns
    -------
        Dataframe with cost column and timestamp index.
    """
    # Pre-fill with day costs as they're the "default"
    df = pd.DataFrame(index=timestamps, data={"cost": [day_cost for _ in timestamps]})
    utc_times = timestamps.tz_convert(datetime.UTC)
    night_start, night_end = datetime.time(hour=0, minute=0), datetime.time(hour=7, minute=0)
    peak_start, peak_end = datetime.time(hour=16, minute=0), datetime.time(hour=19, minute=0)

    is_night_mask = np.logical_and(night_start <= utc_times.time, utc_times.time < night_end)
    df.loc[is_night_mask, "cost"] = night_cost

    is_peak_mask = np.logical_and(peak_start <= utc_times.time, utc_times.time < peak_end)
    df.loc[is_peak_mask, "cost"] = peak_cost
    return df


def create_custom_tariff(timestamps: pd.DatetimeIndex, end_times: list[datetime.time], costs: list[float]) -> pd.DataFrame:
    """
    Create a custom tariff with specified costs in pence.

    The time bands are in the form [end_time, cost], and we iterate over them in reverse
    order, filling the costs up to each end time.

    Parameters
    ----------
    timestamps
        Timestamps at which to sample the tariff costs
    end_times
        Within-day times at which each tariff band ends
    costs
        Costs for each band in p / kWh

    Returns
    -------
    df
        Dataframe with cost column and timestamp index.
    """
    df = pd.DataFrame(index=timestamps, data={"cost": [float("NaN") for _ in timestamps]})

    # Midnight is handled unusually as it doesn't work nicely with < which is the natural way
    # to enter it as an argument.
    # All times are before midnight, so overwrite them now.
    # We check only the hour and minute to avoid timezone and second issues.

    for end_time, cost in zip(end_times, costs, strict=False):
        if end_time.hour == 0 and end_time.minute == 0:
            df["cost"] = cost

    assert isinstance(df.index, pd.DatetimeIndex)
    for end_time, cost in sorted(zip(end_times, costs, strict=False), reverse=True):
        df[df.index.time <= end_time] = cost
    return df
