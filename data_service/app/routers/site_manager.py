"""Lazy endpoints for bundling everything together."""

import asyncio
import datetime
import logging
import uuid
import warnings
from asyncio import Task
from collections.abc import Sequence
from typing import Any, cast

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..dependencies import DatabasePoolDep, HttpClientDep, SecretsDep, VaeDep
from ..internal.site_manager import (
    list_ashp_datasets,
    list_carbon_intensity_datasets,
    list_elec_datasets,
    list_elec_synthesised_datasets,
    list_gas_datasets,
    list_heating_load_datasets,
    list_import_tariff_datasets,
    list_renewables_generation_datasets,
    list_thermal_models,
)
from ..internal.site_manager.bundles import file_self_with_bundle, insert_dataset_bundle
from ..internal.site_manager.dataset_lists import list_baseline_datasets
from ..internal.site_manager.fetch_data import fetch_all_input_data
from ..internal.utils.uuid import uuid7
from ..models.carbon_intensity import GridCO2Request
from ..models.client_data import SiteDataEntries, SolarLocation
from ..models.core import (
    BundleEntryMetadata,
    DatasetEntry,
    DatasetIDWithTime,
    DatasetTypeEnum,
    MultipleDatasetIDWithTime,
    RequestBase,
    SiteID,
    SiteIDWithTime,
    dataset_id_t,
)
from ..models.electricity_load import ElectricalLoadRequest
from ..models.heating_load import HeatingLoadRequest, InterventionEnum
from ..models.import_tariffs import EpochTariffEntry, SyntheticTariffEnum, TariffRequest
from ..models.renewables import RenewablesRequest
from ..models.site_manager import DatasetBundleMetadata, DatasetList, RemoteMetaData
from ..models.weather import WeatherRequest
from .carbon_intensity import generate_grid_co2
from .client_data import get_location, get_solar_locations
from .electricity_load import generate_electricity_load
from .heating_load import generate_heating_load
from .import_tariffs import generate_import_tariffs, get_import_tariffs
from .renewables import generate_renewables_generation
from .weather import get_weather

router = APIRouter()

MULTIPLE_DATASET_ENDPOINTS = {DatasetTypeEnum.HeatingLoad, DatasetTypeEnum.RenewablesGeneration, DatasetTypeEnum.ImportTariff}
NULL_UUID = uuid.UUID(int=0, version=4)
type to_generate_t = dict[DatasetTypeEnum, RequestBase | Sequence[RequestBase]]
logger = logging.getLogger(__name__)


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
    async with asyncio.TaskGroup() as tg:
        baseline_task = tg.create_task(list_baseline_datasets(site_id, pool))
        gas_task = tg.create_task(list_gas_datasets(site_id, pool))
        elec_task = tg.create_task(list_elec_datasets(site_id, pool))
        elec_synth_task = tg.create_task(list_elec_synthesised_datasets(site_id, pool))
        import_tariff_task = tg.create_task(list_import_tariff_datasets(site_id, pool))
        renewables_generation_task = tg.create_task(list_renewables_generation_datasets(site_id, pool))
        heating_load_task = tg.create_task(list_heating_load_datasets(site_id, pool))
        carbon_intensity_task = tg.create_task(list_carbon_intensity_datasets(site_id, pool))
        ashp_task = tg.create_task(list_ashp_datasets())
        thermal_model_task = tg.create_task(list_thermal_models(site_id, pool))

    res = {
        DatasetTypeEnum.SiteBaseline: baseline_task.result(),
        DatasetTypeEnum.GasMeterData: gas_task.result(),
        DatasetTypeEnum.ElectricityMeterData: elec_task.result(),
        DatasetTypeEnum.ElectricityMeterDataSynthesised: elec_synth_task.result(),
        DatasetTypeEnum.ImportTariff: import_tariff_task.result(),
        DatasetTypeEnum.RenewablesGeneration: renewables_generation_task.result(),
        DatasetTypeEnum.HeatingLoad: heating_load_task.result(),
        DatasetTypeEnum.CarbonIntensity: carbon_intensity_task.result(),
        DatasetTypeEnum.ThermalModel: thermal_model_task.result(),
    }
    # If we didn't get any real datasets, then
    # don't insert a dummy ASHP dataset
    if any(val is not None for val in res.values()):
        res[DatasetTypeEnum.ASHPData] = ashp_task.result()
    logger.info(f"Returning {len(res)} datasets for {site_id}")

    return res


