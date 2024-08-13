"""Functions for getting photovolatic data."""

import datetime
import json
import os

import fastapi

from fastapi import HTTPException
import httpx
import numpy as np
import pandas as pd

from ..models.renewables import PvgisMountingSystemEnum, PVOptimaResult
from .utils import check_latitude_longitude, load_dotenv


async def get_pvgis_optima(
    latitude: float, longitude: float, tracking: bool = False, client: httpx.AsyncClient | None = None
) -> PVOptimaResult:
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
        "fixed": int(not tracking),  # PVGIS used "fixed" instead of "tracking"
        "optimalangles": int(True),
        "mountingplace": "building",
        "outputformat": "json",
        "header": int(False),
    }

    # this slightly odd construct is because we might receive a client as an argument, which we'd want to use
    # for connection pooling. However, if weren't given one we'll have to make one.
    try:
        if client is not None:
            res = await client.get(base_url, params=params)
        else:
            async with httpx.AsyncClient() as client:
                res = await client.get(base_url, params=params)
    except httpx.TimeoutException as ex:
        raise HTTPException(f"Failed to get PVGIS optima with {params} due to a timeout.") from ex
    data = res.json()

    if tracking:
        mounting_system = "tracking"
    else:
        mounting_system = "fixed"

    return PVOptimaResult(
        azimuth=(180 + data["inputs"]["mounting_system"][mounting_system]["azimuth"]["value"]) % 360,
        tilt=data["inputs"]["mounting_system"][mounting_system]["slope"]["value"],
        altitude=data["inputs"]["location"]["elevation"],
        mounting_system=PvgisMountingSystemEnum(mounting_system),
        type=data["inputs"]["mounting_system"][mounting_system]["type"],
        technology=data["inputs"]["pv_module"]["technology"],
        data_source=data["inputs"]["meteo_data"]["radiation_db"],
    )


async def get_pvgis_data(
    lat: float,
    lon: float,
    start_year: datetime.datetime | int,
    end_year: datetime.datetime | int,
    client: httpx.AsyncClient | None = None,
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
    # the slightly odd `int(bool)` format is because the API accepts ints, but really they're logical values. It's
    # to make it easier for you to read.
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

    # this slightly odd construct is because we might receive a client as an argument, which we'd want to use
    # for connection pooling. However, if weren't given one we'll have to make one.
    if client is not None:
        req = await client.get(base_url, params=params)
    else:
        async with httpx.AsyncClient() as client:
            req = await client.get(base_url, params=params)

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
    latitude: float,
    longitude: float,
    start_ts: datetime.datetime,
    end_ts: datetime.datetime,
    azimuth: float | None = None,
    tilt: float | None = None,
    tracking: bool = False,
    client: httpx.AsyncClient | None = None,
) -> pd.DataFrame:
    """
    Request solar PV information from renewables.ninja.

    This takes in a location, timestamps, and some information about the solar installation.
    If the solar installation information isn't provided, we get optima from PVGIS.
    This may take a few seconds, and is relatively heavily rate limited by renewables.ninja.

    The returned dataframe is in (kw / kWp) so can be easily scaled up (it's calculated for
    a nominal 1kWp array).

    Parameters
    ----------
    latitude

    longitude

    start_ts
        Earliest timestamp to get data for (usually Jan 1st)
    end_ts
        Earliest timestamp to get data for (usually Dec 31st)
    azimuth
        Angle of solar array from polar north, should be around 180 in the UK
    tilt
        Angle of the panels facing the sun (around 40?)
    tracking
        Whether the panels are single axis trackers (commonly False in the UK)

    Returns
    -------
        pandas dataframe with timestamp index and column "pv"
    """
    load_dotenv()
    BASE_URL = "https://www.renewables.ninja/api/data/pv"

    if not check_latitude_longitude(latitude=latitude, longitude=longitude):
        raise ValueError("Latitude and longitude provided the wrong way round.")
    if azimuth is None or tilt is None:
        optimal_params = await get_pvgis_optima(latitude, longitude, tracking)
        azimuth = float(optimal_params.azimuth)
        tilt = float(optimal_params.tilt)
    params: dict[str, str | float | int] = {
        "lat": latitude,
        "lon": longitude,
        "date_from": start_ts.strftime("%Y-%m-%d"),
        "date_to": end_ts.strftime("%Y-%m-%d"),
        "tracking": int(tracking),
        "azim": azimuth,
        "tilt": tilt,
        "system_loss": 0.14,
        "header": "false",
        "capacity": 1.0,
        "format": "json",
    }
    # this slightly odd construct is because we might receive a client as an argument, which we'd want to use
    # for connection pooling. However, if weren't given one we'll have to make one.
    if client is not None:
        req = await client.get(
            BASE_URL, params=params, headers={"Authorization": f"Token {os.environ['RENEWABLES_NINJA_API_KEY']}"}
        )
    else:
        async with httpx.AsyncClient() as aclient:
            req = await aclient.get(
                BASE_URL, params=params, headers={"Authorization": f"Token {os.environ['RENEWABLES_NINJA_API_KEY']}"}
            )

    try:
        renewables_df = pd.DataFrame.from_dict(req.json(), columns=["electricity"], orient="index").rename(
            columns={"electricity": "pv"}
        )
    except json.JSONDecodeError as ex:
        raise fastapi.HTTPException(400, "Decoding renewables.ninja data failed. Try again later.") from ex
    renewables_df.index = pd.to_datetime(renewables_df.index.astype(float) * 1e6)
    assert isinstance(renewables_df.index, pd.DatetimeIndex), "Renewables dataframe must have a datetime index"
    renewables_df.index = renewables_df.index.tz_localize(datetime.UTC)
    within_timestamps_mask = np.logical_and(renewables_df.index >= start_ts, renewables_df.index < end_ts)  # type: ignore
    return renewables_df[within_timestamps_mask]
