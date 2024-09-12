"""
Functions to parse various formats of gas data we find.

Every time we have to write a new lot of meter data parsers, add them here.
They should be unusually strict and fail if they find anything weird, as often
we'll loop over all the parsers to find one that works.
"""

import datetime
import os
from collections.abc import Callable
from typing import BinaryIO

import numpy as np
import numpy.typing as npt
import pandas as pd

from ..epl_typing import HHDataFrame, MonthlyDataFrame
from ..utils import last_day_of_month, m3_to_kwh


def check_if_readings_not_consumption(df: pd.DataFrame) -> bool:
    """
    Check if this dataframe is parsed wrongly, and is likely a set of raw readings not a consumption.

    Readings tend to be larger and always increase. This isn't guaranteed to be correct.

    Parameters
    ----------
    df

    Returns
    -------
    bool
        If this dataframe is likely to be readings, not a consumption
    """
    always_increasing = np.all(np.ediff1d(df["consumption"]) > 0)
    return bool(always_increasing)


def parse_comma_float(in_str: float | int | str) -> float:
    """
    Parse a float that Excel helpfully put a comma into.

    Watch out for other locales!

    Parameters
    ----------
    in_str
        A float or float-like string, maybe with a comma in it to separate units.

    Returns
    -------
        parsed float
    """
    if isinstance(in_str, str):
        return float(in_str.replace(",", ""))
    return float(in_str)


MONTH_ABBR_TO_IDX = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def month_to_idx(month_name: str) -> int:
    """
    Convert a month name to a 1 indexed number suitable for datetime constructors.

    This will check the lowercase abbreviation, so no need to handle case or size beforehand.

    Parameters
    ----------
    month_name
        English string name of the month

    Returns
    -------
    month_idx
        One indexed month, with January = 1 and December = 12
    """
    return MONTH_ABBR_TO_IDX[month_name[:3].lower()]


def parse_half_hourly(fname: os.PathLike | str | BinaryIO) -> HHDataFrame:
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
    consumption_df = pd.read_csv(fname, skipinitialspace=True).rename(
        columns={
            "Consumption (kWh)": "consumption",
            "HH Read (kwh)": "consumption",
            "HH Read (kWh)": "consumption",
            "kWh": "consumption",
            "Date / Time": "start_ts",
            "dateTime": "start_ts",
            "Start": "start_ts",
            "End": "end_ts",
            "Date (UTC)": "start_ts",
        }
    )
    if "Consumption (m³)" in consumption_df.columns:
        consumption_df["consumption"] = m3_to_kwh(consumption_df["Consumption (m³)"].map(parse_comma_float))
        consumption_df = consumption_df.drop(columns=["Consumption (m³)"])

    assert "consumption" in consumption_df.columns, f"Didn't get a consumption column in {consumption_df.columns}."
    consumption_df["consumption"] = consumption_df["consumption"].map(parse_comma_float)
    DATE_FORMATS = ["ISO8601", "%Y-%m-%d %H:%M:%S", "%d %b %Y %H:%M"]
    for fmt in DATE_FORMATS:
        try:
            consumption_df["start_ts"] = pd.to_datetime(consumption_df["start_ts"], utc=True, format=fmt)
            if "end_ts" in consumption_df.columns:
                consumption_df["end_ts"] = pd.to_datetime(consumption_df["end_ts"], utc=True, format=fmt)
            else:
                consumption_df["end_ts"] = [
                    *consumption_df.start_ts[1:],
                    consumption_df.start_ts.to_numpy()[-1] + pd.Timedelta(minutes=30),
                ]
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"Could not parse {consumption_df['start_ts'].to_numpy()[0]} with {DATE_FORMATS}")
    consumption_df = consumption_df.set_index("start_ts")
    return HHDataFrame(consumption_df[["end_ts", "consumption"]])


