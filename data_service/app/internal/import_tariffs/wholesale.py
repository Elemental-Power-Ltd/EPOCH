"""Functions for getting and processing raw wholesale electricity price data."""

import datetime
import itertools
import logging

import httpx
import pandas as pd

logger = logging.getLogger("default")


async def get_wholesale_costs(
    start_ts: datetime.datetime, end_ts: datetime.datetime, client: httpx.AsyncClient
) -> pd.DataFrame:
    """
    Get wholesale electricity costs from the Elexon balancing market API.

    This function can be relatively slow, so be careful (as the API is relatively limited).
    The provided data should be half hourly with gaps forwards and backwards filled as appropriate.
    We only return data from the APXMIDP data stream as that's most reliable.

    Parameters
    ----------
    start_ts
        The earliest time to retrieve wholesale costs for
    end_ts
        The latest time to retrieve wholesale costs for.
    client
        Async HTTP client to send requests

    Returns
    -------
    Pandas dataframe with datetime index (billing window start times) and costs (p / kWh)
    """
    dates = pd.date_range(start_ts, end_ts, freq=pd.Timedelta(days=7)).to_list()

    if dates[-1] != end_ts:
        dates += [pd.Timestamp(end_ts)]

    all_data = []
    for s_ts, e_ts in itertools.pairwise(dates):
        base_url = "https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index"
        params = {"from": s_ts.isoformat(), "to": e_ts.isoformat(), "format": "json", "dataProviders": "APXMIDP"}
        resp = await client.get(base_url, params=params)
        if not resp.status_code == 200:
            logger.warning("Could not get data from Elexon for {resp.url}")
            continue
        all_data.extend(resp.json()["data"])
    df = pd.DataFrame.from_records(all_data)
    df = df.pivot_table(columns="dataProvider", index="startTime", values="price")
    df.index = pd.to_datetime(df.index, format="ISO8601")
    df = df.ffill().bfill()
    df = df[["APXMIDP"]].rename(columns={"APXMIDP": "cost"})
    return df
