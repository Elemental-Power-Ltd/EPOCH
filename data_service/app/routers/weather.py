import datetime
import logging
import os

import httpx
import pandas as pd
from fastapi import APIRouter, Request

from ..internal.utils import load_dotenv
from .models import WeatherRequest

router = APIRouter()


async def visual_crossing_request(location: str, start_ts: datetime.datetime, end_ts: datetime.datetime):
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
    if not isinstance(start_ts, datetime.datetime):
        raise TypeError(f"Received a date object instead of a datetime for {start_ts}")

    if not isinstance(end_ts, datetime.datetime):
        raise TypeError(f"Received a date object instead of a datetime for {end_ts}")

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
    async with httpx.AsyncClient() as client:
        req = await client.get(
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

    records = [hour for day in req.json()["days"] for hour in day["hours"]]
    for idx, rec in enumerate(records):
        records[idx]["timestamp"] = datetime.datetime.fromtimestamp(rec["datetimeEpoch"], datetime.UTC)
        del records[idx]["datetimeEpoch"]

    return records


@router.get("/get-weather")
async def get_weather(request: Request, weather_request: WeatherRequest):
    async with request.state.pgpool.acquire() as conn:
        res = await conn.fetch(
            """SELECT
                               timestamp,
                               temp,
                               humidity,
                               solarradiation,
                               windspeed,
                               pressure
                               FROM weather.visual_crossing
                               WHERE location = $1
                               AND $2 <= timestamp
                               AND timestamp < $3
                               ORDER BY timestamp ASC""",
            weather_request.location,
            weather_request.start_ts,
            weather_request.end_ts,
        )

    expected_days = {
            item.date()
            for item in pd.date_range(
                weather_request.start_ts,
                weather_request.end_ts,
                freq=pd.Timedelta(days=1),
                inclusive="left",
            )
    }
    got_days = {item["timestamp"].date() for item in res}

    missing_days = sorted(expected_days - got_days)

    if missing_days:
        logging.warning(f"Missing days between {min(missing_days)} and {max(missing_days)} for {weather_request.location}")
        vc_recs = await visual_crossing_request(
            weather_request.location,
            datetime.datetime.combine(min(missing_days), datetime.time.min, datetime.UTC),
            datetime.datetime.combine(max(missing_days), datetime.time.max, datetime.UTC),
        )
        async with request.state.pgpool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """DELETE FROM
                                    weather.visual_crossing
                                WHERE location = $1
                                AND $2 <= timestamp AND timestamp < $3""",
                    weather_request.location,
                    min(missing_days),
                    max(missing_days),
                )

                await conn.executemany(
                    """INSERT INTO weather.visual_crossing
                        (timestamp,
                        location,
                        temp,
                        humidity,
                        precip,
                        precipprob,
                        snow,
                        snowdepth,
                        windgust,
                        windspeed,
                        winddir,
                        pressure,
                        cloudcover,
                        solarradiation,
                        solarenergy) 
                        VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)""",
                    [
                        (
                            item["timestamp"],
                            weather_request.location,
                            item["temp"],
                            item["humidity"],
                            item["precip"],
                            item["precipprob"],
                            item["snow"],
                            item["snowdepth"],
                            item["windgust"],
                            item["windspeed"],
                            item["winddir"],
                            item["pressure"],
                            item["cloudcover"],
                            item["solarradiation"],
                            item["solarenergy"],
                        )
                        for item in vc_recs
                    ],
                )
            # Now re-query the data we just fetched for a consistent view
            res = await conn.fetch(
                """SELECT
                               timestamp,
                               temp,
                               humidity,
                               solarradiation,
                               windspeed,
                               pressure
                               FROM weather.visual_crossing
                               WHERE location = $1
                               AND $2 <= timestamp
                               AND timestamp < $3
                               ORDER BY timestamp ASC""",
                weather_request.location,
                weather_request.start_ts,
                weather_request.end_ts,
            )
    return res
