"""Lazy endpoints for bundling everything together."""

import asyncio
import datetime
import logging
import uuid

import httpx
import pydantic
from fastapi import APIRouter, HTTPException

from ..dependencies import DatabasePoolDep, HttpClientDep, SecretsDep, VaeDep
from ..internal.site_manager.site_manager import fetch_all_input_data
from ..models.client_data import SiteDataEntries
from ..models.core import DatasetEntry, DatasetIDWithTime, DatasetTypeEnum, MultipleDatasetIDWithTime, SiteID, SiteIDWithTime
from ..models.electricity_load import ElectricalLoadRequest
from ..models.heating_load import HeatingLoadRequest
from ..models.import_tariffs import SyntheticTariffEnum, TariffRequest
from ..models.optimisation import RemoteMetaData
from ..models.renewables import RenewablesRequest
from ..models.site_manager import DatasetRequest
from .carbon_intensity import generate_grid_co2
from .electricity_load import generate_electricity_load
from .heating_load import generate_heating_load
from .import_tariffs import generate_import_tariffs
from .renewables import generate_renewables_generation

router = APIRouter()

MULTIPLE_DATASET_ENDPOINTS = {DatasetTypeEnum.HeatingLoad, DatasetTypeEnum.RenewablesGeneration, DatasetTypeEnum.ImportTariff}


async def list_gas_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the gas meter datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
                SELECT
                    cm.dataset_id,
                    MAX(cm.created_at) AS created_at,
                    MIN(gm.start_ts) AS start_ts,
                    MAX(gm.end_ts) AS end_ts,
                    COUNT(*) AS num_entries,
                    AVG(end_ts - start_ts) AS resolution
                FROM client_meters.metadata AS cm
                LEFT JOIN
                    client_meters.gas_meters AS gm
                ON gm.dataset_id = cm.dataset_id
                WHERE
                    (cm.is_synthesised = false)
                    AND cm.fuel_type = 'gas'
                    AND site_id = $1
                GROUP BY
                    cm.dataset_id
                """,
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.GasMeterData,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
        )
        for item in res
    ]


async def list_elec_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the true electricity meter datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                cm.dataset_id,
                MAX(cm.created_at) AS created_at,
                MIN(em.start_ts) AS start_ts,
                MAX(em.end_ts) AS end_ts,
                COUNT(*) AS num_entries,
                AVG(end_ts - start_ts) AS resolution
            FROM client_meters.metadata AS cm
            LEFT JOIN
                client_meters.electricity_meters AS em
            ON em.dataset_id = cm.dataset_id
            WHERE
                (cm.is_synthesised = false)
                AND cm.fuel_type = 'elec'
                AND site_id = $1
            GROUP BY
                cm.dataset_id""",
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.ElectricityMeterData,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
        )
        for item in res
    ]


async def list_elec_synthesised_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the synthetic electricity datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                cm.dataset_id,
                MAX(cm.created_at) AS created_at,
                MIN(em.start_ts) AS start_ts,
                MAX(em.end_ts) AS end_ts,
                COUNT(*) AS num_entries,
                AVG(end_ts - start_ts) AS resolution
            FROM client_meters.metadata AS cm
            LEFT JOIN
                client_meters.electricity_meters_synthesised AS em
            ON em.dataset_id = cm.dataset_id
            WHERE
                (cm.is_synthesised = true)
                AND cm.fuel_type = 'elec'
                AND site_id = $1
            GROUP BY
                cm.dataset_id""",
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.ElectricityMeterDataSynthesised,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
        )
        for item in res
        if item["num_entries"] > 1  # filter out bad entries here
    ]


async def list_import_tariff_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the import tariff datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                tm.dataset_id,
                MAX(tm.created_at) AS created_at,
                MIN(te.start_ts) AS start_ts,
                MAX(te.end_ts) AS end_ts,
                COUNT(*) AS num_entries,
                (MAX(te.end_ts) - MIN(te.start_ts)) / (COUNT(*) - 1) AS resolution
            FROM tariffs.metadata AS tm
            LEFT JOIN
                tariffs.electricity AS te
            ON tm.dataset_id = te.dataset_id
            WHERE site_id = $1
            GROUP BY tm.dataset_id""",
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.ImportTariff,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
        )
        for item in res
    ]


