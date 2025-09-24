"""Functions for getting photovolatic data."""

import asyncio
import datetime
import json
import logging
import random

import fastapi
import httpx
import numpy as np
import pandas as pd
from fastapi import HTTPException

from ..epl_secrets import get_secrets_environment
from ..models.renewables import PvgisMountingSystemEnum, PVOptimaResult
from .utils import RateLimiter, check_latitude_longitude

logger = logging.getLogger(__name__)

# This is for the burst rate limit of 1/second
RN_SLOW_LIMITER = RateLimiter(rate_limit_requests=50, rate_limit_period=datetime.timedelta(hours=1))
RN_BURST_LIMITER = RateLimiter(rate_limit_requests=6, rate_limit_period=datetime.timedelta(seconds=60))
PVGIS_RATE_LIMITER = RateLimiter(rate_limit_requests=25, rate_limit_period=datetime.timedelta(seconds=1))


async def get_pvgis_optima(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    tracking: bool = False,
) -> PVOptimaResult:
    """
    Use PVGIS to calculate optimal tilts and azimuths for a solar setup at this location.

    The PVGIS calculator itself is a bit poor, but they provide this nice utility optimiser.
    Returns a default UK-friendly optimum if we couldn't contact PVGIS.

    Parameters
    ----------
    client
        HTTP connection pool used to contact PVGIS
    latitude
        Latitude of this site in degrees
    longitude
        Longitude of this site in degrees
    tracking
        Whether we install tracking panels or not (mostly no)

    Returns
    -------
        Dictionary with optima and some useful parameters calculated by PVGIS
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

    if getattr(client, "DO_RATE_LIMIT", True):
        await PVGIS_RATE_LIMITER.acquire()
    res = await client.get(base_url, params=params)

    assert res.status_code == 200, f"Failed to get PVGIS optima: {res.status_code}, {res.text}"
    data = res.json()

    mounting_system = "tracking" if tracking else "fixed"

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
    client: httpx.AsyncClient,
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
    if getattr(client, "DO_RATE_LIMIT", True):
        await PVGIS_RATE_LIMITER.acquire()
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
    client: httpx.AsyncClient,
    azimuth: float | None = None,
    tilt: float | None = None,
    tracking: bool = False,
    api_key: str | None = None,
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
    if api_key is None:
        api_key = get_secrets_environment()["RENEWABLES_NINJA_API_KEY"]

    BASE_URL = "https://www.renewables.ninja/api/data/pv"

    if not check_latitude_longitude(latitude=latitude, longitude=longitude):
        raise ValueError("Latitude and longitude provided the wrong way round.")
    if azimuth is None or tilt is None:
        optimal_params = await get_pvgis_optima(client=client, latitude=latitude, longitude=longitude, tracking=tracking)
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

    if getattr(client, "DO_RATE_LIMIT", True):
        await RN_SLOW_LIMITER.acquire()
        await RN_BURST_LIMITER.acquire()
    # If we're working in a threaded environment, then we can sometimes thrash renewables.ninja if we've picked up
    # multiple RenewablesRequest jobs at once.
    # To avoid that, we jitter these requests slightly.
    await asyncio.sleep(random.uniform(1.0, 10.0))
    req = await client.get(BASE_URL, params=params, headers={"Authorization": f"Token {api_key}"})

    if req.status_code == 400 and "short-term burst limit" in req.text:
        # The headline jitter didn't work, so let's take another crack at it later.
        await asyncio.sleep(random.uniform(1.0, 10.0))
        req = await client.get(BASE_URL, params=params, headers={"Authorization": f"Token {api_key}"})

    try:
        renewables_df = pd.DataFrame.from_dict(req.json(), columns=["electricity"], orient="index").rename(
            columns={"electricity": "pv"}
        )
    except json.JSONDecodeError as ex:
        raise fastapi.HTTPException(
            400, f"Decoding renewables.ninja data failed. Got `{req.text}` instead of valid JSON."
        ) from ex
    renewables_df.index = pd.to_datetime(renewables_df.index.astype(float) * 1e6)
    assert isinstance(renewables_df.index, pd.DatetimeIndex), "Renewables dataframe must have a datetime index"
    renewables_df.index = renewables_df.index.tz_localize(datetime.UTC)
    within_timestamps_mask = np.logical_and(
        renewables_df.index >= pd.Timestamp(start_ts), renewables_df.index < pd.Timestamp(end_ts)
    )
    masked_df: pd.DataFrame = renewables_df[within_timestamps_mask]
    return masked_df


async def get_renewables_ninja_wind_data(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    start_ts: datetime.datetime,
    end_ts: datetime.datetime,
    turbine: str = "Vestas V90 2000",
    height: float = 80.0,
    api_key: str | None = None,
) -> pd.DataFrame:
    """
    Request wind turbine information from renewables.ninja.

    This takes in a location, timestamps, and some information about the wind turbine.
    There is a list of available turbines on renewables ninja and we'll tell you if the one you give is invalid.
    This may take a few seconds, and is relatively heavily rate limited by renewables.ninja.

    The returned dataframe is in (kw / kWp) so can be easily scaled up (it's calculated for
    a nominal 1kWp trubine).

    Parameters
    ----------
    client
        HTTP connection client for renewables ninja
    latitude
        Latitude of the site you're interested in, in degrees
    longitude
        Longitude of the site you're interested in, in degrees
    start_ts
        Earliest timestamp to get data for (usually Jan 1st)
    end_ts
        Earliest timestamp to get data for (usually Dec 31st)
    height
        Height of the wind turbine at this point above the ground in m
    turbine
        Name of the turbine you want
    api_key
        Renewables Ninja API key; if None, get one from the environment.

    Returns
    -------
        pandas dataframe with timestamp index and column "wind"
    """
    if api_key is None:
        api_key = get_secrets_environment()["RENEWABLES_NINJA_API_KEY"]

    if not check_latitude_longitude(latitude=latitude, longitude=longitude):
        raise ValueError("Latitude and longitude provided the wrong way round.")

    async def get_valid_turbines(http_client: httpx.AsyncClient) -> frozenset[str]:
        """
        Get a list of all the valid turbines that renewables.ninja can calculate.

        A turbine is identified by a string name.

        Parameters
        ----------
        http_client
            HTTP connection client for accessing renewables.ninja

        Returns
        -------
        set of valid turbine names
        """
        if getattr(http_client, "DO_RATE_LIMIT", True):
            await RN_SLOW_LIMITER.acquire()
            await RN_BURST_LIMITER.acquire()
        rn_wind_resp = await http_client.get(
            "https://www.renewables.ninja/api/models/wind", headers={"Authorization": f"Token {api_key}"}
        )
        assert rn_wind_resp.status_code == 200, (
            "Got a bad status code from Renewables.ninja" + f" for wind model listing: {rn_wind_resp.status_code}"
        )
        rn_wind_fields = rn_wind_resp.json()["fields"]
        for field in rn_wind_fields:
            if field["id"] == "turbine":
                break
        else:
            raise ValueError("Couldn't find turbine in returned field data")
        return frozenset(item["value"] for item in field["options"])

    valid_turbines = await get_valid_turbines(client)
    if turbine not in valid_turbines:
        raise HTTPException(404, detail=f"Specified turbine {turbine} not found. Try one of {valid_turbines}")
    params: dict[str, str | float | int] = {
        "lat": latitude,
        "lon": longitude,
        "date_from": start_ts.strftime("%Y-%m-%d"),
        "date_to": end_ts.strftime("%Y-%m-%d"),
        "turbine": turbine,
        "height": height,
        "header": "false",
        "capacity": 1.0,
        "format": "json",
    }
    if getattr(client, "DO_RATE_LIMIT", True):
        await RN_SLOW_LIMITER.acquire()
        await RN_BURST_LIMITER.acquire()

    # If we're working in a threaded environment, then we can sometimes thrash renewables.ninja if we've picked up
    # multiple RenewablesRequest jobs at once.
    # To avoid that, we jitter these requests slightly.
    await asyncio.sleep(random.uniform(1.0, 10.0))
    req = await client.get(
        "https://www.renewables.ninja/api/data/wind", params=params, headers={"Authorization": f"Token {api_key}"}
    )

    if req.status_code == 400 and "short-term burst limit" in req.text:
        # The headline jitter didn't work, so let's take another crack at it later.
        await asyncio.sleep(random.uniform(1.0, 10.0))
        req = await client.get(
            "https://www.renewables.ninja/api/data/wind", params=params, headers={"Authorization": f"Token {api_key}"}
        )

    try:
        renewables_df = pd.DataFrame.from_dict(req.json(), columns=["electricity"], orient="index").rename(
            columns={"electricity": "wind"}
        )
    except json.JSONDecodeError as ex:
        raise fastapi.HTTPException(
            400, f"Decoding renewables.ninja data failed. Got {req.text} instead of valid JSON."
        ) from ex
    renewables_df.index = pd.to_datetime(renewables_df.index.astype(float) * 1e6)
    assert isinstance(renewables_df.index, pd.DatetimeIndex), "Renewables dataframe must have a datetime index"
    renewables_df.index = renewables_df.index.tz_localize(datetime.UTC)
    within_timestamps_mask = np.logical_and(
        renewables_df.index >= pd.Timestamp(start_ts), renewables_df.index < pd.Timestamp(end_ts)
    )
    masked_df: pd.DataFrame = renewables_df[within_timestamps_mask]
    return masked_df
