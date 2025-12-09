"""
Endpoints for weather data.

Weather data is slightly different to the other datasets, as it will more often be re-used between sites.
As such, weather is stored by a `location`, which is often the nearest town.
We use VisualCrossing or OpenMeteo as the source of all weather data currently.
If you don't have a VisualCrossing API key, then we've added OpenMeteo for the open source release.

Weather data by Open-Meteo.com

"""

import datetime
import functools
import itertools
import json
import logging

import aiometer
import httpx
import pandas as pd
import pydantic
from fastapi import APIRouter

from app.dependencies import DatabasePoolDep, HTTPClient, HttpClientDep, SecretsDep
from app.epl_secrets import get_secrets_environment
from app.internal.utils import RateLimiter, split_into_sessions
from app.models.weather import WeatherDataProvider, WeatherDatasetEntry, WeatherRequest

router = APIRouter()

# This is used for book-keeping of the temporary weather tables
WEATHER_TEMP_IDX = 0

# We batch requests and use aiometer.amap for a single request, but this is a higher
# level rate limit just to make sure we're not being silly.
WEATHER_RATE_LIMIT = RateLimiter(rate_limit_requests=10, rate_limit_period=datetime.timedelta(seconds=1))


async def visual_crossing_request(
    location: str,
    start_ts: datetime.datetime | datetime.date,
    end_ts: datetime.datetime | datetime.date,
    http_client: HTTPClient,
    api_key: str | None = None,
) -> list[dict[str, pydantic.AwareDatetime | float]]:
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
        Clips to UTC midnight if a date if provided.
    end_ts
        Latest timestamp (preferably UTC) to get weather for. Rounds to next hour.
        Clips to UTC midnight if a date if provided.

    Returns
    -------
        raw response from VisualCrossing, with no sanity checking.
    """
    if isinstance(start_ts, datetime.date):
        start_ts = datetime.datetime.combine(start_ts, datetime.time.min, datetime.UTC)
    if isinstance(end_ts, datetime.date):
        end_ts = datetime.datetime.combine(end_ts, datetime.time.min, datetime.UTC)

    if api_key is None:
        # This can still fail if no key was provided
        api_key = get_secrets_environment().get("VISUAL_CROSSING_API_KEY")

    if api_key is None:
        raise ValueError("Tried to get VisualCrossing data but had no API key.")
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
        "dniradiation",
        "difradiation",
    ]

    async def get_single_result(
        in_location: str,
        in_client: httpx.AsyncClient,
        api_key: str,
        ts_pair: tuple[pd.Timestamp, pd.Timestamp] | tuple[datetime.datetime, datetime.datetime],
    ) -> httpx.Response:
        """
        Get a single batch of data from VisualCrossing.

        Your ts_pair should be chosen so as not to request more than about 10000 records (approx 1 year)
        It is your responsibility to parse the response and make sure that it's legit.

        Returns
        -------
        raw httpx response
        """
        return await in_client.get(
            (
                "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
                + f"/{in_location}/{int(ts_pair[0].timestamp())}/{int(ts_pair[1].timestamp())}"
            ),
            params={
                "key": api_key,
                "include": "hours",
                "unitGroup": "metric",
                "timezone": "Z",  # We want UTC
                "lang": "uk",
                "elements": ",".join(desired_columns),
            },
        )

    records = []
    # Segment the query to not overload VisualCrossing.
    # They recommend requesting no more than 10,000 rows at a time, and splitting the query up.
    # so iterate over (ts, ts + 9999h) pairs until we reach the end (thankfully Pandas makes that easy)

    # There is however a risk that we'll have to re-sort the list at the end and remove duplicates.
    segment_timestamps = [
        item.to_pydatetime()
        for item in pd.date_range(start_ts, end_ts, freq=pd.Timedelta(hours=4999), inclusive="left").tolist()
    ]
    if segment_timestamps[-1] != end_ts:
        segment_timestamps += [end_ts]

    ts_pairs = list(itertools.pairwise(segment_timestamps))
    logger = logging.getLogger("default")
    logger.info(f"Requesting {len(ts_pairs)} batches between {start_ts} and {end_ts} for {location}.")
    async with aiometer.amap(
        functools.partial(get_single_result, location, http_client, api_key),
        ts_pairs,
        max_at_once=1 if getattr(http_client, "DO_RATE_LIMIT", True) else None,
        max_per_second=1 if getattr(http_client, "DO_RATE_LIMIT", True) else None,
    ) as results:
        async for req in results:
            try:
                raw_json = req.json()
            except json.decoder.JSONDecodeError as ex:
                raise ValueError(f"Could not decode JSON from VisualCrossing: `{req.text}`") from ex
            data = [hour for day in raw_json["days"] for hour in day["hours"]]
            for idx, rec in enumerate(data):
                data[idx]["timestamp"] = datetime.datetime.fromtimestamp(rec["datetimeEpoch"], datetime.UTC)
                del data[idx]["datetimeEpoch"]
            records.extend(data)

    # This is our cheeky trick to only select unique timestamps (we can't use the usual sorted(set(...)) idiom as
    # the dict results are unhashable), and avoids having to construct a Pandas dataframe to do all this work.
    # We also filter out any that don't meet our requirements.
    record_dict = {x["timestamp"]: x for x in records if start_ts <= x["timestamp"] < end_ts}
    return [record_dict[ts] for ts in sorted(record_dict.keys())]


async def open_meteo_request(
    latitude: float,
    longitude: float,
    start_ts: datetime.datetime | datetime.date,
    end_ts: datetime.datetime | datetime.date,
    http_client: HTTPClient,
    api_key: str | None = None,
) -> list[dict[str, pydantic.AwareDatetime | float]]:
    """
    Get a weather history as a raw response from VisualCrossing.

    This sets some sensible defaults for the VisualCrossing API call.
    Be careful as it may be slow if you request lots of data.

    Parameters
    ----------
    latitude
        GPS coordinates for the location
    longitude
        GPS coordinates for the location
    start_ts
        Earliest timestamp (preferably UTC) to get weather for. Rounds to previous hour.
        Clips to UTC midnight if a date if provided.
    end_ts
        Latest timestamp (preferably UTC) to get weather for. Rounds to next hour.
        Clips to UTC midnight if a date if provided.

    Returns
    -------
        raw response from VisualCrossing, with no sanity checking.
    """
    if isinstance(start_ts, datetime.date):
        start_ts = datetime.datetime.combine(start_ts, datetime.time.min, datetime.UTC)
    if isinstance(end_ts, datetime.date):
        end_ts = datetime.datetime.combine(end_ts, datetime.time.min, datetime.UTC)

    if api_key is None:
        # This can still fail if no key was provided
        api_key = get_secrets_environment().get("OPEN_METEO_API_KEY")

    desired_columns = [
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "surface_pressure",
        "cloud_cover",
        "direct_normal_irradiance",
        "diffuse_radiation",
        "terrestrial_radiation",
    ]

    NAME_MAPPING = {
        "temperature_2m": "temp",
        "relative_humidity_2m": "humidity",
        "wind_speed_10m": "windspeed",
        "surface_pressure": "pressure",
        "cloud_cover": "cloudcover",
        "direct_normal_irradiance": "dniradiation",
        "diffuse_radiation": "difradiation",
        "terrestrial_radiation": "solarradiation",
    }

    async def get_single_result(
        in_lat: float,
        in_lon: float,
        in_client: httpx.AsyncClient,
        api_key: str | None,
        ts_pair: tuple[pd.Timestamp, pd.Timestamp] | tuple[datetime.datetime, datetime.datetime],
    ) -> httpx.Response:
        """
        Get a single batch of data from OpenMeteo.

        Your ts_pair should be chosen so as not to request more than about 10000 records (approx 1 year)
        It is your responsibility to parse the response and make sure that it's legit.

        Returns
        -------
        raw httpx response
        """
        params: dict[str, str | float] = {
            "latitude": in_lat,
            "longitude": in_lon,
            "start_date": ts_pair[0].date().isoformat(),
            "end_date": ts_pair[1].date().isoformat(),
            "hourly": ",".join(desired_columns),
            "timeformat": "iso8601",
            "temperature_unit": "celsius",
            "wind_speed_unit": "ms",  # holdover from visualcrossing, sorry!
        }
        if api_key is not None:
            params["apikey"] = api_key
        return await in_client.get(
            ("https://archive-api.open-meteo.com/v1/archive"),
            params=params,
        )

    records = []
    # Segment the query to not overload VisualCrossing.
    # They recommend requesting no more than 10,000 rows at a time, and splitting the query up.
    # so iterate over (ts, ts + 9999h) pairs until we reach the end (thankfully Pandas makes that easy)

    # There is however a risk that we'll have to re-sort the list at the end and remove duplicates.
    segment_timestamps = [
        item.to_pydatetime()
        for item in pd.date_range(start_ts, end_ts, freq=pd.Timedelta(hours=4999), inclusive="left").tolist()
    ]
    if segment_timestamps[-1] != end_ts:
        segment_timestamps += [end_ts]

    ts_pairs = list(itertools.pairwise(segment_timestamps))
    logger = logging.getLogger("default")
    logger.info(f"Requesting {len(ts_pairs)} batches between {start_ts} and {end_ts} for {latitude} and {longitude}.")
    async with aiometer.amap(
        functools.partial(get_single_result, latitude, longitude, http_client, api_key),
        ts_pairs,
        max_at_once=2 if getattr(http_client, "DO_RATE_LIMIT", True) else None,
        max_per_second=10 if getattr(http_client, "DO_RATE_LIMIT", True) else None,
    ) as results:
        async for req in results:
            try:
                raw_json = req.json()
            except json.decoder.JSONDecodeError as ex:
                raise ValueError(f"Could not decode JSON from OpenMeteo: `{req.text}`") from ex
            hours = raw_json["hourly"]
            for idx, timestamp in enumerate(hours["time"]):
                rec = {NAME_MAPPING.get(col, col): hours[col][idx] for col in desired_columns}
                rec["timestamp"] = datetime.datetime.fromisoformat(timestamp)
                rec["timestamp"] = rec["timestamp"].replace(tzinfo=datetime.UTC)
                records.append(rec)

    # This is our cheeky trick to only select unique timestamps (we can't use the usual sorted(set(...)) idiom as
    # the dict results are unhashable), and avoids having to construct a Pandas dataframe to do all this work.
    # We also filter out any that don't meet our requirements.
    record_dict = {x["timestamp"]: x for x in records if start_ts <= x["timestamp"] < end_ts}
    return [record_dict[ts] for ts in sorted(record_dict.keys())]


@router.post("/get-visual-crossing")
async def get_visual_crossing(
    weather_request: WeatherRequest, http_client: HttpClientDep, secrets_env: SecretsDep
) -> list[dict[str, pydantic.AwareDatetime | float]]:
    """
    Get the raw data from VisualCrossing for a specific location between two timestamps.

    This will not do any database caching; use `/get-weather` for that.
    This will segment your query into multiple requests to avoid overloading VC.

    Parameters
    ----------
    WeatherRequest
        location, start_ts and end_ts pairs.

    Returns
    -------
    weather_dataset_entries
        List of weather dataset entries, sorted and with duplicates removed
    """
    return await visual_crossing_request(
        location=weather_request.location,
        start_ts=weather_request.start_ts,
        end_ts=weather_request.end_ts,
        http_client=http_client,
        api_key=secrets_env.get("VISUAL_CROSSING_API_KEY"),
    )


async def open_meteo_geocode(location: str, http_client: HttpClientDep) -> tuple[float, float]:
    """
    Turn a location string (usually a town name) into a lat, lon pair using OpenMeteo's geocoding API.

    Note that this might get the wrong location: be careful if you're looking up a "Newport", for example.
    Careful that you comply with the terms of the OpenMeteo API.

    Parameters
    ----------
    location
        Name of nearest town
    http_client
        Async connection pool to send requests to OpenMeteo with

    Returns
    -------
    latitude, longitude
        WS84 coordinates of this site, generally to not many sig figs (but that's OK for weather!)
    """
    response = await http_client.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1, "language": "en", "format": "json", "countryCode": "GB"},
    )
    if not response.is_success:
        raise ValueError(f"Bad geocoding response: {response.text}")
    data = response.json()["results"][0]
    return float(data["latitude"]), float(data["longitude"])


@router.post("/get-open-meteo")
async def get_open_meteo(
    weather_request: WeatherRequest, http_client: HttpClientDep, secrets_env: SecretsDep
) -> list[dict[str, pydantic.AwareDatetime | float]]:
    """
    Get the raw data from VisualCrossing for a specific location between two timestamps.

    This will not do any database caching; use `/get-weather` for that.
    This will segment your query into multiple requests to avoid overloading VC.

    Parameters
    ----------
    WeatherRequest
        location, start_ts and end_ts pairs.

    Returns
    -------
    weather_dataset_entries
        List of weather dataset entries, sorted and with duplicates removed
    """
    if weather_request.latitude is None or weather_request.longitude is None:
        weather_request.latitude, weather_request.longitude = await open_meteo_geocode(weather_request.location, http_client)
    return await open_meteo_request(
        latitude=weather_request.latitude,
        longitude=weather_request.longitude,
        start_ts=weather_request.start_ts,
        end_ts=weather_request.end_ts,
        http_client=http_client,
        api_key=secrets_env.get("OPEN_METEO_API_KEY"),
    )


@router.post("/get-weather")
async def get_weather(
    weather_request: WeatherRequest, pool: DatabasePoolDep, http_client: HttpClientDep
) -> list[WeatherDatasetEntry]:
    """
    Get the weather for a specific location between two timestamps.

    This will first attempt to grab the data from our PostgreSQL database, and if that fails,
    it will grab the data from VisualCrossing (and cache that). Be warned that this can result in
    an external API call, which could be slow or expensive.

    Parameters
    ----------
    weather_request
        Details about the weather you want to fetch, including where and when (and the provider, if applicable)
    pool
        Database connection pool to write into
    http_client
        HTTP Connection pool to get data with

    Returns
    -------
    list[WeatherDatasetEntry]
        Weather data in hourly increments at this site (maybe from the DB?)
    """
    # request only the days first so we can check if any data are missing
    res = await pool.fetch(
        """
        SELECT DISTINCT
            timestamp::date as date
        FROM weather.visual_crossing
        WHERE location = $1
        AND $2 <= timestamp
        AND timestamp <= $3
        ORDER BY date ASC""",
        weather_request.location,
        weather_request.start_ts,
        # There's a <= in here to prevent missing out the final day of a given group
        weather_request.end_ts,
    )

    expected_days = {
        item.date()
        for item in pd.date_range(
            weather_request.start_ts,
            # This missing second is to make sure we don't try to get the date for the last day
            weather_request.end_ts - pd.Timedelta(seconds=1),
            freq=pd.Timedelta(days=1),
            inclusive="left",
        )
    }
    got_days = {item["date"] for item in res}

    missing_days = sorted(expected_days - got_days)

    logger = logging.getLogger(__name__)
    for missing_session in split_into_sessions(missing_days, datetime.timedelta(days=1)):
        logger.warning(f"Missing days between {min(missing_session)} and {max(missing_session)} for {weather_request.location}")

        session_min_ts = datetime.datetime.combine(min(missing_session), datetime.time.min, datetime.UTC)
        session_max_ts = datetime.datetime.combine(max(missing_session), datetime.time.max, datetime.UTC) + datetime.timedelta(
            days=1
        )
        # There's another rate limiter within the `visual_crossing_request` function, this just slows down parallel requests
        # to prevent trouble.
        await WEATHER_RATE_LIMIT.acquire()
        HAS_VC_API_KEY = get_secrets_environment().get("VISUAL_CROSSING_API_KEY") is not None
        if weather_request.provider == WeatherDataProvider.Auto:
            if HAS_VC_API_KEY:
                vc_recs = await visual_crossing_request(
                    weather_request.location,
                    session_min_ts,
                    session_max_ts,
                    http_client=http_client,
                )
            else:
                if weather_request.latitude is None or weather_request.longitude is None:
                    weather_request.latitude, weather_request.longitude = await open_meteo_geocode(
                        weather_request.location, http_client
                    )
                vc_recs = await open_meteo_request(
                    latitude=weather_request.latitude,
                    longitude=weather_request.longitude,
                    start_ts=session_min_ts,
                    end_ts=session_max_ts,
                    http_client=http_client,
                )
        elif weather_request.provider == WeatherDataProvider.VisualCrossing:
            if not HAS_VC_API_KEY:
                raise ValueError("Specified VisualCrossing as weather data provider but no API key, try OpenMeteo.")
            vc_recs = await visual_crossing_request(
                weather_request.location,
                session_min_ts,
                session_max_ts,
                http_client=http_client,
            )
        elif weather_request.provider == WeatherDataProvider.OpenMeteo:
            if weather_request.latitude is None or weather_request.longitude is None:
                raise ValueError(f"Using OpenMeteo but wasn't given lat/lon for {weather_request.location}")
            vc_recs = await open_meteo_request(
                latitude=weather_request.latitude,
                longitude=weather_request.longitude,
                start_ts=session_min_ts,
                end_ts=session_max_ts,
                http_client=http_client,
            )
        else:
            raise ValueError(f"Unknown Weather Data provider: {weather_request.provider}")
        async with pool.acquire() as conn, conn.transaction():
            # We do this odd two-step copy because we might be writing to the cache repeatedly from two different tasks.
            # Those will show a UniqueViolationError, so we create a temporary table, copy the records over, and
            # ignore any clashes.
            # We can't use a WHERE NOT EXISTS clause because the other task might be actively writing to the table
            # as we go along, which trips us up.
            # Track unique tables by the hash of the weather request and a counting suffix.
            # If you send two identical requests from two different threads at exactly the same time,
            # you're on your own.

            global WEATHER_TEMP_IDX
            temp_suffix = str(abs(hash(weather_request.model_dump_json())))
            temp_table_name = f"weather_temp_{temp_suffix}_{WEATHER_TEMP_IDX}"
            WEATHER_TEMP_IDX += 1

            await conn.execute(f"CREATE TEMPORARY TABLE {temp_table_name} (LIKE weather.visual_crossing)")

            await conn.copy_records_to_table(
                table_name=temp_table_name,
                columns=[
                    "timestamp",
                    "location",
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
                    "dniradiation",
                    "difradiation",
                ],
                # Some of these columns are optional.
                records=[
                    (
                        item["timestamp"],
                        weather_request.location,
                        item["temp"],
                        item["humidity"],
                        item.get("precip"),
                        item.get("precipprob"),
                        item.get("snow"),
                        item.get("snowdepth"),
                        item.get("windgust"),
                        item["windspeed"],
                        item.get("winddir"),
                        item["pressure"],
                        item["cloudcover"],
                        item["solarradiation"],
                        item.get("solarenergy"),
                        item["dniradiation"],
                        item["difradiation"],
                    )
                    for item in vc_recs
                ],
            )
            await conn.execute(f"""
                    INSERT INTO weather.visual_crossing
                    (SELECT
                        t.*
                    FROM {temp_table_name} AS t)
                    ON CONFLICT (location, timestamp) DO NOTHING""")
            await conn.execute(f"DROP TABLE {temp_table_name}")

    # Now re-query the data we just fetched for a consistent view
    res = await pool.fetch(
        """
        SELECT
            timestamp,
            temp,
            humidity,
            solarradiation,
            windspeed,
            pressure,
            dniradiation,
            difradiation,
            cloudcover
        FROM weather.visual_crossing
        WHERE location = $1
        AND $2 <= timestamp
        AND timestamp < $3
        ORDER BY timestamp ASC""",
        weather_request.location,
        weather_request.start_ts,
        weather_request.end_ts,
    )

    return [
        WeatherDatasetEntry(
            timestamp=item["timestamp"],
            temp=item["temp"],
            windspeed=item["windspeed"],
            humidity=item["humidity"],
            pressure=item["pressure"],
            solarradiation=item["solarradiation"],
            dniradiation=item["dniradiation"],
            difradiation=item["difradiation"],
            cloudcover=item["cloudcover"],
        )
        for item in res
    ]
