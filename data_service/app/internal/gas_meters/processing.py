"""
Functions to resample or group up gas data.

Often, we'll want to group half hourly gas data (very noisy) into longer periods, or to reasonably
fill in missing periods.
"""

import numpy as np
import pandas as pd

from ..epl_typing import HHDataFrame, MonthlyDataFrame


def fill_in_half_hourly(gas_df: HHDataFrame) -> HHDataFrame:
    """
    Resample and fix half hourly gas data to meet our requirements.

    This is useful if we've got slightly spotty gas readings.
    Linearly interpolates between the readings we've got
    and fills in a `timedelta` column.

    Parameters
    ----------
    gas_df
        Hourly or half-hourly-ish gas dataframe

    Returns
    -------
    gas_df
        Nice, clean, resampled 30 minute gas data.
    """
    gas_df["timedelta"] = (gas_df["end_ts"] - gas_df.index).dt.total_seconds()
    gas_df = HHDataFrame(gas_df.resample("30min", origin="epoch").mean(numeric_only=True).interpolate(method="time"))
    # We can't naively add the end_ts, so instead we keep the timedeltas
    # and use that to reconstruct them. This might be weird if we have multiple
    # entries per hh?
    gas_df["end_ts"] = gas_df.index + pd.to_timedelta(gas_df["timedelta"], unit="s")
    gas_df = HHDataFrame(gas_df.drop(columns="timedelta"))
    return gas_df


def hh_gas_to_monthly(hh_gas_df: HHDataFrame) -> MonthlyDataFrame:
    """
    Resample a half hourly gas dataframe to monthly for further analysis.

    We often want a monthly gas dataframe for regression purposes, as the half hourly
    data can be too noisy. This does all the bookkeeping, including finding start
    and end periods and how long they are.
    Note that the returned start_ts and end_ts periods are not necessarily the same
    as the months in the index!

    Parameters
    ----------
    hh_gas_df
        Half hourly gas meter data for a site. Must have a "consumption" column, and a timestamp index.

    Returns
    -------
    monthly_gas_df
        Monthly gas usage downsampled
    """
    if "start_ts" not in hh_gas_df.columns:
        hh_gas_df["start_ts"] = hh_gas_df.index
    monthly_gas_df = MonthlyDataFrame(hh_gas_df.resample(pd.tseries.offsets.MonthBegin()).sum(numeric_only=True))

    # Select the end dates as either the end of the month, or the last reading we took
    # Similarly for start dates.
    # TODO (2024-06-25 MHJB): make this work also for periods with missing data (split into sub-months?)
    end_dates = hh_gas_df[["consumption"]].resample(pd.tseries.offsets.MonthEnd()).sum().index + pd.Timedelta(days=1)
    min_dates, max_dates = (
        hh_gas_df.resample(pd.tseries.offsets.MonthBegin()).min()["start_ts"],
        hh_gas_df.resample(pd.tseries.offsets.MonthBegin()).max()["start_ts"] + pd.Timedelta(minutes=30),
    )
    monthly_gas_df["start_ts"] = np.maximum(monthly_gas_df.index, min_dates)
    monthly_gas_df["end_ts"] = np.minimum(end_dates, max_dates)
    monthly_gas_df["days"] = (monthly_gas_df["end_ts"] - monthly_gas_df["start_ts"]).dt.total_seconds() / 86400
    return monthly_gas_df