def parse_daily_readings(fname: os.PathLike | str | BinaryIO) -> MonthlyDataFrame:
    """
    Read and calculate daily readings, not consumptions (raw meter figures).

    They provide m^3 readings, which we need to convert.

    Parameters
    ----------
    fname
        Name of the file to read, should be a csv

    Returns
    -------
    pd.DataFrame
        (start_ts, end_ts, consumption) half hourly data
    """
    readings_df = (
        pd.read_csv(fname, skipinitialspace=True)
        .rename(columns=lambda x: x.strip())
        .rename(
            columns={"Read Type": "reading_type", "Read": "reading", "Date": "timestamp", "Consumption (m^3)": "consumption_m3"}
        )
    )

    if "reading_type" in readings_df.columns:
        # if there's no information, presume that everything is an actual reading.
        is_estimated_mask = readings_df["reading_type"].isin({"Estimated", "Other"})
        readings_df = readings_df[~is_estimated_mask]
    readings_df["timestamp"] = pd.to_datetime(readings_df["timestamp"], utc=True, format="ISO8601")
    readings_df = readings_df.set_index("timestamp", drop=True).sort_index()

    gas_df = pd.DataFrame()
    gas_df["start_ts"] = readings_df.index.to_numpy()
    gas_df["end_ts"] = [*readings_df.index[1:], readings_df.index[-1] + readings_df.index.diff().mean()]  # type: ignore

    if "consumption" not in readings_df.columns and "consumption_m3" not in readings_df.columns:
        m3_consumptions: npt.NDArray[np.float64] = np.ediff1d(
            readings_df["reading"].map(parse_comma_float).to_numpy().astype(np.float64)
        ).astype(np.float64)
        gas_df["consumption"] = m3_to_kwh(m3_consumptions)
    elif "consumption_m3" in readings_df.columns:
        print(readings_df)
        gas_df["consumption"] = m3_to_kwh(readings_df["consumption_m3"].to_numpy())
    else:
        gas_df["consumption"] = readings_df["consumption"]
    gas_df = gas_df.set_index("start_ts")
    return MonthlyDataFrame(gas_df[["end_ts", "consumption"]])


def parse_be_st_format(fname: os.PathLike | BinaryIO | str) -> MonthlyDataFrame:
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
    start_column = 0
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
            month=month_to_idx(month_name),
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


def parse_horizontal_monthly_both_years(fname: os.PathLike | str | BinaryIO) -> MonthlyDataFrame:
    """
    Read a horizontal monthly format.

    This is of the form
    YY MON DD - YY MON DD
    2123.0

    Parameters
    ----------
    fname
        Name of the file to read, should be a csv

    Returns
    -------
    pd.DataFrame
        (start_ts, end_ts, consumption) half hourly data
    """
    reading_df = (
        pd.read_csv(fname, skipinitialspace=True).rename(columns=lambda x: x.strip()).set_index("Monthly Consumption").T
    )
    split_dates = reading_df.index.str.split("-")
    readings = []
    for (start_date, end_date), consumption in zip(split_dates, reading_df[reading_df.columns[0]], strict=False):
        if pd.isna(consumption):
            continue
        consumption = parse_comma_float(consumption)

        year, month_name, day = start_date.strip().split()
        month_name = month_name[:3]
        start_ts = pd.to_datetime(f"{year} {month_name} {day}", utc=True, format="%d %b %y")

        end_year, end_month_name, end_day = end_date.strip().split()
        end_month_name = end_month_name[:3]
        end_ts = pd.to_datetime(f"{end_year} {end_month_name} {end_day}", utc=True, format="%d %b %y")
        readings.append({"start_ts": start_ts, "end_ts": end_ts, "consumption": consumption})

    gas_df = pd.DataFrame.from_records(readings).set_index("start_ts")
    return MonthlyDataFrame(gas_df[["end_ts", "consumption"]])


def parse_horizontal_monthly_only_month(fname: os.PathLike | str | BinaryIO) -> MonthlyDataFrame:
    """
    Parse a reading file with columns being a single month.

    Each column is expected to run from (start of month) to (end of month)

    Parameters
    ----------
    fname
        CSV-like object to parse

    Returns
    -------
    MonthlyDataFrame
        Usual elec/gas consumption dataframe
    """
    df = pd.read_csv(fname, skipinitialspace=True).rename(columns=lambda x: x.strip())
    dates = df.columns
    parsed_rows = []
    for date, consumption in zip(dates, df.iloc[0], strict=False):
        try:
            month_str, year_str = date.split("-")
        except ValueError:
            continue
        month = month_to_idx(month_str)
        year = int(year_str)
        if year < 2000:
            year += 2000
        start_ts = datetime.datetime(year=year, month=month, day=1, tzinfo=datetime.UTC)
        end_ts = last_day_of_month(start_ts)
        consumption = parse_comma_float(consumption)

        parsed_rows.append({"start_ts": start_ts, "end_ts": end_ts, "consumption": consumption})

    return MonthlyDataFrame(pd.DataFrame.from_records(parsed_rows).set_index("start_ts"))


