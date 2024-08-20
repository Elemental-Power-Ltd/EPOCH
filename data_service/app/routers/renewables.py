"""
Endpoints for solar PV generation.

This includes getting optimal positions (tilt, azimuth etc) and the predicted solar gain at a site.
In future, it may include wind etc.
"""

import datetime
import json
import logging
import uuid

import httpx
import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from ..dependencies import DatabaseDep, HttpClientDep
from ..internal.pvgis import get_pvgis_optima, get_renewables_ninja_data
from ..internal.utils import hour_of_year
from ..models.core import DatasetIDWithTime, SiteID
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
    params: RenewablesRequest, conn: DatabaseDep, http_client: HttpClientDep
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
async def get_renewables_generation(params: DatasetIDWithTime, conn: DatabaseDep) -> list[EpochRenewablesEntry]:
    """
    Get a pre-generated dataset of renewables generation load.

    You can generate the expected outputs for a given solar PV array with the `generate-renewables-generation`
    endpoint. This function retrieves that from the database, and returns it in an EPOCH friendly format.

    Currently only supports a single solar PV generation column, but will be expanded in future.

    Watch out for the timestamps, which can return no data if they don't overlap with the time of interest.

    Parameters
    ----------
    *request*
        Internal FastAPI request object

    *params*
        Renewables PV dataset ID and timestamps of interest.

    Returns
    -------
    epoch_renewables_entries
        List of EPOCH friendly renewables generation.
    """
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
    if not dataset:
        raise HTTPException(400, f"No data found for {params.dataset_id} between {params.start_ts} and {params.end_ts}.")
    renewables_df = pd.DataFrame.from_records(dataset, columns=["timestamp", "solar_generation"], index="timestamp")
    renewables_df.index = pd.to_datetime(renewables_df.index)
    assert isinstance(renewables_df.index, pd.DatetimeIndex), "Renewables dataframe must have a DatetimeIndex"
    renewables_df["Date"] = renewables_df.index.strftime("%d-%b")
    renewables_df["StartTime"] = renewables_df.index.strftime("%H:%M")
    renewables_df["HourOfYear"] = renewables_df.index.map(hour_of_year)
    renewables_df = renewables_df.rename(columns={"solar_generation": "RGen1"})
    return [
        EpochRenewablesEntry(Date=item["Date"], StartTime=item["StartTime"], HourOfYear=item["HourOfYear"], RGen1=item["RGen1"])
        for item in renewables_df.to_dict(orient="records")
    ]
