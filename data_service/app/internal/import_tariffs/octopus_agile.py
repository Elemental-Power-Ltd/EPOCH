"""Specific Octopus Agile functions, including lookup tables for regional costs and the wholesale to agile mapping."""

import datetime
import itertools

import httpx
import numpy as np
import pandas as pd

from app.models.import_tariffs import GSPEnum

DISTRIBUTION_REGION_FACTORS = {
    GSPEnum.A: 2.10,
    GSPEnum.B: 2.00,
    GSPEnum.C: 2.00,
    GSPEnum.D: 2.20,
    GSPEnum.E: 2.10,
    GSPEnum.F: 2.10,
    GSPEnum.G: 2.10,
    GSPEnum.H: 2.10,
    GSPEnum.J: 2.20,
    GSPEnum.K: 2.20,
    GSPEnum.L: 2.30,
    GSPEnum.M: 2.00,
    GSPEnum.N: 2.10,
    GSPEnum.P: 2.40,
}

PEAK_REGION_FACTORS = {
    GSPEnum.A: 13,
    GSPEnum.B: 14,
    GSPEnum.C: 12,
    GSPEnum.D: 13,
    GSPEnum.E: 12,
    GSPEnum.F: 12,
    GSPEnum.G: 12,
    GSPEnum.H: 12,
    GSPEnum.J: 12,
    GSPEnum.K: 12,
    GSPEnum.L: 11,
    GSPEnum.M: 13,
    GSPEnum.N: 13,
    GSPEnum.P: 12,
}


async def get_elexon(start_ts: datetime.datetime, end_ts: datetime.datetime, http_client: httpx.AsyncClient) -> pd.DataFrame:
    """
    Get wholesale prices from Elexon.

    These are the balancing mechanism system sell price.
    https://bmrs.elexon.co.uk/api-documentation/endpoint/balancing/pricing/market-index

    Parameters
    ----------
    start_ts
        Earliest date to get data for
    end_ts
        Latest date to get data for
    http_client
        Async connection client to query Elexon

    Returns
    -------
    pd.DataFrame
        Wholesale electrical costs
    """
    timestamps: list[datetime.datetime] = []
    prices: list[float] = []
    # We must only request 7 day periods at once
    for start, end in itertools.pairwise(pd.date_range(start_ts, end_ts, freq=pd.Timedelta(days=7))):
        response = await http_client.get(
            "https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index",
            params={
                "from": start.date().isoformat(),
                "to": end.date().isoformat(),
                "dataProviders": "APXMIDP",
                "format": "json",
            },
        )
        assert response.is_success, response.text
        data = response.json()["data"]
        timestamps.extend(datetime.datetime.fromisoformat(item["startTime"]) for item in data)
        # Convert prices into p / kWh
        prices.extend(item["price"] / 10 for item in data)
    return pd.DataFrame(index=timestamps, data={"cost": prices}).sort_index()


def wholesale_to_agile(
    wholesale_df: pd.DataFrame, distribution_factor: float = 2.0, peak_factor: float = 11, price_cap: float = 95
) -> pd.DataFrame:
    """
    Convert a set of wholesale electrical unit costs in p / kWh to an Octopus Agile Tariff.

    This uses the equation published on Octopus's blog here:
    https://octopus.energy/blog/agile-pricing-explained/
    THe distribution factors and peak factors for a given region are available in the dicts in this module.
    Note that this provides a cost without VAT, and the price cap applies pre-VAT as well.

    Parameters
    ----------
    wholesale_df
        Pandas dataframe with time series index and "cost" column in p / kWh
    distribution_factor
        Octopus's D factor which is multiplicative and probably around 2.0-2.2
    peak_factor
        Peak premium charged between 16:00 and 19:00, added on to the (D * cost)
    price_cap
        Pre-VAT price cap applied to the tariff costs (35p in 2023, 95p in 2024)

    Returns
    -------
    Pandas dataframe with "cost" column and datetime index, in p / kWh pre-VAT.
    """
    agile_df = pd.DataFrame(index=wholesale_df.index, data={"cost": wholesale_df["cost"]})
    agile_df["cost"] *= distribution_factor
    assert isinstance(agile_df.index, pd.DatetimeIndex)
    is_peak_mask = np.logical_and(agile_df.index.hour >= 16, agile_df.index.hour < 19)
    agile_df.loc[is_peak_mask, "cost"] += peak_factor
    agile_df["cost"] = np.minimum(agile_df["cost"], price_cap)
    return agile_df


async def get_elexon_wholesale_tariff(
    start_ts: datetime.datetime,
    end_ts: datetime.datetime,
    http_client: httpx.AsyncClient,
    region_code: GSPEnum = GSPEnum.C,
) -> pd.DataFrame:
    """
    Get a synthetic Agile tariff by querying wholesale prices from Elexon, and applying the Agile algorithm.

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
    assert end_ts > start_ts, "Timestamps provided in wrong order"
    assert start_ts > datetime.datetime(year=2024, month=4, day=1, tzinfo=datetime.UTC), "Start timestamp too far back"

    wholesale_hh_df = await get_elexon(start_ts, end_ts, http_client)
    wholesale_hh_df = wholesale_hh_df.resample(pd.Timedelta(minutes=30)).max()

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
