"""Functions to output pandas dataframes into EPOCH friendly formats.

Mostly you won't use these, as the endpoints will send these out to the optimiser, but
they might sometimes be handy.
"""

import os

import numpy as np
import pandas as pd

from ..epl_typing import HHDataFrame, WeatherDataFrame
from .utils import hour_of_year


def to_rgen_csv(df: HHDataFrame, fname: os.PathLike | str = "CSVRGen.csv") -> None:
    """
    Output renewables generation data to an Epoch-friendly CSV.

    Does the date formatting and hour-of-year calculation required for EPOCH.

    Parameters
    ----------
    df
        Dataframe, ideally from PVGIS, with a 'power' column and a datetime index.
    fname
        Name of the file to write to (should be 'CSVRGen.csv' for the current version)

    Returns
    -------
        None
    """
    df = HHDataFrame(df.resample(pd.Timedelta(hours=1)).mean().interpolate(method="time"))
    solar_gen = df["power"].to_numpy(dtype=np.float32)
    assert isinstance(df.index, pd.DatetimeIndex), "Must be a DatetimeIndex-ed dataframe"
    new_df = pd.DataFrame(
        {
            "HoY": [hour_of_year(ts) for ts in df.index],
            "Date": df.index.strftime("%d-%b"),
            "Start Time": df.index.strftime("%H:%M"),
            "RGen1": solar_gen,
            "RGen2": np.zeros_like(solar_gen),
            "RGen3": np.zeros_like(solar_gen),
            "RGen4": np.zeros_like(solar_gen),
        }
    )
    new_df.to_csv(fname, index=False)


def to_hload_csv(df: HHDataFrame, fname: os.PathLike | str = "CSVHLoad.csv") -> None:
    """
    Output heating load data to an Epoch-friendly CSV.

    Does the date formatting and hour-of-year calculation required for EPOCH.

    Parameters
    ----------
    df
        Dataframe, ideally from Demand Ninja, with a 'heating_power' column and a datetime index.
    fname
        Name of the file to write to (should be 'CSVRGen.csv' for the current version)

    Returns
    -------
        None
    """
    df = HHDataFrame(df.resample(pd.Timedelta(hours=1)).mean().interpolate(method="time"))
    heating_load = df["heating_power"].to_numpy(dtype=np.float32)
    assert isinstance(df.index, pd.DatetimeIndex), "Must be a DatetimeIndex-ed dataframe"
    new_df = pd.DataFrame(
        {
            "HoY": [hour_of_year(ts) for ts in df.index],
            "Date": df.index.strftime("%d-%b"),
            "Start Time": df.index.strftime("%H:%M"),
            "HLoad1": heating_load,
            "HLoad2": np.zeros_like(heating_load),
            "HLoad3": np.zeros_like(heating_load),
            "HLoad4": np.zeros_like(heating_load),
        }
    )
    new_df.to_csv(fname, index=False)


def to_airtemp_csv(df: WeatherDataFrame, fname: os.PathLike | str = "CSVAirtemp.csv") -> None:
    """
    Output hourly external temperature data to a CSV.

    Does the date formatting and hour-of-year calculation required for EPOCH.

    Parameters
    ----------
    df
        Dataframe, ideally from Demand Ninja, with a 'temp' column and a datetime index.
    fname
        Name of the file to write to (should be 'CSVRGen.csv' for the current version)

    Returns
    -------
        None
    """
    df = WeatherDataFrame(df.resample(pd.Timedelta(hours=1)).mean().interpolate(method="time"))
    assert isinstance(df.index, pd.DatetimeIndex), "Must be a DatetimeIndex-ed dataframe"
    new_df = pd.DataFrame(
        {
            "HoY": [hour_of_year(ts) for ts in df.index],
            "Date": df.index.strftime("%d-%b"),
            "Start Time": df.index.strftime("%H:%M"),
            "Air-temp": df["temp"],
        }
    )
    new_df.to_csv(fname, index=False)