def parse_horizontal_monthly_only_end_year(fname: os.PathLike | str | BinaryIO) -> MonthlyDataFrame:
    """
    Parse a reading file with columns being specified periods e.g. 01 Jan - 31 Jan 2024.

    Watch out, as the date parsing is relatively delicate.

    Parameters
    ----------
    fname
        CSV-like object to parse

    Returns
    -------
    MonthlyDataFrame
        Usual elec/gas consumption dataframe
    """
    df = pd.read_csv(fname, skipinitialspace=True).rename(columns=lambda x: x.strip())
    dates = df.columns
    parsed_rows = []
    for date, consumption in zip(dates, df.iloc[0], strict=False):
        try:
            start_date, end_date = (item.strip() for item in date.split("-"))
        except ValueError:
            continue
        consumption = parse_comma_float(consumption)
        start_d_str, start_m_str = start_date.split(" ")
        start_d = int(start_d_str)
        start_m = month_to_idx(start_m_str)
        end_d_str, end_m_str, end_y_str = end_date.split(" ")
        end_d = int(end_d_str)
        end_m = month_to_idx(end_m_str)
        end_y = int(end_y_str)
        if end_y < 2000:
            end_y += 2000

        if start_m < end_m:
            start_y = end_y
        else:
            start_y = end_y - 1

        start_ts = datetime.datetime(year=start_y, month=start_m, day=start_d, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=end_y, month=end_m, day=end_d, tzinfo=datetime.UTC)
        parsed_rows.append({"start_ts": start_ts, "end_ts": end_ts, "consumption": consumption})

    return MonthlyDataFrame(pd.DataFrame.from_records(parsed_rows).set_index("start_ts"))


def parse_square_half_hourly(fname: os.PathLike | str | BinaryIO) -> HHDataFrame:
    """
    Read a baffling square (date x time) format.

    Parameters
    ----------
    fname
        Name of the file to read, should be a csv

    Returns
    -------
    pd.DataFrame
        (start_ts, end_ts, consumption) half hourly data
    """
    square_df = (
        pd.read_csv(fname, skipinitialspace=True)
        .rename(columns=lambda x: x.strip().lower())
        .rename(
            columns={
                "dailytotal": "total",
            }
        )
    )

    if "total" in square_df.columns:
        square_df = square_df.drop(columns=["total"])
    square_df["date"] = pd.to_datetime(square_df["date"], utc=True, format="ISO8601")
    square_df = square_df.set_index("date", drop=True)

    if len(square_df.columns) < 47:
        raise ValueError(f"File not in square half hourly format, got {square_df.columns}")
    readings = []
    for date in square_df.index:
        for col_idx, col_name in enumerate(square_df.columns):
            if col_idx >= 48:
                # We've got extra columns -- probably just blank?
                continue
            try:
                hours, minutes = (int(item) for item in col_name.split(":"))
            except ValueError:
                # We haven't got usefully named time columns, so hope they're in order
                # and use the position instead
                hours = col_idx // 2
                minutes = 30 * (col_idx % 2)
            time = datetime.time(hour=hours, minute=minutes, second=0, tzinfo=datetime.UTC)
            timestamp = datetime.datetime.combine(date, time)

            consumption = parse_comma_float(square_df.loc[date, col_name])  # pyright: ignore
            readings.append({
                "start_ts": timestamp,
                "end_ts": timestamp + datetime.timedelta(minutes=30),
                "consumption": consumption,
            })
    gas_df = pd.DataFrame.from_records(readings).set_index("start_ts")
    return HHDataFrame(gas_df[["end_ts", "consumption"]])


def try_meter_parsing(fname: os.PathLike | str | BinaryIO) -> MonthlyDataFrame | HHDataFrame:
    """
    Try different parsing functions to get one that works for this file.

    Parameters
    ----------
    fname
        File or file-like object to try parsing

    Returns
    -------
        parsed dataframe with `(start_ts, end_ts, consumption)`

    Raises
    ------
    NotImplementedError
        If we couldn't find a parser
    """
    possible_parsers: list[
        Callable[[os.PathLike | str | BinaryIO], MonthlyDataFrame] | Callable[[os.PathLike | str | BinaryIO], HHDataFrame]
    ] = [
        parse_be_st_format,
        parse_daily_readings,
        parse_half_hourly,
        parse_square_half_hourly,
        parse_horizontal_monthly_both_years,
        parse_horizontal_monthly_only_end_year,
        parse_horizontal_monthly_only_month,
    ]
    for parser in possible_parsers:
        try:
            parsed_df = parser(fname)
            consumption_mask = ~pd.isna(parsed_df.consumption)
            return parsed_df[consumption_mask], parser.__name__  # type: ignore
        except ValueError:
            continue
        except KeyError:
            continue
        except AssertionError:
            continue
    raise NotImplementedError("No parser available for this file.")
