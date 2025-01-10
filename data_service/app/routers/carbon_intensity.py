"""
Carbon Itensity endpoints, including generation and getting.

Carbon intensity is a measure of kg CO2 e / kWh for electrical power used, and
varies over time as the grid changes.
"""

import datetime
import itertools
import logging
import uuid

import aiometer
import numpy as np
import pandas as pd
import pydantic
from fastapi import APIRouter, HTTPException

from ..dependencies import DatabaseDep, DatabasePoolDep, HTTPClient, HttpClientDep
from ..internal.utils import hour_of_year
from ..models.carbon_intensity import CarbonIntensityMetadata, EpochCarbonEntry
from ..models.core import DatasetIDWithTime, SiteIDWithTime

router = APIRouter()


async def fetch_carbon_intensity(
    client: HTTPClient,
    postcode: str | None,
    timestamps: tuple[pydantic.AwareDatetime, pydantic.AwareDatetime],
    use_regional: bool = True,
    interpolate: bool = False,
) -> list[dict[str, float | datetime.datetime | None]]:
    """
    Fetch a single lot of data from the carbon itensity API.

    This is in its own (rather ugly) function to allow the rate limiter to function.
    Will return a `forecast` carbon itensity and a breakdown if using regional, or an actual if not.

    Parameters
    ----------
    client
        HTTPX AsyncClient that we re-use between connections

    postcode
        The entire postcode for this site with inbound and outbound codes split by a space (e.g. `SW1 1AA`).

    timestamps
        A (start_ts, end_ts) pairing for the time period we want to check. Should be within 14 days of each other.

    use_regional
        Whether to use regional carbon itensity data or national

    interpolate
        Whether to interpolate to half hourly gaps in this function (leave False if you do so elsewhere)

    Returns
    -------
    results
        A list of carbon intensity readings and their times.
    """
    fetch_start_ts, fetch_end_ts = timestamps
    if isinstance(fetch_start_ts, pd.Timestamp):
        fetch_start_ts = fetch_start_ts.to_pydatetime()
    if isinstance(fetch_end_ts, pd.Timestamp):
        fetch_end_ts = fetch_end_ts.to_pydatetime()

    if fetch_start_ts == fetch_end_ts:
        return []
    start_ts_str = fetch_start_ts.isoformat()
    end_ts_str = fetch_end_ts.isoformat()

    if use_regional:
        if postcode is None:
            raise HTTPException(400, "Got postcode=None but also use_regional=True, which is invalid.")
        postcode_out = postcode.strip().split(" ")[0]
        ci_url = f"https://api.carbonintensity.org.uk/regional/intensity/{start_ts_str}/{end_ts_str}/postcode/{postcode_out}"
    else:
        ci_url = f"https://api.carbonintensity.org.uk/intensity/{start_ts_str}/{end_ts_str}"
    response = await client.get(ci_url)
    if not response.status_code == 200:
        raise HTTPException(400, f"{ci_url} returned `{response.text}`")
    data = response.json()
    results: list[dict[str, float | datetime.datetime | None]] = []
    subdata = data["data"]
    if "data" in subdata:
        # Sometimes we get a nested object one deep, especially for regional data
        subdata = subdata["data"]

    seen_keys = set()
    for item in subdata:
        entry = {
            "start_ts": pd.to_datetime(item["from"]),
            "end_ts": pd.to_datetime(item["to"]),
            "forecast": item["intensity"].get("forecast", float("NaN")),
            "actual": item["intensity"].get("actual", float("NaN")),
        }
        for fuel_data in item.get("generationmix", []):
            entry[fuel_data["fuel"]] = fuel_data["perc"] / 100.0
        if fetch_start_ts <= entry["start_ts"] and entry["end_ts"] <= fetch_end_ts:
            results.append(entry)
            seen_keys.update(entry.keys())
    seen_keys.remove("start_ts")
    seen_keys.remove("end_ts")
    results = sorted(results, key=lambda x: x["start_ts"])
    if not interpolate:
        return results

    new_times = pd.date_range(fetch_start_ts, fetch_end_ts, freq=pd.Timedelta(minutes=30), inclusive="left")
    interpolated_data = {}
    for key in seen_keys:
        xs = (new_times - fetch_start_ts).total_seconds().to_numpy()
        xp = np.asarray([
            (item["start_ts"] - fetch_start_ts).total_seconds()
            for item in results
            if item.get(key) is not None and np.isfinite(item[key])
        ])
        yp = np.asarray([item[key] for item in results if item.get(key) is not None and np.isfinite(item[key])])
        # print(key, xs, xp, yp)
        if len(xp) == 0 or len(yp) == 0:
            interpolated_vals = np.full_like(xp, np.nan)
        else:
            interpolated_vals = np.interp(xs, xp, yp)
        interpolated_data[key] = interpolated_vals

    interpolated_results = [
        {
            "start_ts": time,
            "end_ts": time + pd.Timedelta(minutes=30),
            **{key: interpolated_data[key][i] for key in seen_keys if len(interpolated_data[key]) > i},
        }
        for i, time in enumerate(new_times)
    ]
    return interpolated_results


