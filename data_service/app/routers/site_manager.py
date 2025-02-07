"""Lazy endpoints for bundling everything together."""

import asyncio
import datetime
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..dependencies import DatabasePoolDep, HttpClientDep, SecretsDep, VaeDep
from ..internal.site_manager.site_manager import fetch_all_input_data
from ..models.client_data import SiteDataEntries
from ..models.core import (
    DatasetEntry,
    DatasetIDWithTime,
    DatasetTypeEnum,
    MultipleDatasetIDWithTime,
    SiteIDWithTime,
    dataset_id_t,
)
from ..models.electricity_load import ElectricalLoadRequest
from ..models.heating_load import HeatingLoadRequest
from ..models.import_tariffs import EpochTariffEntry, SyntheticTariffEnum, TariffRequest
from ..models.renewables import RenewablesRequest
from ..models.site_manager import DatasetList, RemoteMetaData
from .carbon_intensity import generate_grid_co2
from .electricity_load import generate_electricity_load
from .heating_load import generate_heating_load
from .import_tariffs import generate_import_tariffs, get_import_tariffs
from .renewables import generate_renewables_generation

router = APIRouter()

MULTIPLE_DATASET_ENDPOINTS = {DatasetTypeEnum.HeatingLoad, DatasetTypeEnum.RenewablesGeneration, DatasetTypeEnum.ImportTariff}
NULL_UUID = uuid.UUID(int=0, version=4)


async def list_gas_datasets(site_id: SiteIDWithTime, pool: DatabasePoolDep) -> list[DatasetEntry]:
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


async def list_elec_datasets(site_id: SiteIDWithTime, pool: DatabasePoolDep) -> list[DatasetEntry]:
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


async def list_elec_synthesised_datasets(site_id: SiteIDWithTime, pool: DatabasePoolDep) -> list[DatasetEntry]:
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


async def list_import_tariff_datasets(site_id: SiteIDWithTime, pool: DatabasePoolDep) -> list[DatasetEntry]:
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
                (MAX(te.end_ts) - MIN(te.start_ts)) / (COUNT(*) - 1) AS resolution,
                ANY_VALUE(provider) AS provider,
                ANY_VALUE(product_name) AS product_name
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
            dataset_subtype=SyntheticTariffEnum(item["product_name"]) if item["provider"] == "synthetic" else None,
        )
        for item in res
    ]


async def list_renewables_generation_datasets(site_id: SiteIDWithTime, pool: DatabasePoolDep) -> list[DatasetEntry]:
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


async def list_heating_load_datasets(site_id: SiteIDWithTime, pool: DatabasePoolDep) -> list[DatasetEntry]:
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


async def list_carbon_intensity_datasets(site_id: SiteIDWithTime, pool: DatabasePoolDep) -> list[DatasetEntry]:
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
async def list_datasets(site_id: SiteIDWithTime, pool: DatabasePoolDep) -> dict[DatasetTypeEnum, list[DatasetEntry]]:
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
    logger = logging.getLogger(__name__)
    async with asyncio.TaskGroup() as tg:
        gas_task = tg.create_task(list_gas_datasets(site_id, pool))
        elec_task = tg.create_task(list_elec_datasets(site_id, pool))
        elec_synth_task = tg.create_task(list_elec_synthesised_datasets(site_id, pool))
        import_tariff_task = tg.create_task(list_import_tariff_datasets(site_id, pool))
        renewables_generation_task = tg.create_task(list_renewables_generation_datasets(site_id, pool))
        heating_load_task = tg.create_task(list_heating_load_datasets(site_id, pool))
        carbon_intensity_task = tg.create_task(list_carbon_intensity_datasets(site_id, pool))
        ashp_task = tg.create_task(list_ashp_datasets())

    res = {
        DatasetTypeEnum.GasMeterData: gas_task.result(),
        DatasetTypeEnum.ElectricityMeterData: elec_task.result(),
        DatasetTypeEnum.ElectricityMeterDataSynthesised: elec_synth_task.result(),
        DatasetTypeEnum.ImportTariff: import_tariff_task.result(),
        DatasetTypeEnum.RenewablesGeneration: renewables_generation_task.result(),
        DatasetTypeEnum.HeatingLoad: heating_load_task.result(),
        DatasetTypeEnum.CarbonIntensity: carbon_intensity_task.result(),
    }
    # If we didn't get any real datasets, then
    # don't insert a dummy ASHP dataset
    if any(val is not None for val in res.values()):
        res[DatasetTypeEnum.ASHPData] = ashp_task.result()
    logger.info(f"Returning {len(res)} datasets for {site_id}")
    return res


