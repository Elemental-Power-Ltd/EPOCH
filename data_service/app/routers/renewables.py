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
import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from ..dependencies import DatabaseDep, DatabasePoolDep, HttpClientDep, SecretsDep
from ..internal.pvgis import get_pvgis_optima, get_renewables_ninja_data
from ..models.core import MultipleDatasetIDWithTime, SiteID, dataset_id_t
from ..models.renewables import EpochRenewablesEntry, PVOptimaResult, RenewablesMetadata, RenewablesRequest

router = APIRouter()

logger = logging.getLogger("default")


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
    params: RenewablesRequest, pool: DatabasePoolDep, http_client: HttpClientDep, secrets_env: SecretsDep
) -> RenewablesMetadata:
    """
    Calculate renewables generation in kW / kWp for this site.

    This uses renewables.ninja currently, so needs relatively old timestamps (2020?).
    If you don't provide specific azimuths and tilts, then we'll calculate the optimum using PVGIS.
    Note that we store hourly data in the database as raw as we can get it from renewables.ninja.
    The get-renewables-generation function will handle the processing into EPOCH timesteps.

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
        result = await conn.fetchrow(
            """
            SELECT
                location,
                coordinates
            FROM client_info.site_info AS s
            WHERE site_id = $1
            LIMIT 1""",
            params.site_id,
        )
        if result is None:
            raise HTTPException(400, f"Did not find a location for dataset {params.site_id}.")
        location, coords = result
    if location is None or coords is None:
        raise HTTPException(400, f"Did not find a location for dataset {params.site_id}.")

    latitude, longitude = coords
    if params.azimuth is None or params.tilt is None:
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
                            start_ts,
                            end_ts,
                            solar_generation
                        )
                    VALUES (
                        $1,
                        $2,
                        $3,
                        $4)""",
                zip(
                    [metadata.dataset_id for _ in renewables_df.index],
                    renewables_df.index,
                    renewables_df.index + pd.Timedelta(hours=1),  # assume that we got consistent data from RN
                    renewables_df.pv,
                    strict=True,
                ),
            )
    return metadata


@router.post("/get-renewables-generation", tags=["get", "solar_pv"])
async def get_renewables_generation(params: MultipleDatasetIDWithTime, pool: DatabasePoolDep) -> EpochRenewablesEntry:
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
        """
        Get a single renewables dataframe and reindex it to be half hourly.

        Parameters
        ----------
        dataset_id
            The ID of teh dataset you want
        start_ts
            Earliest renewables data to get
        end_ts
            Latest renewables data to get
        db_pool
            Database pool with connections

        Returns
        -------
        Single half hourly renewables DF
        """
        async with db_pool.acquire() as conn:
            dataset = await conn.fetch(
                """
                        SELECT
                            start_ts,
                            end_ts,
                            solar_generation
                        FROM renewables.solar_pv
                        WHERE
                            dataset_id = $1
                            AND $2 <= start_ts
                            AND end_ts < $3
                        ORDER BY start_ts ASC""",
                dataset_id,
                start_ts,
                end_ts,
            )
            if not dataset:
                raise HTTPException(400, f"No data found for dataset_id={dataset_id!s} between {start_ts} and {end_ts}.")
            renewables_df = pd.DataFrame.from_records(
                dataset, columns=["start_ts", "end_ts", "solar_generation"], index="start_ts"
            )
            renewables_df = renewables_df.reindex(
                index=pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="left")
            )

            renewables_df["solar_generation"] = renewables_df["solar_generation"].interpolate(method="time").ffill().bfill()
            # Turn this into kWh per timestep instead of kW
            renewables_df["solar_generation"] *= pd.Timedelta(minutes=30) / pd.Timedelta(minutes=60)
            return renewables_df

    try:
        async with asyncio.TaskGroup() as tg:
            all_dfs = [
                tg.create_task(get_single_renewables_df(dataset_id, params.start_ts, params.end_ts, pool))
                for dataset_id in params.dataset_id
            ]
    except ExceptionGroup as ex:
        raise ex.exceptions[0] from ex

    return EpochRenewablesEntry(
        timestamps=all_dfs[0].result().index.to_list(), data=[df.result()["solar_generation"].to_list() for df in all_dfs]
    )
