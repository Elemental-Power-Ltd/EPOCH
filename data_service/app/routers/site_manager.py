"""Lazy endpoints for bundling everything together."""

import asyncio
import datetime
import logging
import uuid
from typing import Any, cast

import httpx
from fastapi import APIRouter, HTTPException

from ..dependencies import DatabasePoolDep, HttpClientDep, SecretsDep, VaeDep
from ..internal.site_manager.site_manager import fetch_all_input_data, fetch_import_tariffs
from ..models.client_data import SiteDataEntries
from ..models.core import (
    DatasetEntry,
    DatasetIDWithTime,
    DatasetTypeEnum,
    MultipleDatasetIDWithTime,
    SiteID,
    SiteIDWithTime,
    dataset_id_t,
)
from ..models.electricity_load import ElectricalLoadRequest
from ..models.heating_load import HeatingLoadRequest
from ..models.import_tariffs import EpochTariffEntry, SyntheticTariffEnum, TariffRequest
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
    logger.info(f"Returning {len(res)} datasets for {site_id}")
    return res


@router.post("/list-latest-datasets", tags=["db", "list"])
async def list_latest_datasets(
    site_id: SiteID, pool: DatabasePoolDep
) -> dict[DatasetTypeEnum, DatasetEntry | list[DatasetEntry]]:
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

    curr_latest_ds: dict[DatasetTypeEnum, DatasetEntry | dict[Any, DatasetEntry]] = {}
    for dataset in all_datasets:
        if dataset.dataset_subtype is not None:
            if dataset.dataset_type not in curr_latest_ds:
                curr_latest_ds[dataset.dataset_type] = {dataset.dataset_subtype: dataset}
            no_entries_yet = dataset.dataset_subtype not in curr_latest_ds[dataset.dataset_type]
            is_newer_than_entry = no_entries_yet or (
                curr_latest_ds[dataset.dataset_type][dataset.dataset_subtype].created_at < dataset.created_at  # type: ignore
            )
            if no_entries_yet or is_newer_than_entry:
                curr_latest_ds[dataset.dataset_type][dataset.dataset_subtype] = dataset  # type: ignore
        elif dataset.dataset_type not in curr_latest_ds or (
            curr_latest_ds[dataset.dataset_type].created_at < dataset.created_at
        ):  # type: ignore
            curr_latest_ds[dataset.dataset_type] = dataset  # type: ignore

    # For the multiple entry, let's just form it into a list in the right order.

    latest_ds: dict[DatasetTypeEnum, DatasetEntry | list[DatasetEntry]] = {
        key: value
        for key, value in curr_latest_ds.items()
        if key != DatasetTypeEnum.ImportTariff and isinstance(value, DatasetEntry)
    }
    if isinstance(curr_latest_ds.get(DatasetTypeEnum.ImportTariff), dict):
        tariff_types = [
            SyntheticTariffEnum.Fixed,
            SyntheticTariffEnum.Agile,
            SyntheticTariffEnum.Overnight,
            SyntheticTariffEnum.Peak,
        ]
        tariff_list: list[DatasetEntry] = [
            curr_latest_ds[DatasetTypeEnum.ImportTariff][tariff_type]  # type: ignore
            for tariff_type in tariff_types
            if tariff_type in curr_latest_ds.get(DatasetTypeEnum.ImportTariff, {})
        ]
        latest_ds[DatasetTypeEnum.ImportTariff] = tariff_list
    return latest_ds


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

    specified_or_latest_ids: dict[DatasetTypeEnum, dataset_id_t | list[dataset_id_t]] = {}
    dumped_site_info = site_data.model_dump()
    for ds_type in DatasetTypeEnum:
        if ds_type.value in dumped_site_info and dumped_site_info[ds_type.value] is not None:
            specified_or_latest_ids[ds_type] = dumped_site_info[ds_type.value]
        elif isinstance(latest_datasets_info.get(ds_type), DatasetEntry):
            # mypy can't figure these things out, so let's stick in these pointless casts
            specified_or_latest_ids[ds_type] = cast(DatasetEntry, latest_datasets_info[ds_type]).dataset_id
        elif isinstance(latest_datasets_info.get(ds_type), list):
            specified_or_latest_ids[ds_type] = [cast(DatasetEntry, item).dataset_id for item in latest_datasets_info[ds_type]]

    site_data_ids: dict[DatasetTypeEnum, DatasetIDWithTime | MultipleDatasetIDWithTime] = {}
    YEAR_LENGTH = datetime.timedelta(hours=8760)
    for dataset_name, dataset_metadata in specified_or_latest_ids.items():
        if isinstance(dataset_metadata, list):
            site_data_ids[dataset_name] = MultipleDatasetIDWithTime(
                dataset_id=dataset_metadata,
                start_ts=site_data.start_ts,
                end_ts=site_data.start_ts + YEAR_LENGTH,
            )
        elif ds_type in MULTIPLE_DATASET_ENDPOINTS:
            site_data_ids[ds_type] = MultipleDatasetIDWithTime(
                dataset_id=[dataset_metadata],
                start_ts=site_data.start_ts,
                end_ts=site_data.start_ts + YEAR_LENGTH,
            )
        else:
            site_data_ids[ds_type] = DatasetIDWithTime(
                dataset_id=dataset_metadata, start_ts=site_data.start_ts, end_ts=site_data.start_ts + YEAR_LENGTH
            )
    try:
        return await fetch_all_input_data(site_data_ids, pool=pool)
    except KeyError as ex:
        raise HTTPException(400, f"Missing dataset {ex}. Did you run generate-all for this site?") from ex


