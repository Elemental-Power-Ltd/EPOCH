"""Octopus API handling functions."""

import asyncio
import datetime
from typing import Any

import httpx
import pandas as pd

from ...models.import_tariffs import GSPEnum
from ..utils import RateLimiter

# Octopus limits the number of calls we can make; it isn't documented so we have to guess about this.
# "BottlecapDave" from Home Assistant suggests it's 100 / hour, but that seems stricter than what I've actually seen
OCTOPUS_RATE_LIMITER = RateLimiter(rate_limit_requests=25, rate_limit_period=60.0)


async def get_octopus_tariff(
    tariff_name: str,
    region_code: GSPEnum = GSPEnum.C,
    start_ts: datetime.datetime | None = None,
    end_ts: datetime.datetime | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> pd.DataFrame:
    """
    Get a specific Octopus Tariff from their API.

    This will check a given tariff name and region from Octopus,
    and get the data between two timestamps.
    If this is agile data you'll get half hourly readings,
    daily readings if a tracker, or only one reading if it's fixed.

    If you want all half hourly readings use `resample_to_range` afterwards.

    Parameters
    ----------
    tariff_name
        Tariff name in the Octopus DB
    region_code
        Grid Supply Point code (A-P)
    start_ts
        Earliest time in tariff to get
    end_ts
        Latest time in tariff to get
    client
        Async http client used to send requests
    rate_limit_requests
        Maximum number of requests allowed in the rate limit period
    rate_limit_period
        Time period in seconds for the rate limit

    Returns
    -------
        Dataframe with cost in p / kWh
    """
    if http_client is None:
        http_client = httpx.AsyncClient()

    async def rate_limited_request(url: str, params: dict[str, Any] | None = None) -> httpx.Response:
        """
        Make a rate-limited GET request.

        Octopus limits us to 100 calls an hour, which is much longer than
        the timeline of a given function, so we use a shared rate limiter object.
        This may take some time -- watch out if you get caught by the limiter!

        Parameters
        ----------
        url
            URL to send the get request to
        params
            Query parameters to send with your request

        Returns
        -------
        httpx.Response
            Response from the 3rd party API.
        """
        await OCTOPUS_RATE_LIMITER.acquire()
        return await http_client.get(url, params=params)

    params: dict[str, str | int] = {"page_size": 1500}
    if start_ts is not None:
        params["period_from"] = start_ts.isoformat()
    if end_ts is not None:
        params["period_to"] = end_ts.isoformat()

    tariff_metadata_resp = await rate_limited_request(f"https://api.octopus.energy/v1/products/{tariff_name}/", params=params)

    if tariff_metadata_resp.status_code != 200:
        raise ValueError(str(tariff_metadata_resp.status_code) + tariff_metadata_resp.text)

    tariff_meta = tariff_metadata_resp.json()
    # TODO (2024-10-25 MHJB): What if we don't have a tariff in this region?
    region_meta = tariff_meta["single_register_electricity_tariffs"][region_code.value]

    def extract_rates_url(region_meta: dict[str, Any]) -> str:
        for payment_method in "direct_debit_monthly", "varying", "prepayment":
            if payment_method in region_meta:
                for sub_url in region_meta[payment_method]["links"]:
                    if sub_url["rel"] == "standard_unit_rates":
                        assert isinstance(sub_url["href"], str), f"Got a non-string of type {type(sub_url['href'])} for 'href'"
                        return sub_url["href"]
        raise ValueError(f"Could not find `standard_unit_rates` in {region_meta}")

    unit_rate_url = extract_rates_url(region_meta)

    all_results = []
    while unit_rate_url:
        rates_response = await rate_limited_request(unit_rate_url, params=params)
        response_json = rates_response.json()
        unit_rate_url = response_json.get("next")
        all_results.extend(response_json.get("results", []))

    df = pd.DataFrame.from_records(all_results).rename(
        columns={"valid_from": "start_ts", "valid_to": "end_ts", "value_exc_vat": "cost"}
    )
    df["start_ts"] = pd.to_datetime(df["start_ts"], utc=True).dt.tz_convert(datetime.UTC)
    df["end_ts"] = pd.to_datetime(df["end_ts"], utc=True).dt.tz_convert(datetime.UTC)
    df = df.drop(columns=["value_inc_vat", "payment_method"]).set_index("start_ts").sort_index()
    df["start_ts"] = df.index

    return df


async def get_day_and_night_rates(tariff_name: str, region_code: GSPEnum, client: httpx.AsyncClient) -> tuple[float, float]:
    """
    Get the day and night period rates for a specific Octopus Tariff.

    This is for Economy 7 'dual register' meters, and should be available for most fixed tariffs.
    This is not for smart meters or other day/night varying tariffs like Intelligent Octopus Go.
    Those should be accessible via `get_octopus_tariff` which will act more reliably.
    The night period covers between 00:30 and 07:30 UTC, so be careful about timezones when you're using this.

    Parameters
    ----------
    tariff_name
        The name of the octopus tariff without region codes.
    region_code
        Single letter Grid Supply Point code e.g. C
    client
        httpx client used to get query the API asynchronously

    Returns
    -------
        (night_cost, day_cost) tuple in p / kWh.
    """
    base_url = f"https://api.octopus.energy/v1/products/{tariff_name}/"

    tariff_meta = await client.get(base_url)
    if not tariff_meta.status_code == 200:
        if tariff_meta.json()["detail"] == "No EnergyProduct matches the given query.":
            raise ValueError(f"{tariff_name} is not a valid tariff: {tariff_meta.json()['detail']}")
        raise ValueError(tariff_meta.text)

    try:
        region_data = tariff_meta.json()["dual_register_electricity_tariffs"][region_code.value]["direct_debit_monthly"]
    except KeyError as ex:
        raise ValueError(
            f"Tariff {tariff_name} doesn't have a key {ex}. It's either single rate only or not in this region."
        ) from ex

    links = region_data["links"]
    day_url, night_url = None, None
    for link in links:
        if link["rel"] == "day_unit_rates":
            day_url = link["href"]
        elif link["rel"] == "night_unit_rates":
            night_url = link["href"]

    if day_url is None:
        raise ValueError(f"Couldn't find 'day_unit_rates' for tariff {tariff_name}")
    if night_url is None:
        raise ValueError(f"Couldn't find 'night_unit_rates' for tariff {tariff_name}")
    async with asyncio.TaskGroup() as tg:
        night_task = tg.create_task(client.get(night_url))
        day_task = tg.create_task(client.get(day_url))

    night_results, day_results = night_task.result().json(), day_task.result().json()

    night_cost = night_results["results"][0]["value_exc_vat"]
    day_cost = day_results["results"][0]["value_exc_vat"]

    return (night_cost, day_cost)


async def get_fixed_rates(tariff_name: str, region_code: GSPEnum, client: httpx.AsyncClient) -> float:
    """
    Get the night and night period rates for a specific Octopus Tariff.

    This is for 'single registry' meters, and should be available for most fixed tariffs.
    This is not for varying tariffs like Intelligent Octopus Go, Octopus Agile or Octopus Tracker.

    Parameters
    ----------
    tariff_name
        The name of the octopus tariff without region codes.
    region_code
        Single letter Grid Supply Point code e.g. C
    client
        httpx client used to get query the API asynchronously

    Returns
    -------
        fixed_cost in p / kWh.
    """
    base_url = f"https://api.octopus.energy/v1/products/{tariff_name}/"

    tariff_meta = await client.get(base_url)
    if not tariff_meta.status_code == 200:
        if tariff_meta.json()["detail"] == "No EnergyProduct matches the given query.":
            raise ValueError(f"{tariff_name} is not a valid tariff: {tariff_meta.json()['detail']}")
        raise ValueError(tariff_meta.text)

    try:
        region_data = tariff_meta.json()["single_register_electricity_tariffs"][region_code.value]["direct_debit_monthly"]
    except KeyError as ex:
        raise ValueError(
            f"Tariff {tariff_name} doesn't have a key {ex}. It's either single rate only or not in this region."
        ) from ex

    links = region_data["links"]
    fixed_url = None
    for link in links:
        if link["rel"] == "standard_unit_rates":
            fixed_url = link["href"]

    if fixed_url is None:
        raise ValueError(f"Couldn't find 'standard_unit_rates' for tariff {tariff_name}")

    fixed_results = await client.get(fixed_url)
    if not fixed_results.status_code == 200:
        raise ValueError(fixed_results.text)

    fixed_count = fixed_results.json()["count"]
    if fixed_count != 1:
        raise ValueError(f"Got {fixed_count} entries for {tariff_name}; use `get_octopus_tariff` for agile or varying tariffs.")

    return float(fixed_results.json()["results"][0]["value_exc_vat"])