@router.post("/generate-grid-co2", tags=["co2", "generate"])
async def generate_grid_co2(
    params: SiteIDWithTime, pool: DatabasePoolDep, http_client: HttpClientDep
) -> CarbonIntensityMetadata:
    """
    Get a grid CO2 carbon intensity from the National Grid API.

    If this is for a site where we have a stored postcode, it'll look up
    the regional generation mix for that specific region. If not, we'll just use the national mix.

    For the regional mix, we will get a `forecast` carbon itensity and maybe a regional breakdown into
    fuel sources. For the national mix, we'll get a `forecast` and an `actual`.

    This can be slow -- the rate limiting for the API is aggressive, so it
    takes approximately 1 second per 2 weeks of data.

    Parameters
    ----------
    *params*
        A JSON body containing `{"site_id":..., "start_ts":..., "end_ts":...}

    Returns
    -------
    *metadata*
        Metadata about the grid CO2 information we've just put into the database.
    """
    use_regional = True

    async with pool.acquire() as conn:
        postcode = await conn.fetchval(
            r"""
            SELECT
                (regexp_match(address, '[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}'))[1]
            FROM client_info.site_info
            WHERE site_id = $1""",
            params.site_id,
        )
    if postcode is None:
        logging.warning(f"No postcode found for {params.site_id}, using National data.")
        use_regional = False

    all_data: list[dict[str, float | datetime.datetime | None]] = []

    time_pairs: list[tuple[pydantic.AwareDatetime, pydantic.AwareDatetime]]
    if params.end_ts - params.start_ts >= pd.Timedelta(days=14):
        time_pairs = list(
            itertools.pairwise([
                *list(pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(days=13))),
                params.end_ts,
            ])
        )
    else:
        time_pairs = [(params.start_ts, params.end_ts)]

    async with aiometer.amap(
        lambda ts_pair: fetch_carbon_intensity(client=http_client, postcode=postcode, timestamps=ts_pair, use_regional=True),
        time_pairs,
        max_at_once=1,
        max_per_second=1,
    ) as results:
        async for result in results:
            all_data.extend(result)

    if not all_data:
        raise HTTPException(400, "Failed to get grid CO2 data.")
    metadata: dict[str, uuid.UUID | datetime.datetime | str | bool] = {
        "dataset_id": uuid.uuid4(),
        "created_at": datetime.datetime.now(datetime.UTC),
        "data_source": "api.carbonintensity.org.uk",
        "is_regional": use_regional,
        "site_id": params.site_id,
    }

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO
                    carbon_intensity.metadata (
                        dataset_id,
                        created_at,
                        data_source,
                        is_regional,
                        site_id)
                VALUES ($1, $2, $3, $4, $5)""",
                metadata["dataset_id"],
                metadata["created_at"],
                metadata["data_source"],
                metadata["is_regional"],
                metadata["site_id"],
            )

            await conn.executemany(
                """
                INSERT INTO
                    carbon_intensity.grid_co2 (
                        dataset_id,
                        start_ts,
                        end_ts,
                        forecast,
                        actual,
                        gas,
                        coal,
                        biomass,
                        nuclear,
                        hydro,
                        imports,
                        other,
                        wind,
                        solar
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                    )""",
                zip(
                    [metadata["dataset_id"] for _ in all_data],
                    [item["start_ts"] for item in all_data],
                    [item["end_ts"] for item in all_data],
                    [item.get("forecast") for item in all_data],
                    [item.get("actual") for item in all_data],
                    [item.get("gas") for item in all_data],
                    [item.get("coal") for item in all_data],
                    [item.get("biomass") for item in all_data],
                    [item.get("nuclear") for item in all_data],
                    [item.get("hydro") for item in all_data],
                    [item.get("imports") for item in all_data],
                    [item.get("other") for item in all_data],
                    [item.get("wind") for item in all_data],
                    [item.get("solar") for item in all_data],
                    strict=False,
                ),
            )
    return CarbonIntensityMetadata(
        **metadata  # type: ignore
    )


@router.post("/get-grid-co2", tags=["co2", "get"])
async def get_grid_co2(params: DatasetIDWithTime, conn: DatabaseDep) -> list[EpochCarbonEntry]:
    """
    Get a specific grid carbon itensity dataset that we generated with `generate-grid-co2`.

    The carbon itensity is measured in gCO2e / kWh. We get a forecast carbon intensity if
    this dataset was originally regional, and an actual carbon itensity if it was national.

    For regional carbon itensity readings, we also get a breakdown by generation source.
    The columns `["gas", "coal", "biomass", "nuclear", "hydro", "imports", "wind", "solar", "other"]`
    represent the fraction of total generation that came from that specific source (as calculated by
    National Grid).

    Parameters
    ----------
    *request*
        Internal FastAPI request object

    *params*
        Database ID for a specific grid CO2 set, and the timestamps you're interested in.

    Returns
    -------
    *carbon_itensity_entries*
        A list of JSONed carbon intensity entries, maybe forecast or maybe actual.
    """
    res = await conn.fetch(
        """
        SELECT
            start_ts, forecast, actual
        FROM carbon_intensity.grid_co2
        WHERE dataset_id = $1
        AND $2 <= start_ts
        AND end_ts <= $3
        ORDER BY start_ts ASC""",
        params.dataset_id,
        params.start_ts,
        params.end_ts,
    )
    carbon_df = pd.DataFrame.from_records(res, index="start_ts", columns=["start_ts", "forecast", "actual"], coerce_float=True)
    carbon_df.index = pd.to_datetime(carbon_df.index)

    # TODO (2025-01-09 MHJB): fix this awful pandas repeated interpolation, reindexing and resampling, it's a mess
    carbon_df = carbon_df.resample(pd.Timedelta(minutes=30)).max().infer_objects(copy=False).interpolate(method="time")
    carbon_df = carbon_df.reindex(
        pd.DatetimeIndex(pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="left"))
    )

    carbon_df["GridCO2"] = carbon_df["actual"].astype(float).fillna(carbon_df["forecast"].astype(float))
    carbon_df["GridCO2"] = carbon_df["GridCO2"].interpolate(method="time")
    return [
        EpochCarbonEntry(Date=ts.strftime("%d-%b"), HourOfYear=hour_of_year(ts), StartTime=ts.strftime("%H:%M"), GridCO2=val)
        for ts, val in zip(carbon_df.index, carbon_df["GridCO2"], strict=True)
    ]