async def list_latest_bundle(site_id: SiteIDWithTime, pool: DatabasePoolDep) -> DatasetList | None:
    """
    List the contents of the latesst bundle to mimic the format of `list-latest-datasets`.

    If there are no bundles, this returns None.

    Parameters
    ----------
    site_id
        Site ID to check available bundles for
    pool
        Database pool to check in

    Returns
    -------
    DatasetList
        Contents of the latest bundle, in the right order, if one exists
    None
        If no bundles exist
    """
    latest_bundle = await pool.fetchrow(
        """
        SELECT
            m.bundle_id,
            ANY_VALUE(start_ts) AS start_ts,
            ANY_VALUE(end_ts) AS end_ts,
            ANY_VALUE(created_at) AS created_at,
            ARRAY_AGG(dataset_type ORDER BY dataset_order ASC) AS dataset_types,
            ARRAY_AGG(dataset_subtype ORDER BY dataset_order ASC) AS dataset_subtypes,
            ARRAY_AGG(dataset_id ORDER BY dataset_order ASC) AS dataset_ids
        FROM data_bundles.metadata AS m
        LEFT JOIN
            data_bundles.dataset_links AS dl
        ON dl.bundle_id = m.bundle_id
        WHERE m.site_id = $1
        GROUP BY m.bundle_id
        ORDER BY created_at DESC
        LIMIT 1""",
        site_id.site_id,
    )
    if latest_bundle is None:
        return None

    bundle_id, start_ts, end_ts, created_at, dataset_types, dataset_subtypes, dataset_ids = latest_bundle

    return DatasetList(
        site_id=site_id.site_id,
        start_ts=start_ts,
        end_ts=end_ts,
        bundle_id=bundle_id,
        SiteBaseline=DatasetEntry(
            dataset_id=dataset_ids[dataset_types.index(DatasetTypeEnum.SiteBaseline)],
            dataset_type=DatasetTypeEnum.SiteBaseline,
            created_at=created_at,
            start_ts=start_ts,
            end_ts=end_ts,
            num_entries=None,
            resolution=None,
            dataset_subtype=dataset_subtypes[dataset_types.index(DatasetTypeEnum.SiteBaseline)],
        )
        if DatasetTypeEnum.SiteBaseline in dataset_types
        else None,
        HeatingLoad=[
            DatasetEntry(
                dataset_id=ds_id,
                dataset_type=ds_type,
                created_at=created_at,
                start_ts=start_ts,
                end_ts=end_ts,
                num_entries=None,
                resolution=None,
                dataset_subtype=ds_subtype,
            )
            for ds_type, ds_subtype, ds_id in zip(dataset_types, dataset_subtypes, dataset_ids, strict=False)
            if ds_type == DatasetTypeEnum.HeatingLoad
        ]
        if DatasetTypeEnum.HeatingLoad in dataset_types
        else None,
        ASHPData=DatasetEntry(
            dataset_id=dataset_ids[dataset_types.index(DatasetTypeEnum.ASHPData)],
            dataset_type=DatasetTypeEnum.ASHPData,
            created_at=created_at,
            start_ts=start_ts,
            end_ts=end_ts,
            num_entries=None,
            resolution=None,
            dataset_subtype=dataset_subtypes[dataset_types.index(DatasetTypeEnum.ASHPData)],
        )
        if DatasetTypeEnum.ASHPData in dataset_types
        else None,
        CarbonIntensity=DatasetEntry(
            dataset_id=dataset_ids[dataset_types.index(DatasetTypeEnum.CarbonIntensity)],
            dataset_type=DatasetTypeEnum.CarbonIntensity,
            created_at=created_at,
            start_ts=start_ts,
            end_ts=end_ts,
            num_entries=None,
            resolution=None,
            dataset_subtype=dataset_subtypes[dataset_types.index(DatasetTypeEnum.CarbonIntensity)],
        )
        if DatasetTypeEnum.CarbonIntensity in dataset_types
        else None,
        ElectricityMeterData=DatasetEntry(
            dataset_id=dataset_ids[dataset_types.index(DatasetTypeEnum.ElectricityMeterData)],
            dataset_type=DatasetTypeEnum.ElectricityMeterData,
            created_at=created_at,
            start_ts=start_ts,
            end_ts=end_ts,
            num_entries=None,
            resolution=None,
            dataset_subtype=dataset_subtypes[dataset_types.index(DatasetTypeEnum.ElectricityMeterData)],
        )
        if DatasetTypeEnum.ElectricityMeterData in dataset_types
        else None,
        ElectricityMeterDataSynthesised=DatasetEntry(
            dataset_id=dataset_ids[dataset_types.index(DatasetTypeEnum.ElectricityMeterDataSynthesised)],
            dataset_type=DatasetTypeEnum.ElectricityMeterDataSynthesised,
            created_at=created_at,
            start_ts=start_ts,
            end_ts=end_ts,
            num_entries=None,
            resolution=None,
            dataset_subtype=dataset_subtypes[dataset_types.index(DatasetTypeEnum.ElectricityMeterDataSynthesised)],
        )
        if DatasetTypeEnum.ElectricityMeterDataSynthesised in dataset_types
        else None,
        ImportTariff=[
            DatasetEntry(
                dataset_id=ds_id,
                dataset_type=ds_type,
                created_at=created_at,
                start_ts=start_ts,
                end_ts=end_ts,
                num_entries=None,
                resolution=None,
                dataset_subtype=ds_subtype,
            )
            for ds_type, ds_subtype, ds_id in zip(dataset_types, dataset_subtypes, dataset_ids, strict=False)
            if ds_type == DatasetTypeEnum.ImportTariff
        ]
        if DatasetTypeEnum.ImportTariff in dataset_types
        else None,
        Weather=None,
        GasMeterData=DatasetEntry(
            dataset_id=dataset_ids[dataset_types.index(DatasetTypeEnum.GasMeterData)],
            dataset_type=DatasetTypeEnum.GasMeterData,
            created_at=created_at,
            start_ts=start_ts,
            end_ts=end_ts,
            num_entries=None,
            resolution=None,
            dataset_subtype=dataset_subtypes[dataset_types.index(DatasetTypeEnum.GasMeterData)],
        )
        if DatasetTypeEnum.GasMeterData in dataset_types
        else None,
        RenewablesGeneration=[
            DatasetEntry(
                dataset_id=ds_id,
                dataset_type=ds_type,
                created_at=created_at,
                start_ts=start_ts,
                end_ts=end_ts,
                num_entries=None,
                resolution=None,
                dataset_subtype=ds_subtype,
            )
            for ds_type, ds_subtype, ds_id in zip(dataset_types, dataset_subtypes, dataset_ids, strict=False)
            if ds_type == DatasetTypeEnum.RenewablesGeneration
        ]
        if DatasetTypeEnum.RenewablesGeneration in dataset_types
        else None,
        ThermalModel=DatasetEntry(
            dataset_id=dataset_ids[dataset_types.index(DatasetTypeEnum.ThermalModel)],
            dataset_type=DatasetTypeEnum.ThermalModel,
            created_at=created_at,
            start_ts=start_ts,
            end_ts=end_ts,
            num_entries=None,
            resolution=None,
            dataset_subtype=dataset_subtypes[dataset_types.index(DatasetTypeEnum.ThermalModel)],
        )
        if DatasetTypeEnum.ThermalModel in dataset_types
        else None,
    )


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
        The ID of the site you are interested in, and the timestamps you want to get them between.

    Returns
    -------
        A {dataset_type: most recent dataset entry} dictionary for each available dataset type.
    """
    # This is our quick bailout if we've got a new-style bundle
    latest_bundle = await list_latest_bundle(params, pool)
    if latest_bundle is not None:
        return latest_bundle
    logger.info("Didn't get a bundle, so separately listing datasets.")
    all_datasets = await list_datasets(params, pool)

    def created_at_or_epoch(ts: DatasetEntry | None) -> datetime.datetime:
        """Return the created_at date or the EPOCH."""
        if ts is None:
            return datetime.datetime(year=1970, month=1, day=1, tzinfo=datetime.UTC)
        return ts.created_at

    def subtype_contains(ds: DatasetEntry | None, subtype: InterventionEnum | SyntheticTariffEnum | None) -> bool:
        if ds is None:
            return False

        if ds.dataset_subtype == subtype:
            return True

        if hasattr(ds.dataset_subtype, "__contains__") and subtype in ds.dataset_subtype:  # type: ignore
            return True

        return False

    def is_single_enum_entry(item: Any) -> bool:
        """Check if this is a list with a single InterventionEnum."""
        if isinstance(item, list) and len(item) == 1 and isinstance(item[0], InterventionEnum):
            return True
        return False

    heating_subtypes = [None, InterventionEnum.Loft, InterventionEnum.DoubleGlazing, InterventionEnum.Cladding]
    heating_subtypes.extend(
        item.dataset_subtype
        for item in all_datasets[DatasetTypeEnum.HeatingLoad]
        if not isinstance(item.dataset_subtype, InterventionEnum)
        and item.dataset_subtype is not None
        and not is_single_enum_entry(item.dataset_subtype)
    )
    heating_loads = [
        item
        for item in (
            max(
                filter(
                    lambda ds: subtype_contains(ds, intervention_subtype),
                    all_datasets[DatasetTypeEnum.HeatingLoad],
                ),
                key=created_at_or_epoch,
                default=None,
            )
            for intervention_subtype in heating_subtypes
        )
        if item is not None
    ]

    import_tariffs = [
        item
        for item in (
            max(
                filter(lambda ds: subtype_contains(ds, tariff_type), all_datasets[DatasetTypeEnum.ImportTariff]),
                key=created_at_or_epoch,
                default=None,
            )
            for tariff_type in [
                SyntheticTariffEnum.Fixed,
                SyntheticTariffEnum.Agile,
                SyntheticTariffEnum.Overnight,
                SyntheticTariffEnum.Peak,
                SyntheticTariffEnum.ShapeShifter,
            ]
        )
        if item is not None
    ]

    # The labelling of dataset_subtypes for solar locations is a bit of a mess, sorry!
    # The subtypes are generally chosen to be the string ID of the solar_location on that site.
    # However, some sites don't have locations assigned: these are given the location "default"
    # Which is a south-ish facing roof with optimal tilt and azimuth for that location.
    # Some sites have had solar generations in the database from before this change to track location
    # was made. These are given the location None to mark that they pre-date the solar locations,
    # this is mostly equivalent to the "default" location but not necessarily.
    # In the case where we get some real solar locations, we ignore the None/"default" data
    # because they've been replaced with actual data, but keep the None/"default" field where
    # we don't have anything better.
    potential_locations: set[str | None] = {item.dataset_subtype for item in all_datasets[DatasetTypeEnum.RenewablesGeneration]}
    if "default" in potential_locations:
        # Relabel the 'default' entry as None for consistency
        potential_locations.remove("default")
        potential_locations.add(None)
    # However, if we've got multiple legitimate locations then we should remove the None location
    if len(potential_locations) >= 2 and None in potential_locations:
        potential_locations.remove(None)
    if DatasetTypeEnum.RenewablesGeneration in all_datasets and all_datasets[DatasetTypeEnum.RenewablesGeneration] is not None:
        renewables_generations = [
            item
            for item in (
                max(
                    filter(
                        lambda ds: bool(ds.dataset_subtype == solar_locn),
                        all_datasets[DatasetTypeEnum.RenewablesGeneration],
                    ),
                    key=created_at_or_epoch,
                    default=None,
                )
                # Get these in a consistent order sorted alphabetically by their location ID
                for solar_locn in sorted(potential_locations, key=str)
            )
            if item is not None
        ]
    else:
        renewables_generations = []

    return DatasetList(
        site_id=params.site_id,
        start_ts=params.start_ts,
        end_ts=params.end_ts,
        SiteBaseline=max(all_datasets[DatasetTypeEnum.SiteBaseline], key=lambda x: x.created_at)
        if all_datasets[DatasetTypeEnum.SiteBaseline]
        else None,
        HeatingLoad=heating_loads,
        ImportTariff=import_tariffs,
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
        RenewablesGeneration=renewables_generations,
        ThermalModel=[max(all_datasets[DatasetTypeEnum.ThermalModel], key=lambda x: x.created_at)]
        if all_datasets.get(DatasetTypeEnum.ThermalModel)
        else None,
    )


@router.post("/get-dataset-bundle", tags=["db", "bundle", "get"])
async def get_dataset_bundle(bundle_id: dataset_id_t, pool: DatabasePoolDep) -> SiteDataEntries:
    """
    Get the datasets available in a specific dataset bundle.

    A bundle is a collection of datasets for a single site, often created at the same time.
    A bundle isn't guaranteed to be complete, but most likely will be.

    Parameters
    ----------
    bundle_id
        The bundle ID of the specific dataset you want
    pool
        Connection pool for the database to get the bundled datasets.

    Returns
    -------
    SiteDataEntries
        Entries for the datasets in the bundle; unavailable entries are None.
    """
    # We order the dataset IDs and types by the same rules
    # to ensure that we get them out at the same order we got them in
    # This is especially important for import tariffs, where tariff index 0 must be "Fixed"
    bundle_row = await pool.fetchrow(
        """
        SELECT
            MIN(m.start_ts) as start_ts,
            MAX(m.end_ts) AS end_ts,
            ARRAY_AGG(dl.dataset_type ORDER BY dl.dataset_type, dl.dataset_order) AS dataset_type,
            ARRAY_AGG(dl.dataset_id ORDER BY dl.dataset_type, dl.dataset_order) AS dataset_id
        FROM data_bundles.metadata AS m
        LEFT JOIN data_bundles.dataset_links AS dl
        ON dl.bundle_id = m.bundle_id
        WHERE m.bundle_id = $1
        GROUP BY m.bundle_id
        LIMIT 1""",
        bundle_id,
    )
    if bundle_row is None:
        raise ValueError(f"Couldn't fetch {bundle_id} as it isn't in the database")
    bundle_start_ts, bundle_end_ts, dataset_types, dataset_ids = bundle_row

    dataset_requests: dict[DatasetTypeEnum, DatasetIDWithTime | MultipleDatasetIDWithTime] = {}
    for dataset_type, dataset_id in zip(dataset_types, dataset_ids, strict=True):
        dataset_type = DatasetTypeEnum(dataset_type)
        if dataset_type in MULTIPLE_DATASET_ENDPOINTS:
            if dataset_type not in dataset_requests:
                dataset_requests[dataset_type] = MultipleDatasetIDWithTime(
                    dataset_id=[dataset_id], start_ts=bundle_start_ts, end_ts=bundle_end_ts
                )
            else:
                dataset_requests[dataset_type].dataset_id.append(dataset_id)  # type: ignore
        else:
            dataset_requests[dataset_type] = DatasetIDWithTime(
                dataset_id=dataset_id, start_ts=bundle_start_ts, end_ts=bundle_end_ts
            )
    return await fetch_all_input_data(dataset_requests, pool=pool)


@router.post("/list-dataset-bundles")
async def list_dataset_bundles(site_id: SiteIDWithTime, pool: DatabasePoolDep) -> list[DatasetBundleMetadata]:
    """
    List all the dataset bundles available for this site.

    This just lists the metadata for the bundles, and not their contents.
    To get the contents, you'll have to call `get-dataset-bundle` with the retrieved ID of each one.

    Parameters
    ----------
    site_id
        Site that you want to list the available datasets for
    pool
        Connection pool to the database storing the datasets

    Returns
    -------
    list[DatasetBundleMetadata]
        A list of the high-level metadata (ID, created_at, start_ts, end_ts) for the available bundles.
    """
    bundle_entries = await pool.fetch(
        """
        SELECT
            m.bundle_id,
            ANY_VALUE(name) AS name,
            ANY_VALUE(site_id) AS site_id,
            ANY_VALUE(start_ts) AS start_ts,
            ANY_VALUE(end_ts) AS end_ts,
            ANY_VALUE(created_at) AS created_at,
            ARRAY_AGG(dataset_type) AS available_datasets
        FROM data_bundles.metadata AS m
        LEFT JOIN
            data_bundles.dataset_links AS dl
        ON dl.bundle_id = m.bundle_id
        WHERE m.site_id = $1
        GROUP BY m.bundle_id""",
        site_id.site_id,
    )
    if bundle_entries is None or not bundle_entries:
        # We got no available bundles for this site, so return an empty list
        return []
    # TODO (2025-05-09): Do we instead want to return something that looks a bit more like a DatasetEntry,
    # in the form {DatasetTypeEnum: dataset_id | list[dataset_id]} ?
    # For now, we just return a list of all the dataset types with some duplicates.
    # We also do this repeated checking for None for the available datasets because we can get Nones
    # from the database in a few cases
    return [
        DatasetBundleMetadata(
            bundle_id=item["bundle_id"],
            name=item["name"],
            site_id=item["site_id"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            created_at=item["created_at"],
            available_datasets=[DatasetTypeEnum(subitem) for subitem in item["available_datasets"] if subitem is not None]
            if item["available_datasets"]
            else [],
        )
        for item in bundle_entries
    ]


@warnings.deprecated("Prefer get-dataset-bundle.")
@router.post("/get-specific-datasets", tags=["db", "get"])
async def get_specific_datasets(site_data: DatasetList | RemoteMetaData, pool: DatabasePoolDep) -> SiteDataEntries:
    """
    Get specific datasets with chosen IDs for a given site.

    If you have not requested a dataset (its entry is None in the DatasetList), then you'll receive None for that dataset.
    The usual workflow is to call list-latest-datasets yourself, look up each dataset in your own cache, and then
    request the get-specific-datasets that you require.
    You should prefer to use get-dataset-bundle.

    Parameters
    ----------
    site_data
        A specification for the required site data; UUIDs of the datasets of each type you wish to request.
        You can hand back either the DatasetList you received from list-latest-datasets, or a RemoteMetaData of dataset IDs
        that you have curated yourself.

    Returns
    -------
        The site data with full time series for each data source
    """
    # If we've received a DatasetList with all the metadata about each dataset, we turn it into
    # a DatasetList here which is just the IDs, which are easier to request.
    if isinstance(site_data, DatasetList):
        new_site_data = RemoteMetaData(site_id=site_data.site_id, start_ts=site_data.start_ts, end_ts=site_data.end_ts)
        for key in DatasetTypeEnum:
            # Model dump will also dump the sub keys from RemoteMetadata into dicts with a "dataset_id" key
            # and some other stuff that we throw away.
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
        # We have to handle multiple dataset requests slightly differently to the single dataset requests.
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
async def get_latest_tariffs(site_data: SiteIDWithTime, pool: DatabasePoolDep) -> EpochTariffEntry:
    """
    Get the latest Import Tariff entries for a given site.

    This will endeavour to get the most recently generated synthetic tariff of each type.
    If a given tariff type isn't in the database, we skip it.
    The Fixed tariff is generally at index 0.

    This is most useful as a sub-call as part of another dataset getting function.

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
    EpochTariffEntry
        Tariff entries in an EPOCH friendly format.
    """
    site_data_info = await list_latest_datasets(site_data, pool=pool)
    if site_data_info.ImportTariff is None:
        logger = logging.getLogger(__name__)
        logger.warning(f"Requested latest tariffs for {site_data.site_id} but None were available.")
        return EpochTariffEntry(timestamps=[], data=[])
    params = MultipleDatasetIDWithTime(
        dataset_id=[item.dataset_id for item in site_data_info.ImportTariff]
        if isinstance(site_data_info.ImportTariff, list)
        else [site_data_info.ImportTariff.dataset_id],
        start_ts=site_data.start_ts,
        end_ts=site_data.end_ts,
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

    try:
        bundle_metas = await list_dataset_bundles(site_id=params, pool=pool)
        latest_bundle = max(bundle_metas, key=lambda bm: bm.created_at).bundle_id
        return await get_dataset_bundle(bundle_id=latest_bundle, pool=pool)
    except ValueError as ex:
        logger.warning(f"Could not get a latest bundle for {params.site_id} due to {ex}, falling back.")
        pass

    site_data = await list_latest_datasets(params, pool=pool)
    try:
        return await get_specific_datasets(site_data, pool)
    except KeyError as ex:
        raise HTTPException(400, f"Missing dataset {ex}. Did you run generate-all for this site?") from ex


async def generate_all_wrapper(
    pool: DatabasePoolDep,
    http_client: HttpClientDep,
    secrets_env: SecretsDep,
    vae: VaeDep,
    to_generate: to_generate_t,
    bundle_metadata: DatasetBundleMetadata,
) -> None:
    """
    Set the generate all tasks running as part of a TaskGroup.

    This takes in a number of requests, many of which will be IO-bound, and creates a taskgroup to complete
    them in any order.
    This is asynchronous but not parallel due to the stateful database pool and HTTP client dependencies.

    Parameters
    ----------
    pool
        Database connection pool to write results to
    http_client
        HTTP connection pool to contact external parties with
    secrets_env
        Secrets environment featuring API keys
    vae
        Electricity upscaling model
    to_generate
        Dictionary of dataset types and associated requests for generation
    bundle_metadata
        Information about the bundle that these are going to be associated with

    Returns
    -------
    None
    """
    all_tasks: list[Task] = []
    async with asyncio.TaskGroup() as tg:
        for hload_req in to_generate[DatasetTypeEnum.HeatingLoad]:
            assert isinstance(hload_req, HeatingLoadRequest)
            all_tasks.append(tg.create_task(generate_heating_load(hload_req, pool, http_client)))

        for solar_req in to_generate[DatasetTypeEnum.RenewablesGeneration]:
            assert isinstance(solar_req, RenewablesRequest)
            all_tasks.append(tg.create_task(generate_renewables_generation(solar_req, pool, http_client, secrets_env)))

        for tariff_req in to_generate[DatasetTypeEnum.ImportTariff]:
            assert isinstance(tariff_req, TariffRequest)
            all_tasks.append(
                tg.create_task(
                    generate_import_tariffs(tariff_req, pool=pool, http_client=http_client), name=tariff_req.tariff_name
                )
            )

        elec_req = cast(ElectricalLoadRequest, to_generate[DatasetTypeEnum.ElectricityMeterDataSynthesised])
        all_tasks.append(tg.create_task(generate_electricity_load(elec_req, vae=vae, pool=pool, http_client=http_client)))

        ci_req = cast(GridCO2Request, to_generate[DatasetTypeEnum.CarbonIntensity])
        all_tasks.append(tg.create_task(generate_grid_co2(ci_req, pool=pool, http_client=http_client)))

        await file_self_with_bundle(
            pool,
            BundleEntryMetadata(
                bundle_id=bundle_metadata.bundle_id,
                dataset_id=NULL_UUID,
                dataset_type=DatasetTypeEnum.ASHPData,
                dataset_subtype=None,
            ),
        )

    _ = [task.result() for task in all_tasks]


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
    bundle_metadata = DatasetBundleMetadata(
        bundle_id=uuid7(),
        name=None,
        site_id=params.site_id,
        start_ts=params.start_ts,
        end_ts=params.end_ts,
        available_datasets=[],  # Leave this empty to start and we'll fill it in as we go along
    )
    # File the metadata before we do anything else
    await insert_dataset_bundle(bundle_metadata=bundle_metadata, pool=pool)

    async with asyncio.TaskGroup() as tg:
        gas_dataset_task = tg.create_task(
            pool.fetchrow(
                """
            SELECT
                m.dataset_id,
                MIN(gm.start_ts) AS start_ts,
                MAX(gm.end_ts) AS end_ts
            FROM client_meters.metadata AS m
            LEFT JOIN client_meters.gas_meters AS gm
            ON gm.dataset_id = m.dataset_id
            WHERE site_id = $1 AND fuel_type = 'gas' AND NOT is_synthesised
            GROUP BY m.dataset_id
            ORDER BY created_at DESC
            LIMIT 1""",
                params.site_id,
            )
        )
        elec_meter_dataset_task = tg.create_task(
            pool.fetchval(
                """
            SELECT dataset_id FROM client_meters.metadata
            WHERE site_id = $1 AND fuel_type = 'elec' AND NOT is_synthesised
            ORDER BY created_at DESC
            LIMIT 1""",
                params.site_id,
            )
        )

        baseline_task = tg.create_task(
            pool.fetchval(
                """SELECT baseline_id FROM client_info.site_baselines
                          WHERE site_id = $1 ORDER BY created_at DESC LIMIT 1""",
                params.site_id,
            )
        )
    gas_result = gas_dataset_task.result()
    elec_meter_dataset_id = elec_meter_dataset_task.result()
    baseline_id = baseline_task.result()
    if gas_result is None:
        raise HTTPException(400, f"No gas meter data for {params.site_id}.")
    if elec_meter_dataset_id is None:
        raise HTTPException(400, f"No electrical meter data for {params.site_id}.")

    if baseline_id is not None:
        await file_self_with_bundle(
            pool,
            BundleEntryMetadata(
                bundle_id=bundle_metadata.bundle_id,
                dataset_id=elec_meter_dataset_id,
                dataset_type=DatasetTypeEnum.SiteBaseline,
                dataset_subtype=None,
            ),
        )
    gas_meter_dataset_id, gas_start_ts, gas_end_ts = gas_result

    # Attach the two meter datasets we've used to this bundle
    async with asyncio.TaskGroup() as tg:
        gas_task_handle = tg.create_task(
            file_self_with_bundle(
                pool,
                BundleEntryMetadata(
                    bundle_id=bundle_metadata.bundle_id,
                    dataset_id=gas_meter_dataset_id,
                    dataset_type=DatasetTypeEnum.GasMeterData,
                    dataset_subtype=None,
                ),
            )
        )
        elec_task_handle = tg.create_task(
            file_self_with_bundle(
                pool,
                BundleEntryMetadata(
                    bundle_id=bundle_metadata.bundle_id,
                    dataset_id=elec_meter_dataset_id,
                    dataset_type=DatasetTypeEnum.ElectricityMeterData,
                    dataset_subtype=None,
                ),
            )
        )
    # We have to get the weather into the database before we try to do any fitting,
    # especially over the requested and gas meter time periods.
    location = await get_location(params, pool)
    async with asyncio.TaskGroup() as tg:
        params_weather_task = tg.create_task(
            get_weather(
                WeatherRequest(location=location, start_ts=params.start_ts, end_ts=params.end_ts),
                pool=pool,
                http_client=http_client,
            )
        )
        gas_weather_task = tg.create_task(
            get_weather(
                WeatherRequest(location=location, start_ts=gas_start_ts, end_ts=gas_end_ts),
                pool=pool,
                http_client=http_client,
            )
        )
    _ = [params_weather_task.result(), gas_weather_task.result()]
    # Most of these are single datasets, but prime the list of desired UUIDs with empty lists
    # for the cases where we'll need them.
    all_requests: to_generate_t = {}
    POTENTIAL_INTERVENTIONS = [[], [InterventionEnum.Loft], [InterventionEnum.DoubleGlazing], [InterventionEnum.Cladding]]
    hload_reqs: list[RequestBase] = []
    for idx, interventions in enumerate(POTENTIAL_INTERVENTIONS):
        req = HeatingLoadRequest(
            dataset_id=gas_meter_dataset_id,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            interventions=interventions,
            bundle_metadata=BundleEntryMetadata(
                bundle_id=bundle_metadata.bundle_id,
                dataset_id=uuid7(),
                dataset_type=DatasetTypeEnum.HeatingLoad,
                dataset_subtype=interventions,
                dataset_order=idx,
            ),
        )
        hload_reqs.append(req)
    all_requests[DatasetTypeEnum.HeatingLoad] = hload_reqs

    grid_req = GridCO2Request(
        site_id=params.site_id,
        start_ts=params.start_ts,
        end_ts=params.end_ts,
        bundle_metadata=BundleEntryMetadata(
            bundle_id=bundle_metadata.bundle_id,
            dataset_id=uuid7(),
            dataset_type=DatasetTypeEnum.CarbonIntensity,
            dataset_subtype=None,
        ),
    )
    all_requests[DatasetTypeEnum.CarbonIntensity] = grid_req

    # We generate five different types of tariff, here done manually to keep track of the
    # tasks and not lose the handle to the task (which causes mysterious bugs)
    # Note that the order here doesn't matter, we just explicitly list them so it's clear what is going on.
    tariff_reqs: list[TariffRequest] = []
    CHOSEN_TARIFFS = [
        SyntheticTariffEnum.Fixed,
        SyntheticTariffEnum.Agile,
        SyntheticTariffEnum.Peak,
        SyntheticTariffEnum.Overnight,
        # SyntheticTariffEnum.ShapeShifter,
    ]
    for idx, tariff_type in enumerate(CHOSEN_TARIFFS):
        tariff_reqs.append(
            TariffRequest(
                site_id=params.site_id,
                tariff_name=tariff_type,
                start_ts=params.start_ts,
                end_ts=params.end_ts,
                bundle_metadata=BundleEntryMetadata(
                    bundle_id=bundle_metadata.bundle_id,
                    dataset_id=uuid7(),
                    dataset_type=DatasetTypeEnum.ImportTariff,
                    dataset_subtype=tariff_type,
                    dataset_order=idx,
                ),
            )
        )
    all_requests[DatasetTypeEnum.ImportTariff] = tariff_reqs

    solar_locns = await get_solar_locations(SiteID(site_id=params.site_id), pool=pool)
    if not solar_locns:
        # This site doesn't have any solar locations specified so use a sensible default.
        DEFAULT_SOLAR_LOCN = SolarLocation(
            site_id=params.site_id,
            name="Default",
            renewables_location_id="default",
            azimuth=None,
            tilt=None,
            maxpower=float("inf"),
        )
        solar_locns = [DEFAULT_SOLAR_LOCN]

    renewables_reqs: list[RenewablesRequest] = []
    for idx, solar_location in enumerate(solar_locns):
        renewables_req = RenewablesRequest(
            site_id=params.site_id,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            azimuth=solar_location.azimuth,
            tilt=solar_location.tilt,
            renewables_location_id=solar_location.renewables_location_id,
            bundle_metadata=BundleEntryMetadata(
                bundle_id=bundle_metadata.bundle_id,
                dataset_id=uuid7(),
                dataset_type=DatasetTypeEnum.RenewablesGeneration,
                dataset_subtype=solar_location.renewables_location_id,
                dataset_order=idx,
            ),
        )
        renewables_reqs.append(renewables_req)
    all_requests[DatasetTypeEnum.RenewablesGeneration] = renewables_reqs

    elec_req = ElectricalLoadRequest(
        dataset_id=elec_meter_dataset_id,
        start_ts=params.start_ts,
        end_ts=params.end_ts,
        bundle_metadata=BundleEntryMetadata(
            bundle_id=bundle_metadata.bundle_id,
            dataset_id=uuid7(),
            dataset_type=DatasetTypeEnum.ElectricityMeterDataSynthesised,
            dataset_subtype=None,
        ),
    )
    all_requests[DatasetTypeEnum.ElectricityMeterDataSynthesised] = elec_req

    RESOLUTION = datetime.timedelta(minutes=30)
    # These UUIDs are correct, but the metadata may change slightly (e.g. the created_at provided here is only an estimate).
    # We know that none of the requests here have bundle_metadatas of None, as we've specifically assigned them
    to_generate: dict[DatasetTypeEnum, DatasetEntry | list[DatasetEntry]] = {
        DatasetTypeEnum.HeatingLoad: [
            DatasetEntry(
                dataset_id=cast(HeatingLoadRequest, ds_meta).bundle_metadata.dataset_id,  # type: ignore
                dataset_type=DatasetTypeEnum.HeatingLoad,
                created_at=datetime.datetime.now(tz=datetime.UTC),
                resolution=RESOLUTION,
                start_ts=params.start_ts,
                end_ts=params.end_ts,
                num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
                dataset_subtype=cast(HeatingLoadRequest, ds_meta).interventions,
            )
            for ds_meta in all_requests[DatasetTypeEnum.HeatingLoad]
        ],
        DatasetTypeEnum.CarbonIntensity: DatasetEntry(
            dataset_id=all_requests[DatasetTypeEnum.CarbonIntensity].bundle_metadata.dataset_id,  # type: ignore
            dataset_type=DatasetTypeEnum.CarbonIntensity,
            created_at=datetime.datetime.now(tz=datetime.UTC),
            resolution=RESOLUTION,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
        ),
        DatasetTypeEnum.ImportTariff: [
            DatasetEntry(
                dataset_id=ds_meta.bundle_metadata.dataset_id,  # type: ignore
                dataset_type=DatasetTypeEnum.ImportTariff,
                created_at=datetime.datetime.now(tz=datetime.UTC),
                dataset_subtype=cast(TariffRequest, ds_meta).tariff_name,
                resolution=RESOLUTION,
                start_ts=params.start_ts,
                end_ts=params.end_ts,
                num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
            )
            for ds_meta in all_requests[DatasetTypeEnum.ImportTariff]
        ],
        # Renewables generation is one series per potential location
        DatasetTypeEnum.RenewablesGeneration: [
            DatasetEntry(
                dataset_id=ds_meta.bundle_metadata.dataset_id,  # type: ignore
                dataset_type=DatasetTypeEnum.RenewablesGeneration,
                created_at=datetime.datetime.now(tz=datetime.UTC),
                resolution=RESOLUTION,
                start_ts=params.start_ts,
                end_ts=params.end_ts,
                num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
            )
            for ds_meta in all_requests[DatasetTypeEnum.RenewablesGeneration]
        ],
        DatasetTypeEnum.ElectricityMeterDataSynthesised: DatasetEntry(
            dataset_id=all_requests[DatasetTypeEnum.ElectricityMeterDataSynthesised].bundle_metadata.dataset_id,  # type: ignore
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

    background_tasks.add_task(
        generate_all_wrapper, pool, http_client, secrets_env, vae, all_requests, bundle_metadata=bundle_metadata
    )

    # Check that the gas and electricity metadata tasks were handled okay before we tidy up
    _ = [gas_task_handle.result(), elec_task_handle.result()]
    return to_generate
