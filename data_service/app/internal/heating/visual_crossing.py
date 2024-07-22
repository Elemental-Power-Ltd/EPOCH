"""
Functions for handling weather data from VisualCrossing.
"""

import datetime
import os
import pathlib

import numpy as np
import pandas as pd
import requests

from ..utils import load_dotenv


def get_visual_crossing(location: str, start_ts: datetime.datetime, end_ts: datetime.datetime) -> requests.Response:
    """
    Get a weather history as a raw response from VisualCrossing.

    This sets some sensible defaults for the VisualCrossing API call.
    Be careful as it may be slow if you request lots of data.

    Parameters
    ----------
    location
        String describing where to get weather for, e.g. 'Taunton,UK'
    start_ts
        Earliest timestamp (preferably UTC) to get weather for. Rounds to previous hour.
    end_ts
        Latest timestamp (preferably UTC) to get weather for. Rounds to next hour.

    Returns
    -------
        raw response from VisualCrossing, with no sanity checking.
    """
    BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

    load_dotenv()
    url = f"{BASE_URL}/{location}/"
    url += f"{int(start_ts.timestamp())}/{int(end_ts.timestamp())}"

    desired_columns = [
        "datetimeEpoch",
        "temp",
        "humidity",
        "precip",
        "precipprob",
        "snow",
        "snowdepth",
        "windgust",
        "windspeed",
        "winddir",
        "pressure",
        "cloudcover",
        "solarradiation",
        "solarenergy",
        "degreedays",
    ]
    req = requests.get(
        url,
        params={
            "key": os.environ["VISUAL_CROSSING_API_KEY"],
            "include": "hours",
            "unitGroup": "metric",
            "timezone": "Z",  # We want UTC
            "lang": "uk",
            "elements": ",".join(desired_columns),
        },
    )
    return req


def visual_crossing_to_pandas(raw_vc: requests.Response) -> pd.DataFrame:
    """
    Convert a VisualCrossing weather history to a useful pandas dataframe.

    Parameters
    ----------
    raw_vc
        Response from VC, with ["days"] and ["hours"]

    Returns
    -------
        pandas dataframe with datetime index set and weather data.
    """
    records = [hour for day in raw_vc.json()["days"] for hour in day["hours"]]

    df = pd.DataFrame.from_records(records)
    df["timestamp"] = pd.to_datetime(df["datetimeEpoch"] * 1e9, utc=True)
    df = df.set_index("timestamp").drop(["datetimeEpoch"], axis=1)
    return df


def create_weather_dataframe(
    year: int,
    data_directory: os.PathLike = pathlib.Path("InputData"),
) -> pd.DataFrame:
    """
    Generate a complete training dataset from VC and the existing Hload / Rgen data.

    Will load a cached parquet file of VisualCrossing data if available.
    Augments the VisualCrossing data with some time encoding and heating
    degree days data.

    Parameters
    ----------
    year
        The year to get data for
    data_directory
        The directory to find parquet cached data and target CSVs

    Returns
    -------
        augmented pandas dataframe, with target data joined
    """
    weather_path = pathlib.Path(data_directory) / f"taunton_weather_{year}.parquet"
    if weather_path.exists():
        df = pd.read_parquet(weather_path)
    else:
        req = get_visual_crossing(
            "Taunton,UK",
            datetime.datetime(year=year, month=1, day=1, tzinfo=datetime.UTC),
            datetime.datetime(year=year, month=12, day=31, tzinfo=datetime.UTC),
        )
        df = visual_crossing_to_pandas(req)
        df.to_parquet(weather_path)

    rgen_df = pd.read_csv(pathlib.Path(data_directory) / "CSVRGen.csv")
    rgen_df["datetime"] = pd.to_datetime(
        rgen_df.Date + rgen_df["Start Time"], format="%d-%b%H:%M", utc=True
    ) + pd.offsets.DateOffset(years=year - 1900)  # type: ignore
    rgen_df = rgen_df.set_index("datetime").drop(["HoY", "Date", "Start Time", "Unnamed: 7", "RGen4"], axis=1).dropna()

    hgen_df = pd.read_csv(pathlib.Path(data_directory) / "CSVHload.csv")
    hgen_df["datetime"] = pd.to_datetime(
        hgen_df.Date + hgen_df["Start Time"], format="%d-%b%H:%M", utc=True
    ) + pd.offsets.DateOffset(years=year - 1900)  # type: ignore
    hgen_df = (
        hgen_df.set_index("datetime")
        .drop(
            ["HoY", "Date", "Start Time", "Unnamed: 7", "HLoad2", "HLoad3", "HLoad4"],
            axis=1,
        )
        .dropna(axis=0)
    )

    # Add some extra feature columns: heating degree days and
    # a simple time encoding.

    total_df = rgen_df.join(df).fillna(0).join(hgen_df)
    total_df["hdd"] = np.maximum(15.5 - total_df["temp"], 0)
    total_df["last_hdd"] = np.roll(total_df["hdd"].to_numpy(), -1)

    time_index = total_df.index
    assert isinstance(time_index, pd.DatetimeIndex)
    total_df["hour_sin"] = np.sin(2 * np.pi * time_index.hour / 24)
    total_df["hour_cos"] = np.cos(2 * np.pi * time_index.hour / 24)
    total_df["day_sin"] = np.sin(np.minimum(2 * np.pi * time_index.dayofyear / 365, 1.0))
    total_df["day_cos"] = np.cos(np.minimum(2 * np.pi * time_index.dayofyear / 365, 1.0))
    return total_df
