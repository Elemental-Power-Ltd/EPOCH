import datetime
import functools
import itertools
import logging
import uuid

import aiometer
import httpx
import pandas as pd
import pydantic
from fastapi import APIRouter, Request

from ..models.carbon_intensity import CarbonIntensityEntry, CarbonIntensityMetadata
from ..models.core import DatasetIDWithTime, SiteIDWithTime

router = APIRouter()


@router.post("/generate-grid-co2")
async def generate_grid_co2(request: Request, params: SiteIDWithTime) -> CarbonIntensityMetadata:
    """
    Get a grid CO2 carbon intensity from the National Grid API.

    If this is for a site where we have a stored postcode, it'll look up
    the regional generation mix for that specific region.
    If not, we'll just use the annual mix.

    This can be slow -- the rate limiting for the API is aggressive, so it
    takes approximately 1 second per 2 weeks of data.

    Parameters
    ----------
    request
        FastAPI internal request object, not necessary for outside users.

    params
        A JSON body containing `{"site_id":..., "start_ts":..., "end_ts":...}

    Returns
    -------
    metadata
        Metadata about the grid CO2 information we've just put into the database."""
    use_regional = True
    async with request.state.pgpool.acquire() as conn:
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

    async def fetch(
        client: httpx.AsyncClient, postcode: str, timestamps: tuple[pydantic.AwareDatetime, pydantic.AwareDatetime]
    ) -> list[dict[str, float | None | datetime.datetime]]:
        """
        Fetch a single lot of data from
        """
        start_ts, end_ts = timestamps
        start_ts_str = start_ts.isoformat()
        end_ts_str = end_ts.isoformat()

        if use_regional:
            postcode_out = postcode.strip().split(" ")[0]
            ci_url = (
                f"https://api.carbonintensity.org.uk/regional/intensity/{start_ts_str}/{end_ts_str}/postcode/{postcode_out}"
            )
        else:
            ci_url = f"https://api.carbonintensity.org.uk/intensity/{start_ts_str}/{end_ts_str}"
        data = (await client.get(ci_url)).json()
        results = []

        if use_regional:
            data = data["data"]["data"]
        else:
            data = data["data"]
        for item in data:
            entry = {
                "start_ts": pd.to_datetime(item["from"]),
                "end_ts": pd.to_datetime(item["to"]),
                "forecast": item["intensity"].get("forecast"),
                "actual": item["intensity"].get("actual"),
            }
            for fuel_data in item.get("generationmix", []):
                entry[fuel_data["fuel"]] = fuel_data["perc"] / 100.0
            results.append(entry)
        return results

    all_data: list[dict[str, float | None | datetime.datetime]] = []

    time_pairs: list[tuple[pydantic.AwareDatetime, pydantic.AwareDatetime]]
    if params.end_ts - params.start_ts >= pd.Timedelta(days=14):
        time_pairs = list(itertools.pairwise(pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(days=13))))
    else:
        time_pairs = [(params.start_ts, params.end_ts)]

    async with httpx.AsyncClient() as client:
        async with aiometer.amap(
            functools.partial(fetch, client, postcode), time_pairs, max_at_once=1, max_per_second=1
        ) as results:
            async for result in results:
                all_data.extend(result)

    metadata: dict[str, uuid.UUID | datetime.datetime | str | bool] = {
        "dataset_id": uuid.uuid4(),
        "created_at": datetime.datetime.now(datetime.UTC),
        "data_source": "api.carbonintensity.org.uk",
        "is_regional": use_regional,
        "site_id": params.site_id,
    }

    async with request.state.pgpool.acquire() as conn:
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


@router.post("/get-grid-co2")
async def get_grid_co2(request: Request, params: DatasetIDWithTime) -> list[CarbonIntensityEntry]:
    async with request.state.pgpool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                start_ts, end_ts, forecast, actual, gas, coal, biomass, nuclear, hydro, imports, other, wind, solar
            FROM carbon_intensity.grid_co2
            WHERE dataset_id = $1
            AND $2 <= start_ts
            AND end_ts <= $3""",
            params.dataset_id,
            params.start_ts,
            params.end_ts,
        )
    return [CarbonIntensityEntry(**item) for item in res]
