"""Lazy endpoints for bundling everything together."""

import asyncio
import datetime
import json
import logging
import uuid
import warnings
from collections.abc import Sequence

from fastapi import APIRouter, HTTPException

from app.models.import_tariffs import TariffMetadata, TariffProviderEnum
from app.routers.client_data import get_baseline

from ..dependencies import DatabasePoolDep
from ..internal.epl_typing import Jsonable
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
from ..lifespan import JobQueueDep
from ..models.carbon_intensity import GridCO2Request
from ..models.client_data import SiteDataEntries, SolarLocation
from ..models.core import (
    BundleEntryMetadata,
    DatasetEntry,
    DatasetID,
    DatasetIDWithTime,
    DatasetTypeEnum,
    MultipleDatasetIDWithTime,
    RequestBase,
    SiteID,
    SiteIDWithTime,
    dataset_id_t,
)
from ..models.electricity_load import ElectricalLoadRequest
from ..models.heating_load import (
    HeatingLoadMetadata,
    HeatingLoadModelEnum,
    HeatingLoadRequest,
    InterventionEnum,
)
from ..models.import_tariffs import EpochTariffEntry, SyntheticTariffEnum, TariffRequest
from ..models.renewables import RenewablesRequest
from ..models.site_manager import BundleHints, DatasetBundleMetadata, DatasetList, SiteDataEntry
from .client_data import get_solar_locations
from .import_tariffs import get_import_tariffs

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


@router.post("/list-bundle-contents", tags=["db", "bundle"])
async def list_bundle_contents(bundle_id: dataset_id_t, pool: DatabasePoolDep) -> DatasetList | None:
    """
    List the contents of the a bundle to mimic the format of `list-datasets`.

    If there is not a bundle with this ID, this returns None.
    This gives you more metadata about each entry than the `list-dataset-bundles` without actually
    returning all of the entries within a bundle.

    Parameters
    ----------
    bundle_id
         Bundle ID to list the contents of
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
            ANY_VALUE(site_id) AS site_id,
            ARRAY_AGG(dataset_type ORDER BY dataset_order ASC) AS dataset_types,
            ARRAY_AGG(dataset_subtype ORDER BY dataset_order ASC) AS dataset_subtypes,
            ARRAY_AGG(dataset_id ORDER BY dataset_order ASC) AS dataset_ids
        FROM data_bundles.metadata AS m
        LEFT JOIN
            data_bundles.dataset_links AS dl
        ON dl.bundle_id = m.bundle_id
        WHERE m.bundle_id = $1
        GROUP BY m.bundle_id
        ORDER BY created_at DESC
        LIMIT 1""",
        bundle_id,
    )
    if latest_bundle is None:
        return None

    bundle_id, start_ts, end_ts, created_at, site_id, dataset_types, dataset_subtypes, dataset_ids = latest_bundle

    RESOLUTION = datetime.timedelta(minutes=30)
    NUM_ENTRIES = (end_ts - start_ts) / RESOLUTION

    return DatasetList(
        site_id=site_id,
        start_ts=start_ts,
        end_ts=end_ts,
        bundle_id=bundle_id,
        SiteBaseline=DatasetEntry(
            dataset_id=dataset_ids[dataset_types.index(DatasetTypeEnum.SiteBaseline)],
            dataset_type=DatasetTypeEnum.SiteBaseline,
            created_at=created_at,
            start_ts=start_ts,
            end_ts=end_ts,
            num_entries=NUM_ENTRIES,
            resolution=RESOLUTION,
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
                num_entries=NUM_ENTRIES,
                resolution=RESOLUTION,
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
            num_entries=NUM_ENTRIES,
            resolution=RESOLUTION,
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
            num_entries=NUM_ENTRIES,
            resolution=RESOLUTION,
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
            num_entries=NUM_ENTRIES,
            resolution=RESOLUTION,
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
            num_entries=NUM_ENTRIES,
            resolution=RESOLUTION,
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
                num_entries=NUM_ENTRIES,
                resolution=RESOLUTION,
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
            num_entries=NUM_ENTRIES,
            resolution=RESOLUTION,
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
                num_entries=NUM_ENTRIES,
                resolution=RESOLUTION,
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
            num_entries=NUM_ENTRIES,
            resolution=RESOLUTION,
            dataset_subtype=dataset_subtypes[dataset_types.index(DatasetTypeEnum.ThermalModel)],
        )
        if DatasetTypeEnum.ThermalModel in dataset_types
        else None,
    )