@router.post("/get-latest-tariffs", tags=["db", "tariff"])
async def get_latest_tariffs(site_data: RemoteMetaData, pool: DatabasePoolDep) -> list[EpochTariffEntry]:
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
    site_data_info = await list_latest_datasets(SiteID(site_id=site_data.site_id), pool=pool)

    dataset_metadata = site_data_info[DatasetTypeEnum.ImportTariff]
    YEAR_LENGTH = datetime.timedelta(hours=8760)
    params = MultipleDatasetIDWithTime(
        dataset_id=[cast(DatasetEntry, item).dataset_id for item in dataset_metadata],
        start_ts=site_data.start_ts,
        end_ts=site_data.start_ts + YEAR_LENGTH,
    )
    return await fetch_import_tariffs(params, pool)


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
    logger = logging.getLogger(__name__)
    logger.info(f"Getting latest dataset list for {site_data.site_id}")

    site_data_info = await list_latest_datasets(SiteID(site_id=site_data.site_id), pool=pool)

    site_data_ids: dict[DatasetTypeEnum, DatasetIDWithTime | MultipleDatasetIDWithTime] = {}
    YEAR_LENGTH = datetime.timedelta(hours=8760)
    for dataset_name, dataset_metadata in site_data_info.items():
        if isinstance(dataset_metadata, list):
            site_data_ids[dataset_name] = MultipleDatasetIDWithTime(
                dataset_id=[item.dataset_id for item in dataset_metadata],
                start_ts=site_data.start_ts,
                end_ts=site_data.start_ts + YEAR_LENGTH,
            )
        elif dataset_name in MULTIPLE_DATASET_ENDPOINTS:
            # We've got a single dataset ID, but it's for an endpoint that
            # takes multiple.
            site_data_ids[dataset_name] = MultipleDatasetIDWithTime(
                dataset_id=[dataset_metadata.dataset_id],
                start_ts=site_data.start_ts,
                end_ts=site_data.start_ts + YEAR_LENGTH,
            )
        else:
            site_data_ids[dataset_name] = DatasetIDWithTime(
                dataset_id=dataset_metadata.dataset_id,
                start_ts=site_data.start_ts,
                end_ts=site_data.start_ts + YEAR_LENGTH,
            )

    try:
        return await fetch_all_input_data(site_data_ids, pool=pool)
    except KeyError as ex:
        raise HTTPException(400, f"Missing dataset {ex}. Did you run generate-all for this site?") from ex


@router.post("/generate-all")
async def generate_all(
    params: SiteIDWithTime, pool: DatabasePoolDep, http_client: HttpClientDep, vae: VaeDep, secrets_env: SecretsDep
) -> dict[DatasetTypeEnum, DatasetEntry | list[DatasetEntry]]:
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
            assert isinstance(heating_load_dataset, DatasetEntry)
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

            # We generate four different types of tariff, here done manually to keep track of the
            # tasks and not lose the handle to the task (which causes mysterious bugs)
            import_tariff_response_fixed = tg.create_task(
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
            import_tariff_response_overnight = tg.create_task(
                generate_import_tariffs(
                    TariffRequest(
                        site_id=params.site_id,
                        tariff_name=SyntheticTariffEnum.Overnight,
                        start_ts=params.start_ts,
                        end_ts=params.end_ts,
                    ),
                    pool=pool,
                    http_client=http_client,
                )
            )
            import_tariff_response_agile = tg.create_task(
                generate_import_tariffs(
                    TariffRequest(
                        site_id=params.site_id,
                        tariff_name=SyntheticTariffEnum.Agile,
                        start_ts=params.start_ts,
                        end_ts=params.end_ts,
                    ),
                    pool=pool,
                    http_client=http_client,
                )
            )
            import_tariff_response_peak = tg.create_task(
                generate_import_tariffs(
                    TariffRequest(
                        site_id=params.site_id,
                        tariff_name=SyntheticTariffEnum.Peak,
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
            assert isinstance(elec_meter_dataset, DatasetEntry)
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
        DatasetTypeEnum.ImportTariff: [
            DatasetEntry(
                dataset_id=import_tariff_response_fixed.result().dataset_id,
                dataset_type=DatasetTypeEnum.ImportTariff,
                created_at=import_tariff_response_fixed.result().created_at,
                dataset_subtype=SyntheticTariffEnum.Fixed,
            ),
            DatasetEntry(
                dataset_id=import_tariff_response_agile.result().dataset_id,
                dataset_type=DatasetTypeEnum.ImportTariff,
                created_at=import_tariff_response_agile.result().created_at,
                dataset_subtype=SyntheticTariffEnum.Agile,
            ),
            DatasetEntry(
                dataset_id=import_tariff_response_overnight.result().dataset_id,
                dataset_type=DatasetTypeEnum.ImportTariff,
                created_at=import_tariff_response_overnight.result().created_at,
                dataset_subtype=SyntheticTariffEnum.Overnight,
            ),
            DatasetEntry(
                dataset_id=import_tariff_response_peak.result().dataset_id,
                dataset_type=DatasetTypeEnum.ImportTariff,
                created_at=import_tariff_response_peak.result().created_at,
                dataset_subtype=SyntheticTariffEnum.Peak,
            ),
        ],
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
