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

import asyncpg
import httpx
import numpy as np
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
        """SELECT coordinates FROM client_info.site_info WHERE site_id = $1 LIMIT 1""",
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
    result = await pool.fetchrow(
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
        # We can't insert "default" into the database as it isn't a real location
        # associated with a site
        renewables_location_id=params.renewables_location_id if params.renewables_location_id != "default" else None,
    )
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """INSERT INTO
                    renewables.metadata (
                        dataset_id,
                        site_id,
                        created_at,
                        data_source,
                        parameters,
                        renewables_location_id)
                VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5,
                        $6)""",
                metadata.dataset_id,
                metadata.site_id,
                metadata.created_at,
                metadata.data_source,
                json.dumps(metadata.parameters),
                metadata.renewables_location_id,
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
        dataset = await pool.fetch(
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
        renewables_df = pd.DataFrame.from_records(dataset, columns=["start_ts", "end_ts", "solar_generation"], index="start_ts")
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


async def disaggregate_electricity_dataframe(
    elec_df: pd.DataFrame,
    http_client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    azimuth: float | None = None,
    tilt: float | None = None,
    system_size: float = 1.0,
) -> pd.DataFrame:
    """
    Disaggregrate the effect of solar generation from electrical meter readings in a dataframe.

    Use this function if you want to disaggregate a set of electrical meter data before upload.
    This function will generate solar data over the time period you've got meter data for, then
    calculate how much generation there was likely to have been in that time. Then subtract that from your
    total import to get your total used.
    This keeps the granularity of the original meter dataset: if it's monthly, we'll calculate your monthly consumption.
    If it's halfhourly, we'll calculate your halfhourly consumption (but this is likely to be less accurate)

    Parameters
    ----------
    elec_df
        Dataset of the electricity readings with `start_ts`, `end_ts` and `consumption_kwh`.
    http_client
        HTTP connection client used to contact Renewables.Ninja
    latitude
        Latitude of site in degrees
    longitude
        Longitude of site in degrees
    azimuth
        Angle between the solar panels and true north in degrees. If None, we'll estimate this.
    tilt
        Angle between the solar panels and the surface normal in degrees. If None, we'll estimate this.
    system_size
        Rated size of the system in kWp

    Returns
    -------
    pd.DataFrame
        Disaggregrated electrical data with columns `consumption_kwh`, `import` and `generation`
    """
    if azimuth is None or tilt is None:
        logger.info("Got no azimuth or tilt data, so getting optima from PVGIS.")
        optimal_params = await get_pvgis_optima(latitude=latitude, longitude=longitude, client=http_client)
        azimuth, tilt = float(optimal_params.azimuth), float(optimal_params.tilt)

    renewables_df = await get_renewables_ninja_data(
        latitude=latitude,
        longitude=longitude,
        start_ts=elec_df.start_ts.min() - pd.Timedelta(hours=1),
        end_ts=elec_df.end_ts.max() + pd.Timedelta(hours=1),
        azimuth=azimuth,
        tilt=tilt,
        tracking=False,
        client=http_client,
    )
    # Convert to half hourly kWh readings
    renewables_df = renewables_df.resample(pd.Timedelta(minutes=30)).mean().interpolate(method="time").ffill()
    renewables_df["pv"] *= 0.5
    # Convert into the appropriately sized system
    renewables_df["pv"] *= system_size

    total_pv = []
    for start_ts, end_ts in zip(elec_df.start_ts, elec_df.end_ts, strict=False):
        within_mask = np.logical_and(renewables_df.index >= start_ts, renewables_df.index < end_ts)
        total_pv.append(renewables_df.loc[within_mask, "pv"].sum())

    elec_df["generation"] = total_pv
    # We've assumed that the data we've been provided is the net import / export of electricity.
    # Positive values are imports, negative values are exports
    elec_df["import"] = elec_df["consumption_kwh"].clip(0)
    elec_df["export"] = (-elec_df["consumption_kwh"]).clip(0)

    # The total consumption is then the provided net import/export plus the on-site generation
    elec_df["consumption_kwh"] += elec_df["generation"]
    return elec_df


async def disaggregate_readings(
    elec_meter_dataset_id: dataset_id_t,
    pool: asyncpg.Pool,
    http_client: httpx.AsyncClient,
    azimuth: float | None = None,
    tilt: float | None = None,
    system_size: float = 1.0,
) -> pd.DataFrame:
    """
    Disaggregrate the effect of solar generation from electrical meter readings in the database.

    Use this function if you want to disaggregate an existing set of electrical meter data.
    This function will generate solar data over the time period you've got meter data for, then
    calculate how much generation there was likely to have been in that time. Then subtract that from your
    total import to get your total used.
    This keeps the granularity of the original meter dataset: if it's monthly, we'll calculate your monthly consumption.
    If it's halfhourly, we'll calculate your halfhourly consumption (but this is likely to be less accurate)

    Parameters
    ----------
    elec_meter_dataset_id
        Dataset of the electricity meters you want us to disaggregate. We'll look up the associated site and its
        location from the metadata associated with this dataset.
    azimuth
        Angle between the solar panels and true north in degrees. If None, we'll estimate this.
    tilt
        Angle between the solar panels and the surface normal in degrees. If None, we'll estimate this.
    pool
        Database containing electrical meter readings
    http_client
        HTTP connection client used to contact Renewables.Ninja
    system_size
        Rated size of the system in kWp

    Returns
    -------
    pd.DataFrame
        Disaggregrated electrical data with columns `consumption_kwh`, `import` and `generation`
    """
    elec_dataset = await pool.fetch(
        """
        SELECT
            start_ts,
            end_ts,
            consumption_kwh
        FROM client_meters.electricity_meters
        WHERE dataset_id = $1""",
        elec_meter_dataset_id,
    )
    elec_df = pd.DataFrame.from_records(elec_dataset, columns=["start_ts", "end_ts", "consumption_kwh"])

    row = await pool.fetchrow(
        """
        SELECT
            m.site_id,
            si.coordinates
        FROM client_meters.metadata AS m
        LEFT JOIN client_info.site_info AS si
        ON m.site_id = si.site_id
        WHERE m.dataset_id = $1 AND NOT is_synthesised AND fuel_type = 'elec' LIMIT 1""",
        elec_meter_dataset_id,
    )
    site_id, (latitude, longitude) = row if row is not None else (None, (None, None))

    if site_id is None:
        raise ValueError(f"Couldn't find electricity meter metadata for {elec_meter_dataset_id}")
    if latitude is None or longitude is None:
        raise HTTPException(400, f"Did not find a location for site {site_id}.")

    return await disaggregate_electricity_dataframe(
        elec_df=elec_df,
        http_client=http_client,
        latitude=latitude,
        longitude=longitude,
        azimuth=azimuth,
        tilt=tilt,
        system_size=system_size,
    )
