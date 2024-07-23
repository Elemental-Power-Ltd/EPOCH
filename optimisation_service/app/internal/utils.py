import os
import pathlib
import typing

import numpy as np
import numpy.typing as npt
import pandas as pd

from .epl_typing import FloatOrArray


def typename(x: typing.Any) -> str:
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
        raise FileNotFoundError(f"Could not find {fname} in the specified location or its parents.")

    with open(fpath, "r") as fi:
        for line in fi:
            key, value = line.strip().split("=", 1)
            os.environ[key] = value
    # turn this into a dict to prevent any trouble with weird types
    return dict(os.environ.items())


def m3_to_kwh(vol: npt.NDArray[np.float32] | pd.Series, calorific_value: float = 38.0) -> npt.NDArray[np.float32] | pd.Series:
    """
    Convert a gas reading in meters cubed to kWh.

    Parameters
    ----------
    vol
        Volume of gas consumed
    calorific_value
        Energy per unit gas in MJ. Provided on bill.

    Returns
    -------
        gas energy consumption in kWh"""
    return vol * calorific_value * 1.02264 / 3.6


def celsius_to_kelvin(temperature: float) -> float:
    """
    Convert a temperature in Celsius to one in Kelvin

    This checks that you haven't already converted it, and that it's a reasonable air temperature.

    Parameters
    ----------
    temperature
        Air temperature in celsius between -50°C and 100°C

    Returns
    -------
        Temperature in Kelvin between 223.15K and 373.15K
    """
    if isinstance(temperature, (float, int)):
        assert (
            -50 <= temperature < 100
        ), f"{temperature} out of range of likely °C values [-50, 100). Have you already converted it?"
    else:
        assert np.all(
            np.logical_and(-50 <= temperature, temperature < 100)
        ), f"{temperature} out of range of likely °C values [-50, 100). Have you already converted it?"
    return temperature + 273.15


def millibar_to_megapascal(pressure: FloatOrArray) -> FloatOrArray:
    """
    Convert an air pressure in mbar into one in MPa.

    VisualCrossing provides us with air temperatures in mbar, but
    for some equations we want it in megapascals.
    This checks that you haven't already converted it, and that it's
    a reasonable air pressure (outside this range is very bad news).

    Parameters
    ----------
    pressure
        Air pressure in mbar between 800 and 1100 mbar

    Returns
    -------
        air pressure in MPa between 0.08 and 0.11 MPa
    """
    if isinstance(pressure, (float, int)):
        assert (
            800 < pressure < 1100
        ), f"{pressure} out of range of likely mbar values [800, 1100). Have you already converted it?"
    else:
        assert np.all(
            np.logical_and(800 < pressure, pressure < 1100)
        ), f"{pressure} out of range of likely mbar values [800, 1100). Have you already converted it?"
    return pressure / 10000
