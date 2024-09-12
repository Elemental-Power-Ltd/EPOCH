"""Lazy endpoints for bundling everything together."""

import asyncio
import datetime
import logging
import uuid

from fastapi import APIRouter, HTTPException

from ..dependencies import DatabaseDep, DatabasePoolDep, HttpClientDep, VaeDep
from ..internal.site_manager.site_manager import fetch_all_input_data
from ..models.client_data import SiteDataEntries
from ..models.core import DatasetEntry, DatasetIDWithTime, DatasetTypeEnum, MultipleDatasetIDWithTime, SiteID, SiteIDWithTime
from ..models.electricity_load import ElectricalLoadRequest
from ..models.heating_load import HeatingLoadRequest
from ..models.import_tariffs import TariffRequest
from ..models.optimisation import RemoteMetaData
from ..models.renewables import RenewablesRequest
from .carbon_intensity import generate_grid_co2
from .electricity_load import generate_electricity_load
from .heating_load import generate_heating_load
from .import_tariffs import generate_import_tariffs, select_arbitrary_tariff
from .renewables import generate_renewables_generation

router = APIRouter()


@router.post("/generate-all")
async def generate_all(
    params: SiteIDWithTime, pool: DatabasePoolDep, http_client: HttpClientDep, vae: VaeDep
) -> dict[DatasetTypeEnum, DatasetEntry]:
    """
    Run all dataset generation tasks for this site.

    This includes heating load, grid CO2, electrical load, carbon intensity and solar PV.
    Currently it uses a simple tariff that covers a long period of time, and optimal solar PV parameters.
    You almost certainly want the timestamps to be 2021 or 2022 so we can use renewables.ninja data, and relatively recent
    tariff data.

    Parameters
    ----------
    params
        SiteIDWithTime, including two relatively far back timestamps for Renewables Ninja to use.

    Returns
    -------
    datasets
        Dataset Type: Dataset Entry mapping, including UUIDs under the 'dataset_id' key that you can retrieve from `get-*`.
    """
    async with pool.acquire() as conn:
        datasets = await list_latest_datasets(SiteID(site_id=params.site_id), conn=conn)

    if DatasetTypeEnum.GasMeterData not in datasets:
        raise HTTPException(400, f"No gas meter data for {params.site_id}.")
    if DatasetTypeEnum.ElectricityMeterData not in datasets:
        raise HTTPException(400, f"No electrical meter data for {params.site_id}.")
    heating_load_dataset = datasets[DatasetTypeEnum.GasMeterData]
    elec_meter_dataset = datasets[DatasetTypeEnum.ElectricityMeterData]
    tariff_name = await select_arbitrary_tariff(params, http_client=http_client)

    async with asyncio.TaskGroup() as tg:
        heating_load_response = tg.create_task(
            generate_heating_load(
                HeatingLoadRequest(dataset_id=heating_load_dataset.dataset_id, start_ts=params.start_ts, end_ts=params.end_ts),
                pool=pool,
                http_client=http_client,
            )
        )
        grid_co2_response = tg.create_task(generate_grid_co2(params, pool=pool, http_client=http_client))

        import_tariff_response = tg.create_task(
            generate_import_tariffs(
                TariffRequest(site_id=params.site_id, tariff_name=tariff_name, start_ts=params.start_ts, end_ts=params.end_ts),
                pool=pool,
                http_client=http_client,
            )
        )

        renewables_response = tg.create_task(
            generate_renewables_generation(
                RenewablesRequest(
                    site_id=params.site_id, start_ts=params.start_ts, end_ts=params.end_ts, azimuth=None, tilt=None
                ),
                pool=pool,
                http_client=http_client,
            )
        )

        elec_response = tg.create_task(
            generate_electricity_load(
                ElectricalLoadRequest(dataset_id=elec_meter_dataset.dataset_id, start_ts=params.start_ts, end_ts=params.end_ts),
                pool=pool,
                http_client=http_client,
                vae=vae,
            )
        )

    return {
        DatasetTypeEnum.HeatingLoad: DatasetEntry(
            dataset_id=heating_load_response.result().dataset_id,
            dataset_type=DatasetTypeEnum.HeatingLoad,
            created_at=heating_load_response.result().created_at,
        ),
        DatasetTypeEnum.CarbonIntensity: DatasetEntry(
            dataset_id=grid_co2_response.result().dataset_id,
            dataset_type=DatasetTypeEnum.CarbonIntensity,
            created_at=grid_co2_response.result().created_at,
        ),
        DatasetTypeEnum.ImportTariff: DatasetEntry(
            dataset_id=import_tariff_response.result().dataset_id,
            dataset_type=DatasetTypeEnum.ImportTariff,
            created_at=import_tariff_response.result().created_at,
        ),
        DatasetTypeEnum.RenewablesGeneration: DatasetEntry(
            dataset_id=renewables_response.result().dataset_id,
            dataset_type=DatasetTypeEnum.RenewablesGeneration,
            created_at=renewables_response.result().created_at,
        ),
        DatasetTypeEnum.ElectricityMeterData: datasets[DatasetTypeEnum.ElectricityMeterData],
        DatasetTypeEnum.ElectricityMeterDataSynthesised: DatasetEntry(
            dataset_id=elec_response.result().dataset_id,
            dataset_type=DatasetTypeEnum.ElectricityMeterDataSynthesised,
            created_at=elec_response.result().created_at,
        ),
        DatasetTypeEnum.ASHPData: DatasetEntry(
            dataset_id=uuid.uuid4(),
            dataset_type=DatasetTypeEnum.ASHPData,
            created_at=datetime.datetime.now(tz=datetime.UTC),
        ),
    }


