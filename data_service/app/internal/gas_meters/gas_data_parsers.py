import datetime
import os

import numpy as np
import pandas as pd

from ..epl_typing import HHDataFrame, MonthlyDataFrame
from ..utils import m3_to_kwh

MONTH_TO_IDX = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def parse_octopus_half_hourly(fname: os.PathLike | str) -> HHDataFrame:
    """
    Read the lovely Octopus half hourly gas meter format.

    They provide m^3 readings, which we need to convert, and
    a set of half hourly timestamps.

    Parameters
    ----------
    fname
        Name of the file to read, should be a csv

    Returns
    -------
    pd.DataFrame
        (start_ts, end_ts, consumption) half hourly data
    """
    gas_df = pd.read_csv(fname, skipinitialspace=True).rename(
        columns={
            "Consumption (kWh)": "consumption",
            "Start": "start_ts",
            "End": "end_ts",
            "kWh": "consumption",
            "dateTime": "start_ts",
        }
    )
    if "Consumption (m³)" in gas_df.columns:
        gas_df["consumption"] = m3_to_kwh(gas_df["Consumption (m³)"])
        gas_df = gas_df.drop(columns=["Consumption (m³)"])

    assert "consumption" in gas_df.columns, f"Didn't get a consumption column in {gas_df.columns}."

    gas_df["start_ts"] = pd.to_datetime(gas_df["start_ts"], utc=True, format="ISO8601")
    if "end_ts" in gas_df.columns:
        gas_df["end_ts"] = pd.to_datetime(gas_df["end_ts"], utc=True, format="ISO8601")
    else:
        gas_df["end_ts"] = [*gas_df.start_ts[1:], pd.NaT]

    gas_df = gas_df.set_index("start_ts")
    return HHDataFrame(gas_df[["end_ts", "consumption"]])


def parse_be_st_format(fname: os.PathLike, start_column: int = 0) -> MonthlyDataFrame:
    """
    Parse the BE-ST gas consumption data format.

    This is a somewhat complicated Excel format which is hostile to our parsing.
    Multiple buildings can be stored in the Natural Gas sheet, which come in blocks of 4 columns.
    To select the right building, use the start_column parameter (0 for the first building, probably
    5 for the next, and then 9, but we can't be sure).

    This will assume a consumption for "January" runs from 01-01 00:00 to 01-31 23:59 (i.e. the entirety of the named month).
    This function is delicate owing to the difficulties of parsing this file.

    Parameters
    ----------
    fname
        File in the BE-ST readings format
    start_column
        First column to read a block of 4 from, representing a single building.

    Returns
    -------
    pd.DataFrame
        (start_ts, end_ts, consumption, cost) for a single building from this sheet.
    """

    df = pd.read_excel(
        fname,
        sheet_name="Natural Gas",
        header=5,
        usecols=list(range(start_column, start_column + 4)),
    ).rename(columns={"kWh": "consumption", "£ (inc VAT)": "cost"})
    for i in range((start_column // 4) + 1):
        df = df.rename(
            columns={
                f"kWh.{i}": "consumption",
                f"Year.{i}": "Year",
                f"Month.{i}": "Month",
                f"£ (inc VAT).{i}": "cost",
            }
        )
    df["Year"] = df["Year"].ffill()
    last_year, last_month = None, None
    year_idx = 0

    start_timestamps: list[pd.Timestamp | pd._libs.tslibs.nattype.NaTType] = []  # type: ignore
    for year, month in zip(df.Year, df.Month, strict=False):
        # Throw out the entries with no year or month information
        if pd.isna(year) or pd.isna(month):
            start_timestamps.append(pd.NaT)
            continue
        # Try parsing the split year information in the form 20XX/YY
        try:
            year_choice = int(year[0:4]), int(year[0:2] + year[5:8])
        except ValueError:
            start_timestamps.append(pd.NaT)
            continue

        # If we've got into a new year block, reset the flag
        if last_year != year:
            year_idx = 0
        # If we've gone from December to January,
        # increment the flag
        if last_month == "December" and month == "January":
            year_idx = 1
        # get rid of any [A] suffixes that BE-ST have put in
        month_name = month.split(" ")[0]

        start_ts = pd.Timestamp(
            year=year_choice[year_idx],
            month=MONTH_TO_IDX[month_name],
            day=1,
            tz=datetime.UTC,
        )
        start_timestamps.append(start_ts)

        last_year, last_month = year, month
    df["start_ts"] = start_timestamps
    # the end timestamp is the first timestamp of the next month
    # This needs an empty month at the end to work correctly
    df["end_ts"] = df["start_ts"].shift(-1) - pd.Timedelta(seconds=1)
    # Finally, chuck out information with no consumption (we don't care about it)
    # or with no "Month" information as that's from the totals at the end
    consumption_na_mask = np.logical_or(pd.isna(df["consumption"]), pd.isna(df["Month"]))
    df = df[~consumption_na_mask].drop(columns=["Year", "Month"]).set_index("start_ts")
    df["start_ts"] = df.index

    df["days"] = (df["end_ts"] - df["start_ts"] + pd.Timedelta(seconds=1)) / np.timedelta64(1, "D")  # type: ignore
    return MonthlyDataFrame(df)
