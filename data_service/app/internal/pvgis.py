"""
Functions for getting photovolatic data.
"""

import datetime
import json
import os

import httpx
import pandas as pd

from .utils import check_latitude_longitude, load_dotenv


async def get_pvgis_optima(latitude: float, longitude: float) -> dict[str, float | str]:
    """
    Use PVGIS to calculate optimal tilts and azimuths for a solar setup at this location.

    The PVGIS calculator itself is a bit poor, but they provide this nice utility optimiser.

    Parameters
    ----------
    latitude

    longitude

    Returns
    -------
        Dictionary with optima and some useful parameters
    """
    base_url = "https://re.jrc.ec.europa.eu/api/PVcalc"

    if not check_latitude_longitude(latitude=latitude, longitude=longitude):
        raise ValueError("Latitude and longitude provided the wrong way round.")
    params: dict[str, str | float | int] = {
        "lat": latitude,
        "lon": longitude,
        "peakpower": 1.0,
        "loss": 14,
        "browser": int(False),
        "optimalangles": int(True),
        "mountingplace": "building",
        "outputformat": "json",
        "header": int(False),
    }

    async with httpx.AsyncClient() as client:
        res = await client.get(base_url, params=params)
        data = res.json()
    solar_params = {
        "azimuth": (180 + data["inputs"]["mounting_system"]["fixed"]["azimuth"]["value"]) % 360,
        "tilt": data["inputs"]["mounting_system"]["fixed"]["slope"]["value"],
        "altitude": data["inputs"]["location"]["elevation"],
        "mounting_system": "fixed",
        "type": data["inputs"]["mounting_system"]["fixed"]["type"],
        "technology": data["inputs"]["pv_module"]["technology"],
        "data_source": data["inputs"]["meteo_data"]["radiation_db"],
    }
    return solar_params


async def get_pvgis_data(
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
    async with httpx.AsyncClient() as client:
        req = await client.get(
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


async def get_renewables_ninja_data(
    latitude: float, longitude: float, start_ts: datetime.datetime, end_ts: datetime.datetime
) -> pd.DataFrame:
    load_dotenv()
    BASE_URL = "https://www.renewables.ninja/api/data/pv"

    if not check_latitude_longitude(latitude=latitude, longitude=longitude):
        raise ValueError("Latitude and longitude provided the wrong way round.")
    optimal_params = await get_pvgis_optima(latitude, longitude)
    params: dict[str, str | float | int] = {
        "lat": latitude,
        "lon": longitude,
        "date_from": start_ts.strftime("%Y-%m-%d"),
        "date_to": end_ts.strftime("%Y-%m-%d"),
        "tracking": int(False),
        "azim": optimal_params["azimuth"],
        "tilt": optimal_params["tilt"],
        "system_loss": 0.14,
        "header": "false",
        "capacity": 1.0,
        "format": "json",
    }
    async with httpx.AsyncClient() as client:
        req = await client.get(
            BASE_URL, params=params, headers={"Authorization": f"Token {os.environ['RENEWABLES_NINJA_API_KEY']}"}
        )

    renewables_df = pd.read_json(req.text, orient="index").rename(columns={"electricity": "pv"})
    assert isinstance(renewables_df.index, pd.DatetimeIndex), "Renewables dataframe must have a datetime index"
    renewables_df.index = renewables_df.index.tz_localize(datetime.UTC)
    return renewables_df