@router.post("/list-latest-datasets", tags=["db", "list"])
async def list_latest_datasets(params: SiteIDWithTime, pool: DatabasePoolDep) -> DatasetList:
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
    all_datasets = await list_datasets(params, pool)

    return DatasetList(
        site_id=params.site_id,
        start_ts=params.start_ts,
        end_ts=params.end_ts,
        # HeatingLoads are a MultipleDatasetIDWithTime, so wrap them into a list here.
        HeatingLoad=[max(all_datasets[DatasetTypeEnum.HeatingLoad], key=lambda x: x.created_at)]
        if all_datasets.get(DatasetTypeEnum.HeatingLoad)
        else None,
        ImportTariff=[
            item
            for item in (
                max(
                    filter(
                        lambda x: x is not None and x.dataset_subtype == tariff_type, all_datasets[DatasetTypeEnum.ImportTariff]
                    ),
                    key=lambda x: x.created_at
                    if x is not None
                    else datetime.datetime(year=1970, month=1, day=1, tzinfo=datetime.UTC),
                    default=None,
                )
                for tariff_type in SyntheticTariffEnum
            )
            if item is not None
        ],
        ASHPData=max(all_datasets[DatasetTypeEnum.ASHPData], key=lambda x: x.created_at)
        if all_datasets.get(DatasetTypeEnum.ASHPData)
        else None,
        CarbonIntensity=max(all_datasets[DatasetTypeEnum.CarbonIntensity], key=lambda x: x.created_at)
        if all_datasets.get(DatasetTypeEnum.CarbonIntensity)
        else None,
        ElectricityMeterData=max(all_datasets[DatasetTypeEnum.ElectricityMeterData], key=lambda x: x.created_at)
        if all_datasets.get(DatasetTypeEnum.ElectricityMeterData)
        else None,
        ElectricityMeterDataSynthesised=max(
            all_datasets[DatasetTypeEnum.ElectricityMeterDataSynthesised], key=lambda x: x.created_at
        )
        if all_datasets.get(DatasetTypeEnum.ElectricityMeterDataSynthesised)
        else None,
        Weather=max(all_datasets[DatasetTypeEnum.Weather], key=lambda x: x.created_at)
        if all_datasets.get(DatasetTypeEnum.Weather)
        else None,
        GasMeterData=max(all_datasets[DatasetTypeEnum.GasMeterData], key=lambda x: x.created_at)
        if all_datasets.get(DatasetTypeEnum.GasMeterData)
        else None,
        # RenewablesGeneration are a MultipleDatasetIDWithTime, so wrap them into a list here.
        RenewablesGeneration=[max(all_datasets[DatasetTypeEnum.RenewablesGeneration], key=lambda x: x.created_at)]
        if all_datasets.get(DatasetTypeEnum.RenewablesGeneration)
        else None,
    )


@router.post("/get-specific-datasets", tags=["db", "get"])
async def get_specific_datasets(site_data: DatasetList | RemoteMetaData, pool: DatabasePoolDep) -> SiteDataEntries:
    """
    Get specific datasets with chosen IDs for a given site.

    This endpoint combines a call to /list-latest-datasets with each of the /get endpoints for those datasets.
    If you haven't specified an ID, we won't return it to you.

    Parameters
    ----------
    site_data
        A specification for the required site data; UUIDs of the datasets of each type you wish to request.

    Returns
    -------
        The site data with full time series for each data source
    """
    if isinstance(site_data, DatasetList):
        new_site_data = RemoteMetaData(site_id=site_data.site_id, start_ts=site_data.start_ts, end_ts=site_data.end_ts)
        for key in DatasetTypeEnum:
            curr_entries = site_data.model_dump()[key]
            if isinstance(curr_entries, list):
                curr_id = [item["dataset_id"] for item in curr_entries]
            elif isinstance(curr_entries, dict):
                curr_id = curr_entries["dataset_id"]
            else:
                curr_id = None
            new_site_data.__setattr__(key, curr_id)
        site_data = new_site_data
    site_data_ids: dict[DatasetTypeEnum, DatasetIDWithTime | MultipleDatasetIDWithTime] = {}
    for dataset_type in DatasetTypeEnum:
        site_data_entry: dataset_id_t | list[dataset_id_t] | None = site_data.__getattribute__(dataset_type.value)
        if isinstance(site_data_entry, list):
            # Skip the zero length lists, if any have snuck through
            if not site_data_entry:
                continue
            site_data_ids[dataset_type] = MultipleDatasetIDWithTime(
                dataset_id=site_data_entry, start_ts=site_data.start_ts, end_ts=site_data.end_ts
            )
        elif site_data_entry is not None:
            site_data_ids[dataset_type] = DatasetIDWithTime(
                dataset_id=site_data_entry, start_ts=site_data.start_ts, end_ts=site_data.end_ts
            )
        else:
            # We got no dataset here, so skip it.
            continue
    try:
        return await fetch_all_input_data(site_data_ids, pool=pool)
    except KeyError as ex:
        raise HTTPException(400, f"Missing dataset {ex}. Did you run generate-all for this site?") from ex


