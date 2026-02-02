"""
Import Tariffs from RE24, an AlchemAI partner.

RE24 offer wholesale or power purchase tariffs, and are developing an API to get them.
"""

import datetime
from pathlib import Path

import httpx
import pandas as pd
from fastapi import HTTPException

from app.epl_secrets import get_secrets_environment
from app.internal.import_tariffs.octopus_agile import DISTRIBUTION_REGION_FACTORS, PEAK_REGION_FACTORS, wholesale_to_agile
from app.models.core import SiteIDWithTime
from app.models.import_tariffs import GSPEnum


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

    returned_json = resp.json()
    if "data" not in returned_json and returned_json.get("message") == "Forbidden":
        raise ValueError(f"Error from RE24: {returned_json['message']}. Check your API key?")
    if "data" not in returned_json and "message" in returned_json:
        raise ValueError(f"Didn't get data in JSON from RE24: {returned_json['message']}")
    wholesale_df = pd.DataFrame.from_records(returned_json["data"])
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

    wholesale_hh_df = wholesale_hh_df.reindex(pd.date_range(start_ts, end_ts, freq=pd.Timedelta(minutes=30))).ffill().bfill()

    wholesale_hh_df["start_ts"] = wholesale_hh_df.index
    wholesale_hh_df["end_ts"] = wholesale_hh_df.index + pd.Timedelta(minutes=30)

    return wholesale_to_agile(
        wholesale_hh_df,
        distribution_factor=DISTRIBUTION_REGION_FACTORS[region_code],
        peak_factor=PEAK_REGION_FACTORS[region_code],
    )


async def get_re24_approximate_ppa(
    params: SiteIDWithTime,
    grid_tariff: pd.DataFrame | float,
    wind_cost: float = 17.776,
    solar_cost: float = 17.991,
    profile_path: Path = Path("app", "internal", "import_tariffs", "re24_generation_profiles.csv"),
) -> pd.DataFrame:
    """
    Get an approximation of what a client would pay for a PPA via RE24.

    The PPA approximation algorithm takes the following steps:
    - Get a likely generation profile for a local grid scale solar array via solar irradiance
    - Get a likely generation profile for a local grid scale wind farm via local wind speed
    - At each half hour timestep, mark the generation assets as "producing" or "not producing"
    - Mark the grid as always producing
    - Get half hourly timeseries of energy purchase costs from each asset
    - At each timestep, select the cheapest producing asset as the half hourly cost

    This approximation will be poor if the local weather is a poor match for the weather at the generation locations,
    or if we're buying a significant fraction of the assets generation.

    Parameters
    ----------
    params
        Site ID, start time and end time
    grid_tariff
        (float): A fixed cost to pay at all times for grid imports in p / kWh
        (pd.DataFrame): time series of costs at half hourly intervals in p / kWh
    wind_cost
        (float): Fixed cost representing LCOE for wind PPA in p / kWh
    solar_cost
        (float): FIxed cost representing LCOE for solar PPA in p / kWh

    Returns
    -------
    pd.DataFrame
        Dataframe with columns start_ts, end_ts and cost in p / kWh
    """
    # Load the generation profiles and normalise them to being a fraction of total generation
    # (do this before resampling or we'll get artefacts if we've resampled to the summer or winter)
    raw_weather_df = pd.read_csv(profile_path)
    raw_weather_df.index = pd.to_datetime(raw_weather_df["timestamp"], format="ISO8601")
    raw_weather_df["wind_generation"] /= raw_weather_df["wind_generation"].max()
    raw_weather_df["solar_generation"] /= raw_weather_df["solar_generation"].max()

    # Resample picking the relevant day of the year. This isn't a perfect resampling algorithm (weather is different per year!)
    # but it'll do for now. Interpolate in case we have an extra day this year.
    grouped_weather = {
        (idx.dayofyear, idx.time()): (wind_generation, solar_generation)
        for idx, wind_generation, solar_generation in zip(
            raw_weather_df.index, raw_weather_df["wind_generation"], raw_weather_df["solar_generation"], strict=False
        )
    }
    new_timestamps = pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="left")
    weather_df = pd.DataFrame.from_dict(
        {ts: grouped_weather.get((ts.dayofyear, ts.time()), (float("NaN"), float("NaN"))) for ts in new_timestamps},
        orient="index",
        columns=["wind_generation", "solar_generation"],
    )
    weather_df = weather_df.interpolate(method="time").ffill().bfill()

    # These are the fractional cutoffs in generation power.
    # Presume that if there's less wind or solar than this, then we can't buy any
    # from the generator at this timestamp.
    WIND_THRESH = 0.05
    SOLAR_THRESH = 0.05
    is_generating = pd.DataFrame(
        index=weather_df.index,
        data={
            "wind_generation": weather_df.wind_generation > WIND_THRESH,
            "solar_generation": weather_df.solar_generation > SOLAR_THRESH,
            "grid": True,  # there's always grid data available!
        },
    )
    if isinstance(grid_tariff, pd.DataFrame):
        costs = pd.DataFrame(index=weather_df.index, data={"wind": wind_cost, "solar": solar_cost})
        costs["grid"] = grid_tariff
    else:
        costs = pd.DataFrame(index=weather_df.index, data={"wind": wind_cost, "solar": solar_cost, "grid": grid_tariff})
    tariff = pd.DataFrame(costs.mask(~is_generating, other=float("inf")).min(axis=1), columns=["cost"])
    tariff = pd.DataFrame(costs.mask(~is_generating.to_numpy(), other=float("inf")).min(axis=1), columns=["cost"])
    tariff["start_ts"] = tariff.index
    tariff["end_ts"] = tariff.index + pd.Timedelta(minutes=30)
    return tariff