@router.post("/list-latest-datasets", tags=["db", "list"])
async def list_latest_datasets(site_id: SiteID, pool: DatabasePoolDep) -> DatasetList:
    """
    Get the most recent datasets of each type for this site.

    This endpoint is the main one you'd want to call if you are interested in running EPOCH.
    Note that you may still need to call `generate-*` if the datasets in here are too old, or
    not listed at all.

    Parameters
    ----------
    site_id
        The ID of the site you are interested in.

    Returns
    -------
        A {dataset_type: most recent dataset entry} dictionary for each available dataset type.
    """
    bundles = await list_dataset_bundles(site_id, pool)
    if not bundles:
        raise HTTPException(404, f"Didn't find any bundled datasets for {site_id.site_id}, try generating some.")

    latest_bundle_id = max(bundles, key=lambda x: x.created_at).bundle_id
    bundle_contents = await list_bundle_contents(latest_bundle_id, pool)
    if bundle_contents is None:
        raise HTTPException(404, f"Didn't find any bundled datasets for {site_id.site_id}, try generating some.")
    return bundle_contents


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
            ARRAY_AGG(dl.dataset_id ORDER BY dl.dataset_type, dl.dataset_order) AS dataset_id,
            ARRAY_AGG(dl.dataset_order ORDER BY dl.dataset_type, dl.dataset_order) AS dataset_order
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
    bundle_start_ts, bundle_end_ts, dataset_types, dataset_ids, _ = bundle_row

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
async def list_dataset_bundles(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetBundleMetadata]:
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
        GROUP BY m.bundle_id
        ORDER BY created_at ASC""",
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
async def get_specific_datasets(site_data: DatasetList | SiteDataEntry, pool: DatabasePoolDep) -> SiteDataEntries:
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
        new_site_data = SiteDataEntry(site_id=site_data.site_id, start_ts=site_data.start_ts, end_ts=site_data.end_ts)

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
async def get_latest_datasets(site_id: SiteID, pool: DatabasePoolDep) -> SiteDataEntries:
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
    logger.info(f"Getting latest dataset list for {site_id.site_id}")

    bundle_metas = await list_dataset_bundles(site_id=site_id, pool=pool)
    latest_bundle = max(bundle_metas, key=lambda bm: bm.created_at).bundle_id
    return await get_dataset_bundle(bundle_id=latest_bundle, pool=pool)


@router.post("/create-bundle", tags=["db", "bundle"])
async def create_bundle(bundle_metadata: DatasetBundleMetadata, pool: DatabasePoolDep) -> dataset_id_t:
    """
    Create a new bundle in the database.

    This is only used when creating a bundle from an external source, probably an API user.

    Parameters
    ----------
    bundle_metadata
        Information about the bundle, including a unique ID and timestamps, to create
    pool
        Database pool to create the bundle in

    Returns
    -------
    dataset_id_t
        The ID of the newly created bundle.
    """
    resp = await insert_dataset_bundle(bundle_metadata, pool)
    return resp


@router.post("/list-queue-contents")
async def list_queue_contents(queue: JobQueueDep, bundle_id: dataset_id_t | None = None) -> list[dict[str, Jsonable]]:
    """
    List the current contents of the queue.

    This will return the requests that we're hoping to tackle in the order we're going to tackle them.
    It'll provide the JSON data so may not be round-trippable.
    Requests from different bundle generation requests might have been mixed together.

    Parameters
    ----------
    queue
        Job queue to report on
    bundle_id
        If dataset_id, return only the queued tasks that are part of this bundle
        If None, return everything in the queue.

    Returns
    -------
    list[dict[str, Jsonable]]
        list of JSON-ified requests that we're going to inspect.
    """
    # TODO (2025-08-28 MHJB): do we want to return a tuple including the type?

    # We sneakily access the private attribute, don't tell anyone
    assert hasattr(queue, "_queue"), "Queue internal queue not yet initialised"

    queue_components = queue.items()

    if bundle_id is None:
        # We do this weird JSON two-step to make sure that we've got a JSONable thing
        # otherwise some sub-components don't dump correctly
        return [json.loads(item.model_dump_json()) for item in queue_components]

    return [
        json.loads(x.model_dump_json())
        for x in queue_components
        if isinstance(x, RequestBase) and x.bundle_metadata is not None and x.bundle_metadata.bundle_id == bundle_id
    ]


@router.post("/generate-all")
async def generate_all(params: SiteIDWithTime, pool: DatabasePoolDep, queue: JobQueueDep) -> DatasetList:
    """
    Run all dataset generation tasks for this site.

    This includes heating load, grid CO2, electrical load, carbon intensity and solar PV.
    Currently it uses a simple tariff that covers a long period of time, and optimal solar PV parameters.
    You almost certainly want the timestamps to be 2021 or 2022 so we can use renewables.ninja data, and relatively recent
    tariff data.

    This will run background tasks for each sub item, which can take upwards of 1 minute.
    For that reason, we'll return an empty set of null data early and chug along in the background.

    Parameters
    ----------
    params
        SiteIDWithTime, including two relatively far back timestamps for Renewables Ninja to use.
    pool
        Connection pool to underlying PostgreSQL database
    queue
        Task queue to submit to

    Returns
    -------
    datasets
        Dataset Type: Dataset Entry mapping, but with placeholder null UUIDs as the background tasks need to run.
        Note that this will return immediately, and will take some time to generate.
        Use `list-queue-contents` to check how things are going.
        We'll also tell you about the bundle in BundleEntryMetadata.
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
            pool.fetchval(
                """
            SELECT
                dataset_id
            FROM client_meters.metadata
            WHERE site_id = $1 AND fuel_type = 'gas' AND NOT is_synthesised
            ORDER BY created_at DESC
            LIMIT 1""",
                params.site_id,
            )
        )
        elec_meter_dataset_task = tg.create_task(
            pool.fetchval(
                """
            SELECT
                dataset_id
            FROM client_meters.metadata
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
    gas_meter_dataset_id = gas_dataset_task.result()
    elec_meter_dataset_id = elec_meter_dataset_task.result()
    baseline_id = baseline_task.result()
    if gas_meter_dataset_id is None:
        raise HTTPException(400, f"No gas meter data for {params.site_id}.")
    if elec_meter_dataset_id is None:
        raise HTTPException(400, f"No electrical meter data for {params.site_id}.")

    if baseline_id is not None:
        await file_self_with_bundle(
            pool,
            BundleEntryMetadata(
                bundle_id=bundle_metadata.bundle_id,
                dataset_id=baseline_id,
                dataset_type=DatasetTypeEnum.SiteBaseline,
                dataset_subtype=None,
            ),
        )

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
    # Most of these are single datasets, but prime the list of desired UUIDs with empty lists
    # for the cases where we'll need them.
    POTENTIAL_INTERVENTIONS = [[], [InterventionEnum.Loft], [InterventionEnum.DoubleGlazing], [InterventionEnum.Cladding]]
    hload_reqs = []
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
        await queue.put(req)
        hload_reqs.append(req)

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
    await queue.put(grid_req)

    # We generate five different types of tariff, here done manually to keep track of the
    # tasks and not lose the handle to the task (which causes mysterious bugs)
    # Note that the order here doesn't matter, we just explicitly list them so it's clear what is going on.
    CHOSEN_TARIFFS = [
        SyntheticTariffEnum.Fixed,
        SyntheticTariffEnum.Agile,
        SyntheticTariffEnum.Peak,
        SyntheticTariffEnum.Overnight,
        # SyntheticTariffEnum.ShapeShifter,
    ]
    tariff_reqs = []
    for idx, tariff_type in enumerate(CHOSEN_TARIFFS):
        tariff_req = TariffRequest(
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
        await queue.put(tariff_req)
        tariff_reqs.append(tariff_req)

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

    solar_reqs = []
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
        await queue.put(renewables_req)
        solar_reqs.append(renewables_req)

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
    await queue.put(elec_req)

    # File the dummy ASHP datasets as part of the bundle
    await file_self_with_bundle(
        pool,
        BundleEntryMetadata(
            bundle_id=bundle_metadata.bundle_id,
            dataset_id=NULL_UUID,
            dataset_type=DatasetTypeEnum.ASHPData,
            dataset_subtype=None,
        ),
    )
    # Check that the gas and electricity metadata tasks were handled okay before we tidy up
    _ = [gas_task_handle.result(), elec_task_handle.result()]

    RESOLUTION = datetime.timedelta(minutes=30)
    # These UUIDs are correct, but the metadata may change slightly (e.g. the created_at provided here is only an estimate).
    # We know that none of the requests here have bundle_metadatas of None, as we've specifically assigned them
    return DatasetList(
        site_id=params.site_id,
        start_ts=params.start_ts,
        end_ts=params.end_ts,
        bundle_id=bundle_metadata.bundle_id,
        SiteBaseline=DatasetEntry(
            dataset_id=baseline_id,
            dataset_type=DatasetTypeEnum.SiteBaseline,
            created_at=datetime.datetime.now(tz=datetime.UTC),
            resolution=RESOLUTION,
            start_ts=None,
            end_ts=None,
            num_entries=None,
            dataset_subtype=None,
        )
        if baseline_id is not None
        else None,
        HeatingLoad=[
            DatasetEntry(
                dataset_id=ds_meta.bundle_metadata.dataset_id,  # type: ignore
                dataset_type=DatasetTypeEnum.HeatingLoad,
                created_at=datetime.datetime.now(tz=datetime.UTC),
                resolution=RESOLUTION,
                start_ts=params.start_ts,
                end_ts=params.end_ts,
                num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
                dataset_subtype=ds_meta.interventions,
            )
            for ds_meta in hload_reqs
        ],
        ASHPData=DatasetEntry(
            dataset_id=NULL_UUID,
            dataset_type=DatasetTypeEnum.ASHPData,
            created_at=datetime.datetime.now(tz=datetime.UTC),
            resolution=RESOLUTION,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
        ),
        CarbonIntensity=DatasetEntry(
            dataset_id=grid_req.bundle_metadata.dataset_id,  # type: ignore
            dataset_type=DatasetTypeEnum.CarbonIntensity,
            created_at=datetime.datetime.now(tz=datetime.UTC),
            resolution=RESOLUTION,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
        ),
        ElectricityMeterDataSynthesised=DatasetEntry(
            dataset_id=elec_req.bundle_metadata.dataset_id,  # type: ignore
            dataset_type=DatasetTypeEnum.ElectricityMeterDataSynthesised,
            created_at=datetime.datetime.now(tz=datetime.UTC),
            resolution=RESOLUTION,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
        ),
        ImportTariff=[
            DatasetEntry(
                dataset_id=ds_meta.bundle_metadata.dataset_id,  # type: ignore
                dataset_type=DatasetTypeEnum.ImportTariff,
                created_at=datetime.datetime.now(tz=datetime.UTC),
                dataset_subtype=ds_meta.tariff_name,
                resolution=RESOLUTION,
                start_ts=params.start_ts,
                end_ts=params.end_ts,
                num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
            )
            for ds_meta in tariff_reqs
        ],
        # for the meters, return the ID but don't bother to check the other stuff
        ElectricityMeterData=DatasetEntry(
            dataset_id=elec_meter_dataset_id,
            dataset_type=DatasetTypeEnum.ElectricityMeterData,
            created_at=datetime.datetime.now(tz=datetime.UTC),
            resolution=None,
            start_ts=None,
            end_ts=None,
            num_entries=None,
            dataset_subtype=None,
        )
        if elec_meter_dataset_id is not None
        else None,
        GasMeterData=DatasetEntry(
            dataset_id=gas_meter_dataset_id,
            dataset_type=DatasetTypeEnum.GasMeterData,
            created_at=datetime.datetime.now(tz=datetime.UTC),
            resolution=None,
            start_ts=None,
            end_ts=None,
            num_entries=None,
            dataset_subtype=None,
        )
        if gas_meter_dataset_id is not None
        else None,
        RenewablesGeneration=[
            DatasetEntry(
                dataset_id=ds_meta.bundle_metadata.dataset_id,  # type: ignore
                dataset_type=DatasetTypeEnum.RenewablesGeneration,
                created_at=datetime.datetime.now(tz=datetime.UTC),
                resolution=RESOLUTION,
                start_ts=params.start_ts,
                end_ts=params.end_ts,
                num_entries=(params.end_ts - params.start_ts) // RESOLUTION,
            )
            for ds_meta in solar_reqs
        ],
        # We don't know these yet, but they'll be handled by the bundles elsewhere
        Weather=None,
        ThermalModel=None,
        PHPP=None,
    )


@router.post("/get-bundle-hints", tags=["db", "bundle"])
async def get_bundle_hints(bundle_id: dataset_id_t, pool: DatabasePoolDep) -> BundleHints:
    """
    Get hints about the data within this bundle that will be useful for the GUI.

    Hints are the metadata about each bundled dataset that were created when initially generated them.
    This may include human readable names, quality scores, or generation methods.
    These are listed according to the internal `dataset_order` variable so the lists of hints are always
    in the same order to the actual datasets, e.g. tariff hint 0 is the same as tariff data 0.

    Parameters
    ----------
    bundle_id
        The ID of the bundle to get hints for

    pool
        Database pool to check for bundle data in

    Returns
    -------
    BundleHints
        Information about renewables, tariffs, baseline and heating to communicate in the GUI.
    """
    bundle_meta = await list_bundle_contents(bundle_id=bundle_id, pool=pool)
    assert bundle_meta is not None

    if bundle_meta.SiteBaseline is not None:
        baseline_id = bundle_meta.SiteBaseline.dataset_id
        baseline = await get_baseline(site_or_dataset_id=DatasetID(dataset_id=baseline_id), pool=pool)
    else:
        baseline = None

    if isinstance(bundle_meta.ImportTariff, list):
        tariff_recs = await pool.fetch(
            """
            SELECT
                tm.dataset_id,
                dataset_order,
                tm.provider,
                tm.product_name,
                tm.tariff_name,
                tm.valid_from,
                tm.valid_to
            FROM data_bundles.dataset_links AS dl
            LEFT JOIN data_bundles.metadata AS dm
                on dl.bundle_id = dm.bundle_id
            LEFT JOIN tariffs.metadata AS tm
                ON dl.dataset_id = tm.dataset_id
            WHERE
                dataset_type = 'ImportTariff' AND dm.bundle_id = $1
            ORDER BY dataset_order ASC""",
            bundle_id,
        )
        tariff_hints = [
            TariffMetadata(
                dataset_id=item["dataset_id"],
                site_id=bundle_meta.site_id,
                provider=TariffProviderEnum(item["provider"]),
                product_name=str(item["product_name"]),
                tariff_name=str(item["tariff_name"]),
                valid_from=item["valid_from"],
                valid_to=item["valid_to"],
            )
            for item in tariff_recs
        ]
    else:
        tariff_hints = None

    if bundle_meta.RenewablesGeneration is not None:
        solar_locns_rec = await pool.fetch(
            """
            SELECT
                dataset_id,
                dataset_order,
                renewables_location_id,
                sl.name,
                sl.mounting_type,
                sl.tilt,
                sl.azimuth,
                sl.maxpower
            FROM data_bundles.dataset_links AS dl
            LEFT JOIN data_bundles.metadata AS dm
                on dl.bundle_id = dm.bundle_id
            LEFT JOIN client_info.solar_locations AS sl
                ON sl.renewables_location_id = REPLACE(dl.dataset_subtype, '"', '')
            WHERE dataset_type = 'RenewablesGeneration' AND dm.bundle_id = $1
            ORDER BY dataset_order ASC;""",
            bundle_id,
        )
        renewables_hints = [
            SolarLocation(
                site_id=bundle_meta.site_id,
                renewables_location_id=item["renewables_location_id"],
                name=item["name"],
                azimuth=item["azimuth"],
                tilt=item["tilt"],
                maxpower=item["maxpower"],
            )
            for item in solar_locns_rec
        ]
    else:
        renewables_hints = None

    if bundle_meta.HeatingLoad is not None:
        heating_recs = await pool.fetch(
            """
            SELECT
                hm.dataset_id,
                dataset_order,
                hm.interventions,
                hm.params,
                hm.peak_hload,
                hm.created_at,
                hm.params['generation_method'] AS generation_method
            FROM data_bundles.dataset_links AS dl
            LEFT JOIN data_bundles.metadata AS dm
                on dl.bundle_id = dm.bundle_id
            LEFT JOIN heating.metadata AS hm
                ON dl.dataset_id = hm.dataset_id
            WHERE dataset_type = 'HeatingLoad' AND dm.bundle_id = $1
            ORDER BY dataset_order ASC;""",
            bundle_id,
        )
        heating_hints = [
            HeatingLoadMetadata(
                site_id=bundle_meta.site_id,
                dataset_id=item["dataset_id"],
                created_at=item["created_at"],
                params=item["params"],
                interventions=item["interventions"],
                generation_method=HeatingLoadModelEnum(item["generation_method"].replace('"', "")),
                peak_hload=item["peak_hload"],
            )
            for item in heating_recs
        ]
    else:
        heating_hints = None
    return BundleHints(baseline=baseline, tariffs=tariff_hints, renewables=renewables_hints, heating=heating_hints)