@router.post("/get-latest-tariffs", tags=["db", "tariff"])
async def get_latest_tariffs(site_data: SiteIDWithTime, pool: DatabasePoolDep) -> list[EpochTariffEntry]:
    """
    Get the latest Import Tariff entries for a given site.

    This will endeavour to get the most recently generated synthetic tariff of each type.
    If a given tariff type isn't in the database, we skip it.
    The Fixed tariff is generally at index 0.

    Parameters
    ----------
    site_data
        Metadata about the site to get, including a site ID. All other fields except site_id are ignored.
    pool
        Database pool

    Raises
    ------
    KeyError
        if there are no ImportTariffs generated.

    Returns
    -------
    list[EpochTariffEntry]
        List of tariff entries with fields Tariff, Tariff1, Tariff2, etc. filled.
    """
    site_data_info = await list_latest_datasets(site_data, pool=pool)

    YEAR_LENGTH = datetime.timedelta(hours=8760)

    if site_data_info.ImportTariff is None:
        logger = logging.getLogger(__name__)
        logger.warning(f"Requested latest tariffs for {site_data.site_id} but None were available.")
        return []
    params = MultipleDatasetIDWithTime(
        dataset_id=[item.dataset_id for item in site_data_info.ImportTariff]
        if isinstance(site_data_info.ImportTariff, list)
        else [site_data_info.ImportTariff.dataset_id],
        start_ts=site_data.start_ts,
        end_ts=site_data.start_ts + YEAR_LENGTH,
    )
    return await get_import_tariffs(params, pool)