async def list_renewables_generation_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the renewables generation (solar) datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                tm.dataset_id,
                MAX(tm.created_at) AS created_at,
                MIN(te.timestamp) AS start_ts,
                MAX(te.timestamp) AS end_ts,
                COUNT(*) AS num_entries,
                (MAX(te.timestamp) - MIN(te.timestamp)) / (COUNT(*) - 1) AS resolution
            FROM renewables.metadata AS tm
            LEFT JOIN
                renewables.solar_pv AS te
            ON tm.dataset_id = te.dataset_id
            WHERE site_id = $1
            GROUP BY tm.dataset_id""",
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.RenewablesGeneration,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
        )
        for item in res
    ]


async def list_heating_load_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the heating load datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                cm.dataset_id,
                MAX(cm.created_at) AS created_at,
                MIN(em.start_ts) AS start_ts,
                MAX(em.end_ts) AS end_ts,
                COUNT(*) AS num_entries,
                AVG(end_ts - start_ts) AS resolution
            FROM heating.metadata AS cm
            LEFT JOIN
                heating.synthesised AS em
            ON em.dataset_id = cm.dataset_id
            WHERE
                site_id = $1
            GROUP BY
                cm.dataset_id""",
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.HeatingLoad,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
        )
        for item in res
    ]


async def list_carbon_intensity_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the Carbon Intensity datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                cm.dataset_id,
                MAX(cm.created_at) AS created_at,
                MIN(em.start_ts) AS start_ts,
                MAX(em.end_ts) AS end_ts,
                COUNT(*) AS num_entries,
                AVG(end_ts - start_ts) AS resolution
            FROM carbon_intensity.metadata AS cm
            LEFT JOIN
                carbon_intensity.grid_co2 AS em
            ON em.dataset_id = cm.dataset_id
            WHERE
                site_id = $1
            GROUP BY
                cm.dataset_id""",
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.CarbonIntensity,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
        )
        for item in res
    ]


async def list_ashp_datasets() -> list[DatasetEntry]:
    """
    List the ASHP datasets we have in the database.

    This is a dummy function as we don't actually store them, but it returns a reasonable looking response.
    """
    return [
        DatasetEntry(
            dataset_id=uuid.uuid4(), dataset_type=DatasetTypeEnum.ASHPData, created_at=datetime.datetime.now(datetime.UTC)
        )
    ]


@router.post("/list-datasets", tags=["db", "list"])
async def list_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    Get all the datasets associated with a particular site, in the form of a list of UUID strings.

    This covers datasets across all types; it is your responsibility to then pass them to the correct endpoints
    (for example, sending a dataset ID corresponding to a gas dataset will not work when requesting renewables.)
    This will make multiple database calls, as doing it all in a single SQL query caused a terrible mess.

    Parameters
    ----------
    *site_id*
        Database ID for the site you are interested in.

    Returns
    -------
    A list of UUID dataset strings, with the earliest at the start and the latest at the end.
    """
    async with asyncio.TaskGroup() as tg:
        gas_task = tg.create_task(list_gas_datasets(site_id, pool))
        elec_task = tg.create_task(list_elec_datasets(site_id, pool))
        elec_synth_task = tg.create_task(list_elec_synthesised_datasets(site_id, pool))
        import_tariff_task = tg.create_task(list_import_tariff_datasets(site_id, pool))
        renewables_generation_task = tg.create_task(list_renewables_generation_datasets(site_id, pool))
        heating_load_task = tg.create_task(list_heating_load_datasets(site_id, pool))
        carbon_intensity_task = tg.create_task(list_carbon_intensity_datasets(site_id, pool))
        ashp_task = tg.create_task(list_ashp_datasets())

    res = [
        *gas_task.result(),
        *elec_task.result(),
        *elec_synth_task.result(),
        *import_tariff_task.result(),
        *renewables_generation_task.result(),
        *heating_load_task.result(),
        *carbon_intensity_task.result(),
    ]
    # If we didn't get any real datasets, then
    # don't insert a dummy ASHP dataset
    if res:
        res += ashp_task.result()
    logging.info(f"Returning {len(res)} datasets for {site_id}")
    return res


@router.post("/list-latest-datasets", tags=["db", "list"])
async def list_latest_datasets(site_id: SiteID, pool: DatabasePoolDep) -> dict[DatasetTypeEnum, DatasetEntry]:
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
    all_datasets = await list_datasets(site_id, pool)

    latest_ds: dict[DatasetTypeEnum, DatasetEntry] = {}
    for dataset in all_datasets:
        if dataset.dataset_type not in latest_ds or (latest_ds[dataset.dataset_type].created_at < dataset.created_at):
            latest_ds[dataset.dataset_type] = dataset
    return dict(latest_ds)


