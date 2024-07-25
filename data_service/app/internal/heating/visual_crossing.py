"""
Functions for handling weather data from VisualCrossing.
"""

import datetime
import os

import httpx
import pydantic

from ..utils import load_dotenv


async def visual_crossing_request(
    location: str, start_ts: datetime.datetime, end_ts: datetime.datetime
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
