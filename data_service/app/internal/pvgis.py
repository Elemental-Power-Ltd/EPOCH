"""
Functions for getting photovolatic data.
"""

import datetime
import json

import pandas as pd
import requests


def get_pvgis_data(
    lat: float,
    lon: float,
    start_year: datetime.datetime | int,
    end_year: datetime.datetime | int,
) -> pd.DataFrame:
    """
    Get solar data from the PVGIS service, and put it into a handy pandas dataframe.

    The Photo-Voltaic Geographic Information System is an EU source of useful solar data.
    They also provide PV power output calculations!

    Don't use this more than 30 times per second or they'll throttle you.
    The data are approximately 3 years behind, and you can only get yearly chunks.

    The PV output has PVGIS calculate optimal alignment / tilt of the panels for
    ease of calculation.

    Parameters
    ----------
    lat
        Latitude of the site you're interested in
    lon
        Longitude of the site you're interested in
    start_year
        First year of data to receive (inclusive)
    end_year
        Last year of data to receive (inclusive)

    Returns
    -------
        pandas dataframe, with columns [P,Gb(i),Gd(i),Gr(i),H_sun,T2m,WS10m,reconstructed]
    """
    if isinstance(start_year, datetime.datetime):
        start_year = start_year.year
    if isinstance(end_year, datetime.datetime):
        end_year = end_year.year

    base_url = "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"

    # Check here for documentation on each of these values:
    # https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/getting-started-pvgis/api-non-interactive-service_en # noqa
    params: dict[str, str | float | int] = {
        "outputformat": "json",
        "browser": int(False),
        "lat": lat,
        "lon": lon,
        "peakpower": 1,
        "loss": 0.14,
        "pvcalculation": int(True),
        "optimalinclination": int(True),
        "optimalangles": int(True),
        "startyear": int(start_year),
        "endyear": int(end_year),
        "raddatabase": "PVGIS-SARAH2",
        "components": int(True),
        "pvtechchoice": "crystSi",
    }

    req = requests.get(
        base_url,
        params=params,
    )
    try:
        df = pd.DataFrame.from_records(req.json()["outputs"]["hourly"])
    except KeyError as ex:
        raise RuntimeError(req.json()) from ex
    except json.JSONDecodeError as ex:
        raise RuntimeError(req.text) from ex
    df["timestamp"] = pd.to_datetime(df["time"], format="%Y%m%d:%H%M", utc=True) - pd.Timedelta(minutes=10)
    df["reconstructed"] = df["Int"].astype(bool)
    return df.set_index("timestamp").drop(columns=["time", "Int"])