@router.post("/get-specific-datasets", tags=["db", "get"])
async def get_specific_datasets(site_data: DatasetRequest, pool: DatabasePoolDep) -> SiteDataEntries:
    """
    Get specific datasets with chosen IDs for a given site.

    This endpoint combines a call to /list-latest-datasets with each of the /get endpoints for those datasets.
    If a dataset isn't specified in the call, then we'll return the latest.

    Parameters
    ----------
    site_data
        A specification for the required site data; UUIDs of the datasets of each type you wish to request.

    Returns
    -------
        The site data with full time series for each data source
    """
    latest_datasets_info = await list_latest_datasets(SiteID(site_id=site_data.site_id), pool=pool)

    specified_or_latest_ids: dict[DatasetTypeEnum, pydantic.UUID4] = {}
    dumped_site_info = site_data.model_dump()
    for ds_type in DatasetTypeEnum:
        if ds_type.value in dumped_site_info and dumped_site_info[ds_type.value] is not None:
            specified_or_latest_ids[ds_type] = dumped_site_info[ds_type.value]
        elif ds_type in latest_datasets_info:
            specified_or_latest_ids[ds_type] = latest_datasets_info[ds_type].dataset_id

    site_data_ids: dict[DatasetTypeEnum, DatasetIDWithTime | MultipleDatasetIDWithTime] = {}
    for ds_type, dataset_id in specified_or_latest_ids.items():
        if ds_type in MULTIPLE_DATASET_ENDPOINTS:
            site_data_ids[ds_type] = MultipleDatasetIDWithTime(
                dataset_id=[dataset_id],
                start_ts=site_data.start_ts,
                end_ts=site_data.start_ts + datetime.timedelta(hours=8760),
            )
        else:
            site_data_ids[ds_type] = DatasetIDWithTime(
                dataset_id=dataset_id,
                start_ts=site_data.start_ts,
                end_ts=site_data.start_ts + datetime.timedelta(hours=8760),
            )
    return await fetch_all_input_data(site_data_ids, pool=pool)


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
    logging.info(f"Getting latest dataset list for {site_data.site_id}")

    site_data_info = await list_latest_datasets(SiteID(site_id=site_data.site_id), pool=pool)

    site_data_ids: dict[DatasetTypeEnum, DatasetIDWithTime | MultipleDatasetIDWithTime] = {}
    for dataset_name, dataset_metadata in site_data_info.items():
        if dataset_name in MULTIPLE_DATASET_ENDPOINTS:
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

    return await fetch_all_input_data(site_data_ids, pool=pool)


@router.post("/generate-all")
async def generate_all(
    params: SiteIDWithTime, pool: DatabasePoolDep, http_client: HttpClientDep, vae: VaeDep, secrets_env: SecretsDep
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
    datasets = await list_latest_datasets(SiteID(site_id=params.site_id), pool=pool)

    if DatasetTypeEnum.GasMeterData not in datasets:
        raise HTTPException(400, f"No gas meter data for {params.site_id}.")
    if DatasetTypeEnum.ElectricityMeterData not in datasets:
        raise HTTPException(400, f"No electrical meter data for {params.site_id}.")
    heating_load_dataset = datasets[DatasetTypeEnum.GasMeterData]
    elec_meter_dataset = datasets[DatasetTypeEnum.ElectricityMeterData]

    try:
        async with asyncio.TaskGroup() as tg:
            heating_load_response = tg.create_task(
                generate_heating_load(
                    HeatingLoadRequest(
                        dataset_id=heating_load_dataset.dataset_id, start_ts=params.start_ts, end_ts=params.end_ts
                    ),
                    pool=pool,
                    http_client=http_client,
                )
            )
            grid_co2_response = tg.create_task(generate_grid_co2(params, pool=pool, http_client=http_client))

            import_tariff_response = tg.create_task(
                generate_import_tariffs(
                    TariffRequest(
                        site_id=params.site_id,
                        tariff_name=SyntheticTariffEnum.Fixed,
                        start_ts=params.start_ts,
                        end_ts=params.end_ts,
                    ),
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
                    secrets_env=secrets_env,
                )
            )

            elec_response = tg.create_task(
                generate_electricity_load(
                    ElectricalLoadRequest(
                        dataset_id=elec_meter_dataset.dataset_id, start_ts=params.start_ts, end_ts=params.end_ts
                    ),
                    pool=pool,
                    http_client=http_client,
                    vae=vae,
                )
            )
    except* ValueError as excgroup:
        raise HTTPException(500, detail=f"Generate all failed due to {list(excgroup.exceptions)}") from excgroup
    except* TypeError as excgroup:
        raise HTTPException(500, detail=f"Generate all failed due to {list(excgroup.exceptions)}") from excgroup
    except* httpx.ReadTimeout as excgroup:
        raise HTTPException(500, detail=f"Generate all failed due to {list(excgroup.exceptions)}") from excgroup
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
