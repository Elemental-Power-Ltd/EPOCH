import datetime
import json
import logging
import uuid

import httpx
import pandas as pd
import pydantic
from fastapi import APIRouter, HTTPException, Request

from ..internal.pvgis import get_pvgis_optima, get_renewables_ninja_data
from ..internal.utils import hour_of_year
from ..models.core import DatasetIDWithTime
from ..models.renewables import RenewablesRequest

router = APIRouter()


@router.post("/generate-renewables-generation", tags=["generate", "solar_pv"])
async def generate_renewables_generation(
    request: Request, params: RenewablesRequest
) -> dict[str, str | datetime.datetime | pydantic.UUID4 | dict[str, float | bool]]:
    async with request.state.pgpool.acquire() as conn:
        location, (latitude, longitude) = await conn.fetchrow(
            """
            SELECT
                location,
                coordinates
            FROM client_info.site_info AS s
            WHERE site_id = $1
            LIMIT 1""",
            params.site_id,
        )
        if location is None:
            raise HTTPException(400, f"Did not find a location for dataset {params.site_id}.")

    if params.azimuth is None or params.tilt is None:
        logging.info("Got no azimuth or tilt data, so getting optima from PVGIS.")
        optimal_params = await get_pvgis_optima(latitude=latitude, longitude=longitude)
        azimuth, tilt = float(optimal_params["azimuth"]), float(optimal_params["tilt"])
    else:
        azimuth, tilt = params.azimuth, params.tilt

    try:
        renewables_df = await get_renewables_ninja_data(
            latitude=latitude, longitude=longitude, start_ts=params.start_ts, end_ts=params.end_ts, azimuth=azimuth, tilt=tilt
        )
    except httpx.ReadTimeout as ex:
        raise HTTPException(400, "Call to renewables.ninja timed out, please wait before trying again.") from ex
    if len(renewables_df) < 364 * 24:
        raise HTTPException(500, f"Could not get renewables information for {location}.")

    metadata: dict[str, str | datetime.datetime | pydantic.UUID4 | dict[str, float | bool]] = {
        "data_source": "renewables.ninja",
        "created_at": datetime.datetime.now(datetime.UTC),
        "dataset_id": uuid.uuid4(),
        "site_id": params.site_id,
        "parameters": json.dumps({"azimuth": azimuth, "tilt": tilt, "tracking": params.tracking}),
    }
    async with request.state.pgpool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO
                    renewables.metadata (
                        dataset_id,
                        site_id,
                        created_at,
                        data_source,
                        parameters)
                VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5)""",
                metadata["dataset_id"],
                metadata["site_id"],
                metadata["created_at"],
                metadata["data_source"],
                metadata["parameters"],
            )

            await conn.executemany(
                """INSERT INTO
                        renewables.solar_pv (
                            dataset_id,
                            timestamp,
                            solar_generation
                        )
                    VALUES (
                        $1,
                        $2,
                        $3)""",
                zip(
                    [metadata["dataset_id"] for _ in renewables_df.index],
                    renewables_df.index,
                    renewables_df.pv,
                    strict=True,
                ),
            )
    return metadata


@router.post("/get-renewables-generation", tags=["get", "solar_pv"])
async def get_renewables_generation(request: Request, params: DatasetIDWithTime) -> list:
    async with request.state.pgpool.acquire() as conn:
        dataset = await conn.fetch(
            """
                SELECT
                    timestamp,
                    solar_generation
                FROM renewables.solar_pv
                WHERE
                    dataset_id = $1
                    AND $2 <= timestamp
                    AND timestamp < $3
                ORDER BY timestamp ASC""",
            params.dataset_id,
            params.start_ts,
            params.end_ts,
        )
    renewables_df = pd.DataFrame.from_records(dataset, columns=["timestamp", "solar_generation"], index="timestamp")
    renewables_df.index = pd.to_datetime(renewables_df.index)
    assert isinstance(renewables_df.index, pd.DatetimeIndex), "Renewables dataframe must have a DatetimeIndex"
    renewables_df["Date"] = renewables_df.index.strftime("%d-%b")
    renewables_df["StartTime"] = renewables_df.index.strftime("%H:%M")
    renewables_df["HourOfYear"] = renewables_df.index.map(hour_of_year)
    renewables_df = renewables_df.rename(columns={"solar_generation": "RGen1"})
    return renewables_df.to_dict(orient="records")