@router.post("/get-latest-datasets", tags=["db", "get"])
async def get_latest_datasets(params: SiteIDWithTime, pool: DatabasePoolDep) -> SiteDataEntries:
    """
    Get the most recent dataset entries of each type for this site.

    This endpoint combines a call to /list-latest-datasets with each of the /get endpoints for those datasets

    Parameters
    ----------
    paramss
        The site ID you want, and the start / end times for the datasets you want.

    Returns
    -------
        The site data with full time series for each data source
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Getting latest dataset list for {params.site_id}")
    site_data = await list_latest_datasets(params, pool=pool)

    try:
        return await get_specific_datasets(site_data, pool)
    except KeyError as ex:
        raise HTTPException(400, f"Missing dataset {ex}. Did you run generate-all for this site?") from ex


@router.post("/generate-all")
async def generate_all(
    params: SiteIDWithTime,
    pool: DatabasePoolDep,
    http_client: HttpClientDep,
    vae: VaeDep,
    secrets_env: SecretsDep,
    background_tasks: BackgroundTasks,
) -> dict[DatasetTypeEnum, DatasetEntry | list[DatasetEntry]]:
    """
    Run all dataset generation tasks for this site.

    This includes heating load, grid CO2, electrical load, carbon intensity and solar PV.
    Currently it uses a simple tariff that covers a long period of time, and optimal solar PV parameters.
    You almost certainly want the timestamps to be 2021 or 2022 so we can use renewables.ninja data, and relatively recent
    tariff data.

    This will run background tasks for each sub item, which can take upwards of 1 minute.
    For that reason, we'll return an empty set of null data early and chug along in the background.
    This may block the main thread, so be careful.

    Parameters
    ----------
    params
        SiteIDWithTime, including two relatively far back timestamps for Renewables Ninja to use.
    pool
        Connection pool to underlying PostgreSQL database
    http_client
        Asynchronous HTTP client to use for requests to 3rd party APIs
    vae
        ML model for upscaling of electrical data
    secrets_env
        Client secrets environment
    background_tasks
        Task group to run after returning data

    Returns
    -------
    datasets
        Dataset Type: Dataset Entry mapping, but with placeholder null UUIDs as the background tasks need to run.
        Note that this will return immediately, but block this thread until the calculations are done.
    """
    # Note that we specifically don't request time-limited datasets here.
    # This is because we want to resample from the existing dataset pool into new time periods (those specified in the params)
    datasets = await list_latest_datasets(
        SiteIDWithTime(
            site_id=params.site_id,
            start_ts=datetime.datetime(year=1970, month=1, day=1, tzinfo=datetime.UTC),
            end_ts=datetime.datetime.now(datetime.UTC),
        ),
        pool=pool,
    )

    gas_meter_dataset = datasets.GasMeterData
    elec_meter_dataset = datasets.ElectricityMeterData

    if gas_meter_dataset is None:
        raise HTTPException(400, f"No gas meter data for {params.site_id}.")
    if elec_meter_dataset is None:
        raise HTTPException(400, f"No electrical meter data for {params.site_id}.")
    assert isinstance(gas_meter_dataset, DatasetEntry), (
        f"Expecting a DatasetEntry for gas_meter_dataset but got {type(gas_meter_dataset)}"
    )
    assert isinstance(elec_meter_dataset, DatasetEntry), (
        f"Expecting a DatasetEntry for elec_meter_dataset but got {type(elec_meter_dataset)}"
    )
    background_tasks.add_task(
        generate_heating_load,
        HeatingLoadRequest(dataset_id=gas_meter_dataset.dataset_id, start_ts=params.start_ts, end_ts=params.end_ts),
        pool=pool,
        http_client=http_client,
    )

    background_tasks.add_task(generate_grid_co2, params, pool=pool, http_client=http_client)

    # We generate four different types of tariff, here done manually to keep track of the
    # tasks and not lose the handle to the task (which causes mysterious bugs)
    for tariff_type in SyntheticTariffEnum:
        background_tasks.add_task(
            generate_import_tariffs,
            TariffRequest(
                site_id=params.site_id,
                tariff_name=tariff_type,
                start_ts=params.start_ts,
                end_ts=params.end_ts,
            ),
            pool=pool,
            http_client=http_client,
        )

    background_tasks.add_task(
        generate_renewables_generation,
        RenewablesRequest(site_id=params.site_id, start_ts=params.start_ts, end_ts=params.end_ts, azimuth=None, tilt=None),
        pool=pool,
        http_client=http_client,
        secrets_env=secrets_env,
    )

    background_tasks.add_task(
        generate_electricity_load,
        ElectricalLoadRequest(dataset_id=elec_meter_dataset.dataset_id, start_ts=params.start_ts, end_ts=params.end_ts),
        pool=pool,
        http_client=http_client,
        vae=vae,
    )

    RESOLUTION = datetime.timedelta(minutes=30)
    # Return the background tasks immediately with null-ish data.
    # The UUIDs will have to be collected later (unless we assign them in this function in future?)
    return {
        DatasetTypeEnum.HeatingLoad: DatasetEntry(
            dataset_id=NULL_UUID,
            dataset_type=DatasetTypeEnum.HeatingLoad,
            created_at=datetime.datetime.now(tz=datetime.UTC),
            resolution=RESOLUTION,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
        ),
        DatasetTypeEnum.CarbonIntensity: DatasetEntry(
            dataset_id=NULL_UUID,
            dataset_type=DatasetTypeEnum.CarbonIntensity,
            created_at=datetime.datetime.now(tz=datetime.UTC),
            resolution=RESOLUTION,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
        ),
        DatasetTypeEnum.ImportTariff: [
            DatasetEntry(
                dataset_id=NULL_UUID,
                dataset_type=DatasetTypeEnum.ImportTariff,
                created_at=datetime.datetime.now(tz=datetime.UTC),
                dataset_subtype=tariff_type,
                resolution=RESOLUTION,
                start_ts=params.start_ts,
                end_ts=params.end_ts,
                num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
            )
            for tariff_type in SyntheticTariffEnum
        ],
        DatasetTypeEnum.RenewablesGeneration: DatasetEntry(
            dataset_id=NULL_UUID,
            dataset_type=DatasetTypeEnum.RenewablesGeneration,
            created_at=datetime.datetime.now(tz=datetime.UTC),
            resolution=RESOLUTION,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
        ),
        DatasetTypeEnum.ElectricityMeterData: elec_meter_dataset,
        DatasetTypeEnum.ElectricityMeterDataSynthesised: DatasetEntry(
            dataset_id=NULL_UUID,
            dataset_type=DatasetTypeEnum.ElectricityMeterDataSynthesised,
            created_at=datetime.datetime.now(tz=datetime.UTC),
            resolution=RESOLUTION,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
        ),
        DatasetTypeEnum.ASHPData: DatasetEntry(
            dataset_id=NULL_UUID,
            dataset_type=DatasetTypeEnum.ASHPData,
            created_at=datetime.datetime.now(tz=datetime.UTC),
            resolution=RESOLUTION,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
        ),
    }