@router.post("/list-latest-datasets", tags=["db", "list"])
async def list_latest_datasets(site_id: SiteID, conn: DatabaseDep) -> dict[DatasetTypeEnum, DatasetEntry]:
    """
    Get the most recent datasets of each type for this site.

    This endpoint is the main one you'd want to call if you are interested in running EPOCH.
    Note that you may still need to call `generate-*` if the datasets in here are too old, or
    not listed at all.

    Parameters
    ----------
    site_id
        The ID of the site you are interested in

    Returns
    -------
        A {dataset_type: most recent dataset entry} dictionary for each available dataset type.
    """
    res = await conn.fetch(
        """
    WITH cdm AS (
     SELECT u.dataset_id,
    u.created_at,
    u.dataset_type,
    u.site_id
   FROM ( SELECT metadata.dataset_id,
            metadata.created_at,
                CASE
                    WHEN metadata.fuel_type = 'elec'::text THEN 'ElectricityMeterData'::text
                    WHEN metadata.fuel_type = 'gas'::text THEN 'GasMeterData'::text
                    ELSE NULL::text
                END AS dataset_type,
            metadata.site_id
           FROM client_meters.metadata
           WHERE is_synthesised = False
        UNION ALL
        SELECT
            metadata.dataset_id,
            metadata.created_at,
            'ElectricityMeterDataSynthesised'::text AS dataset_type,
            metadata.site_id
           FROM client_meters.metadata
           WHERE is_synthesised = True AND fuel_type = 'elec'
        UNION ALL
         SELECT metadata.dataset_id,
            metadata.created_at,
            'ImportTariff'::text AS dataset_type,
            metadata.site_id
           FROM tariffs.metadata
        UNION ALL
         SELECT metadata.dataset_id,
            metadata.created_at,
            'RenewablesGeneration'::text AS dataset_type,
            metadata.site_id
           FROM renewables.metadata
        UNION ALL
         SELECT metadata.dataset_id,
            metadata.created_at,
            'HeatingLoad'::text AS dataset_type,
            metadata.site_id
           FROM heating.metadata
        UNION ALL
         SELECT metadata.dataset_id,
            metadata.created_at,
            'CarbonIntensity'::text AS dataset_type,
            metadata.site_id
           FROM carbon_intensity.metadata
        UNION ALL
         SELECT gen_random_uuid() AS dataset_id,
            now() AS created_at,
            'ASHPData'::text AS dataset_type,
            si.site_id
           FROM ( SELECT DISTINCT site_info.site_id
                   FROM client_info.site_info) si) u
  ORDER BY u.created_at)

    SELECT
        cdm.dataset_id,
        cdm.dataset_type,
        cdm.site_id,
        cdm.created_at
    FROM cdm
    INNER JOIN (
        SELECT
            MAX(created_at) AS max_created_at,
            dataset_type,
            site_id
        FROM
            cdm
        WHERE site_id = $1
        GROUP BY dataset_type, site_id
    ) AS mc ON
        cdm.site_id = mc.site_id
        AND mc.max_created_at = cdm.created_at
        AND cdm.dataset_type = mc.dataset_type
    """,
        site_id.site_id,
    )

    return {
        DatasetTypeEnum(item["dataset_type"]): DatasetEntry(
            dataset_id=item["dataset_id"], dataset_type=DatasetTypeEnum(item["dataset_type"]), created_at=item["created_at"]
        )
        for item in res
    }


@router.post("/get-latest-datasets", tags=["db", "get"])
async def get_latest_datasets(site_data: RemoteMetaData, pool: DatabasePoolDep) -> SiteDataEntries:
    """
    Get the most recent dataset entries of each type for this site.

    This endpoint combines a call to /list-latest-datasets with each of the /get endpoints for those datasets

    Parameters
    ----------
    site_data
        A specification for the required site data.

    Returns
    -------
        The site data with full time series for each data source
    """
    logging.info("Getting latest dataset list")

    async with pool.acquire() as conn:
        site_data_info = await list_latest_datasets(SiteID(site_id=site_data.site_id), conn=conn)

    site_data_ids: dict[DatasetTypeEnum, DatasetIDWithTime | MultipleDatasetIDWithTime] = {}
    for dataset_name, dataset_metadata in site_data_info.items():
        if dataset_name == DatasetTypeEnum.HeatingLoad or dataset_name == DatasetTypeEnum.RenewablesGeneration:
            site_data_ids[dataset_name] = MultipleDatasetIDWithTime(
                dataset_id=[dataset_metadata.dataset_id],
                start_ts=site_data.start_ts,
                end_ts=site_data.start_ts + datetime.timedelta(hours=8760),
            )
        else:
            site_data_ids[dataset_name] = DatasetIDWithTime(
                dataset_id=dataset_metadata.dataset_id,
                start_ts=site_data.start_ts,
                end_ts=site_data.start_ts + datetime.timedelta(hours=8760),
            )

    logging.info("Fetching latest datasets")
    all_datasets = await fetch_all_input_data(site_data_ids, pool=pool)

    return all_datasets
