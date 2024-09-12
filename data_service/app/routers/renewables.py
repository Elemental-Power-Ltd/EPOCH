"""
Endpoints for solar PV generation.

This includes getting optimal positions (tilt, azimuth etc) and the predicted solar gain at a site.
In future, it may include wind etc.
"""

import asyncio
import datetime
import json
import logging
import uuid

import httpx
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from ..dependencies import DatabaseDep, DatabasePoolDep, HttpClientDep
from ..internal.pvgis import get_pvgis_optima, get_renewables_ninja_data
from ..internal.utils import add_epoch_fields
from ..models.core import MultipleDatasetIDWithTime, SiteID, dataset_id_t
from ..models.renewables import EpochRenewablesEntry, PVOptimaResult, RenewablesMetadata, RenewablesRequest

router = APIRouter()


@router.post("/get-pv-optima", tags=["solar_pv", "get"])
async def get_pv_optima(request: Request, site_id: SiteID, conn: DatabaseDep) -> PVOptimaResult:
    """
    Get some optimal angles and azimuths for this specific site.

    This checks the stored latitude and longitude for the site, and will ask the EU
    PVGIS project to calculate the optimal tilt and azimuth.
    Currently assumes roof mounted and non-tracking panels.

    Parameters
    ----------
    request
        Internal FastAPI request object.
    site_id
        The internal database ID for a given site.

    Returns
    -------
    information about the optimal azimuth, tilt, and some metadata about the technologies used.
    """
    latitude, longitude = await conn.fetchval(
        """SELECT coordinates FROM client_info.site_info WHERE site_id = $1""",
        site_id.site_id,
    )
    optima = await get_pvgis_optima(latitude=latitude, longitude=longitude, client=request.state.http_client)
    return optima


@router.post("/generate-renewables-generation", tags=["generate", "solar_pv"])
async def generate_renewables_generation(
    params: RenewablesRequest, pool: DatabasePoolDep, http_client: HttpClientDep
) -> RenewablesMetadata:
    """
    Calculate renewables generation in kW / kWp for this site.

    This uses renewables.ninja currently, so needs relatively old timestamps (2020?).
    If you don't provide specific azimuths and tilts, then we'll calculate the optimum using PVGIS.

    Parameters
    ----------
    *request*
        Internal FastAPI request object
    *params*
        Details about the site and PV array. This may include azimuth and tilt, but not necessarily.

    Returns
    -------
    renewables_metadata
        Metadata about the renewables calculation we've put into the database.
    """
    async with pool.acquire() as conn:
        location, coords = await conn.fetchrow(  # type: ignore
            """
            SELECT
                location,
                coordinates
            FROM client_info.site_info AS s
            WHERE site_id = $1
            LIMIT 1""",
            params.site_id,
        )
    if location is None or coords is None:
        raise HTTPException(400, f"Did not find a location for dataset {params.site_id}.")

    latitude, longitude = coords
    if params.azimuth is None or params.tilt is None:
        logger = logging.getLogger("default")
        logger.info("Got no azimuth or tilt data, so getting optima from PVGIS.")
        optimal_params = await get_pvgis_optima(latitude=latitude, longitude=longitude, client=http_client)
        azimuth, tilt = float(optimal_params.azimuth), float(optimal_params.tilt)
    else:
        azimuth, tilt = params.azimuth, params.tilt

    try:
        renewables_df = await get_renewables_ninja_data(
            latitude=latitude,
            longitude=longitude,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            azimuth=azimuth,
            tilt=tilt,
            client=http_client,
        )
    except httpx.ReadTimeout as ex:
        raise HTTPException(400, "Call to renewables.ninja timed out, please wait before trying again.") from ex

    if len(renewables_df) < (params.end_ts - params.start_ts).total_seconds() / (60 * 60):
        raise HTTPException(500, f"Got too small a renewables dataset for {location}. Try requesting an older dataset?")

    metadata = RenewablesMetadata(
        data_source="renewables.ninja",
        created_at=datetime.datetime.now(datetime.UTC),
        dataset_id=uuid.uuid4(),
        site_id=params.site_id,
        parameters=json.dumps({"azimuth": azimuth, "tilt": tilt, "tracking": params.tracking}),
    )
    async with pool.acquire() as conn:
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
                metadata.dataset_id,
                metadata.site_id,
                metadata.created_at,
                metadata.data_source,
                json.dumps(metadata.parameters),
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
                    [metadata.dataset_id for _ in renewables_df.index],
                    renewables_df.index,
                    renewables_df.pv,
                    strict=True,
                ),
            )
    return metadata


@router.post("/get-renewables-generation", tags=["get", "solar_pv"])
async def get_renewables_generation(params: MultipleDatasetIDWithTime, pool: DatabasePoolDep) -> list[EpochRenewablesEntry]:
    """
    Get a pre-generated dataset of renewables generation load.

    You can generate the expected outputs for a given solar PV array with the `generate-renewables-generation`
    endpoint. This function retrieves that from the database, and returns it in an EPOCH friendly format.

    Currently only supports a single solar PV generation column, but will be expanded in future.

    Watch out for the timestamps, which can return no data if they don't overlap with the time of interest.

    Parameters
    ----------
    *params*
        Renewables PV dataset ID and timestamps of interest.

    Returns
    -------
    epoch_renewables_entries
        List of EPOCH friendly renewables generation.
    """

    async def get_single_renewables_df(
        dataset_id: dataset_id_t, start_ts: datetime.datetime, end_ts: datetime.datetime, db_pool: DatabasePoolDep
    ) -> pd.DataFrame:
        async with db_pool.acquire() as conn:
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
                dataset_id,
                start_ts,
                end_ts,
            )
            if not dataset:
                raise HTTPException(400, f"No data found for dataset_id={dataset_id!s} between {start_ts} and {end_ts}.")
            renewables_df = pd.DataFrame.from_records(dataset, columns=["timestamp", "solar_generation"], index="timestamp")
            renewables_df.index = pd.to_datetime(renewables_df.index)
            return renewables_df

    try:
        async with asyncio.TaskGroup() as tg:
            all_dfs = [
                tg.create_task(get_single_renewables_df(dataset_id, params.start_ts, params.end_ts, pool))
                for dataset_id in params.dataset_id
            ]
    except ExceptionGroup as ex:
        raise ex.exceptions[0] from ex
    total_df = pd.DataFrame(
        index=pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="left")
    )
    for i, df in enumerate(all_dfs, 1):  # Careful of off-by-one!
        total_df[f"RGen{i}"] = df.result()["solar_generation"]

    within_timestamps_mask = np.logical_and(params.start_ts <= total_df.index, total_df.index < params.end_ts)
    total_df = total_df[within_timestamps_mask].interpolate(method="time").ffill().bfill()
    total_df = add_epoch_fields(total_df)
    total_df = total_df.dropna()
    return [
        EpochRenewablesEntry(
            Date=item["Date"],
            StartTime=item["StartTime"],
            HourOfYear=item["HourOfYear"],
            RGen1=item["RGen1"],
            RGen2=item["RGen2"] if "RGen2" in item else None,
            RGen3=item["RGen3"] if "RGen3" in item else None,
            RGen4=item["RGen4"] if "RGen4" in item else None,
        )
        for item in total_df.to_dict(orient="records")
    ]
