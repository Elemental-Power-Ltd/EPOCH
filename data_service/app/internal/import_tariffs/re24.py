"""
Import Tariffs from RE24, an AlchemAI partner.

RE24 offer wholesale or power purchase tariffs, and are developing an API to get them.
"""

import datetime

import httpx
import pandas as pd
from fastapi import HTTPException

from ...epl_secrets import get_secrets_environment
from ...models.import_tariffs import GSPEnum
from .octopus_agile import DISTRIBUTION_REGION_FACTORS, PEAK_REGION_FACTORS, wholesale_to_agile


async def get_re24_wholesale_tariff(
    start_ts: datetime.datetime,
    end_ts: datetime.datetime,
    http_client: httpx.AsyncClient,
    region_code: GSPEnum = GSPEnum.C,
) -> pd.DataFrame:
    """
    Get a synthetic Agile tariff by querying wholesale prices from RE24, and applying the Agile algorithm.

    This takes the Nordpool day-ahead hourly prices and multiplies them by some factor (approximately 2), with
    an extra bit for prices in peak times.

    Parameters
    ----------
    start_ts
        Earliest timestamp to create the tariff for
    end_ts
        Latest timestamp to create the tariff for
    region_code
        Letter region code for different localised pricing structures (Grid Supply Point)

    Returns
    -------
    pd.DataFrame
        Half hourly Agile-like costs in UTC time.
    """

    def datetime_to_re24_format(dt: datetime.datetime) -> str:
        """
        Format a datetime in a way that RE24 are happy with.

        RE24 don't accept timezoned dates, and are slightly fussy about their input format.
        We localise to UTC and strip the +00:00, then replace with a "Z".

        Parameters
        ----------
        dt
            Datetime object (ideally with timezone)

        Returns
        -------
        str
            Formatted string for the RE24 API.
        """
        return dt.astimezone(datetime.UTC).replace(microsecond=0, tzinfo=None).isoformat() + "Z"

    assert end_ts > start_ts, "Timestamps provided in wrong order"
    assert start_ts > datetime.datetime(year=2024, month=4, day=1, tzinfo=datetime.UTC), "Start timestamp too far back"

    resp = await http_client.get(
        "https://api.re24.energy/v1/data/prices/nordpool",
        params={"timestampStart": datetime_to_re24_format(start_ts), "timestampEnd": datetime_to_re24_format(end_ts)},
        headers={"x-api-key": get_secrets_environment()["EP_RE24_API_KEY"]},
    )

    if resp.status_code != 200:
        # If you're here because you got a 404 No Matching Data, it's because your start timestamp is too far back.
        # Looks like they only do a year in the past?
        raise HTTPException(status_code=400, detail=f"Error from re24: {resp.status_code} - {resp.text}")

    wholesale_df = pd.DataFrame.from_records(resp.json()["data"])
    wholesale_df["timestamp"] = pd.to_datetime(wholesale_df["timestamp"])
    wholesale_df = wholesale_df.set_index("timestamp").rename(columns={"price": "cost"})
    wholesale_df["cost"] /= 10.0  # convert from £ / MWh to p / kWh

    # We do this resampling and reindexing to make sure we've got the extra half hour period at the end,
    # which the resampling alone misses.
    wholesale_hh_df = wholesale_df.resample(pd.Timedelta(minutes=30)).max()

    # note that if you've provided weird timestamps, this might behave strangely as we
    # truncate to the nearest hour to ensure that the reindexing lines up with the resampling.
    if start_ts.minute != 0 or start_ts.second != 0 or start_ts.microsecond != 0:
        start_ts = start_ts.replace(minute=0, second=0, microsecond=0)
    
    if end_ts.minute != 0 or end_ts.second != 0 or end_ts.microsecond != 0:
        end_ts = end_ts.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(minutes=30)

    wholesale_hh_df = (
        wholesale_hh_df.reindex(pd.date_range(start_ts, end_ts, freq=pd.Timedelta(minutes=30))).ffill().bfill()
    )

    wholesale_hh_df["start_ts"] = wholesale_hh_df.index
    wholesale_hh_df["end_ts"] = wholesale_hh_df.index + pd.Timedelta(minutes=30)

    return wholesale_to_agile(
        wholesale_hh_df,
        distribution_factor=DISTRIBUTION_REGION_FACTORS[region_code],
        peak_factor=PEAK_REGION_FACTORS[region_code],
    )
