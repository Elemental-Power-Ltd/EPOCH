import asyncio
import logging
import operator
from datetime import datetime
from typing import cast

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import UUID7, AwareDatetime

from app.dependencies import HTTPClient
from app.models.core import Site, Task
from app.models.database import BundleMetadata, bundle_id_t, dataset_id_t
from app.models.simulate import EpochInputData, LegacyResultReproConfig
from app.models.site_data import (
    DatasetTypeEnum,
    EpochSiteData,
    LegacySiteMetaData,
    SiteDataEntries,
    SiteMetaData,
    site_metadata_t,
)

from .results import get_result_configuration
from .utils import _DB_URL

logger = logging.getLogger("default")


async def fetch_portfolio_data(task: Task, http_client: HTTPClient) -> None:
    """
    Fetch task site data.

    Parameters
    ----------
    task
        Task to fetch site data for.
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
    None
    """
    try:
        async with asyncio.TaskGroup() as tg:
            site_to_task = {}
            for site in task.portfolio:
                async_task = tg.create_task(get_latest_site_data_bundle(site_data=site.site_data, http_client=http_client))
                site_to_task[site.site_data.site_id] = async_task
    except* Exception as eg:
        for e in eg.exceptions:
            logger.exception("Got exception:", repr(e))
        raise

    for site in task.portfolio:
        site._epoch_data = site_to_task[site.site_data.site_id].result()
        # Check here that the data is good, as we partially constructed the site
        # before we got going.
        site = Site.model_validate(site)


async def get_latest_site_data_bundle(site_data: site_metadata_t, http_client: HTTPClient) -> EpochSiteData:
    """
    Get an EPOCH-compatible SiteData using the most recently generated datasets of each type.

    Parameters
    ----------
    site_data
        the metadata definition of the SiteData we want
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
    EpochSiteData
        Data about timeseries inputs for EPOCH to use
    """
    if isinstance(site_data, LegacySiteMetaData):
        bundle_metadata = await get_latest_bundle_metadata(
            site_id=site_data.site_id, start_ts=site_data.start_ts, end_ts=site_data.end_ts, http_client=http_client
        )
        bundle_id, start_ts, end_ts = (
            bundle_metadata.bundle_id,
            bundle_metadata.start_ts,
            bundle_metadata.end_ts,
        )
        site_data.bundle_id = bundle_id
    elif isinstance(site_data, SiteMetaData):
        start_ts, end_ts = await get_bundle_timestamps(bundle_id=site_data.bundle_id, http_client=http_client)

    site_data_entries = await get_bundled_data(bundle_id=bundle_id, http_client=http_client)

    epoch_data = site_data_entries_to_epoch_site_data(site_data_entries, start_ts, end_ts)

    return epoch_data


async def get_latest_bundle_metadata(
    site_id: str, start_ts: AwareDatetime, end_ts: AwareDatetime, http_client: HTTPClient
) -> BundleMetadata:
    """
    Get the bundle_id of the last created bundle with matching start timestamp.

    Parameters
    ----------
    site_id
        ID of the site.
    start_ts
        Start timestamp.
    end_ts
        End timestamp.
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
        Bundle ID.
    """
    data = {"site_id": site_id}
    response = await http_client.post(url=_DB_URL + "/list-dataset-bundles", json=data)
    bundles = response.json()
    matching_bundles = [
        bundle
        for bundle in bundles
        if datetime.fromisoformat(bundle["start_ts"]) == start_ts and datetime.fromisoformat(bundle["end_ts"]) == end_ts
    ]

    if not matching_bundles:
        raise ValueError(f"Unable to find a bundle with matching start and end timestamps: {start_ts}, {end_ts}")

    bundle = max(matching_bundles, key=operator.itemgetter("created_at"))
    bundle_id = cast(UUID7, bundle["bundle_id"])
    bundle_start_ts = cast(AwareDatetime, bundle["start_ts"])
    bundle_end_ts = cast(AwareDatetime, bundle["end_ts"])

    return BundleMetadata(bundle_id=bundle_id, start_ts=bundle_start_ts, end_ts=bundle_end_ts)


async def get_bundled_data(bundle_id: bundle_id_t, http_client: HTTPClient) -> SiteDataEntries:
    """
    Get all the site data entries associated to a bundle_id.

    Parameters
    ----------
    bundle_id
        ID of the bundle.
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
        Dictionary of datasets associated with the bundle.
    """
    response = await http_client.post(url=_DB_URL + "/get-dataset-bundle", params={"bundle_id": str(bundle_id)})
    site_data_entries = response.json()
    try:
        site_data_entries = SiteDataEntries.model_validate(site_data_entries)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to validate site data: {e!s}") from e
    return site_data_entries


async def get_bundle_timestamps(bundle_id: bundle_id_t, http_client: HTTPClient) -> tuple[AwareDatetime, AwareDatetime]:
    """
    Get a bundle's start and end timestamps.

    Parameters
    ----------
    bundle_id
        ID of the bundle.
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
        Tuple with start and end timestamps.
    """
    response = await http_client.post(url=_DB_URL + "/list-bundle-contents", params={"bundle_id": str(bundle_id)})
    bundle_content = response.json()
    starts_ts: AwareDatetime = bundle_content["start_ts"]
    end_ts: AwareDatetime = bundle_content["end_ts"]
    return (starts_ts, end_ts)


def site_data_entries_to_epoch_site_data(
    site_data_entries: SiteDataEntries, start_ts: datetime, end_ts: datetime
) -> EpochSiteData:
    """
    Transform a response from /get-latest-datasets into EPOCH ingestable data.

    Parameters
    ----------
    site_data_entries
        The site data entries returned from the database
    start_ts
        Start timestamp of the data.
    end_ts
        End timestamp of the data.

    Returns
    -------
    site_data
        EPOCH ingestable data.
    """
    site_data = EpochSiteData(
        start_ts=start_ts,
        end_ts=end_ts,
        baseline=site_data_entries.baseline,
        building_eload=site_data_entries.eload.data,
        building_hload=site_data_entries.heat.data[0].reduced_hload,  # First heat_load is Baseline
        peak_hload=site_data_entries.heat.data[0].peak_hload,
        ev_eload=[0 for _ in site_data_entries.eload.data],  # EV_load unsupported by DB
        dhw_demand=site_data_entries.dhw.data,
        air_temperature=site_data_entries.air_temp.data,
        grid_co2=site_data_entries.grid_co2.data,
        solar_yields=site_data_entries.rgen.data,
        import_tariffs=site_data_entries.import_tariffs.data,
        fabric_interventions=site_data_entries.heat.data[1:],  # Following heat_loads are fabric interventions
        ashp_input_table=site_data_entries.ashp_input.data,
        ashp_output_table=site_data_entries.ashp_output.data,
    )
    return site_data


async def get_saved_epoch_input(portfolio_id: dataset_id_t, site_id: str, http_client: HTTPClient) -> EpochInputData:
    """
    Get the SiteData and TaskData that was used to produce a specific result in the database.

    Parameters
    ----------
    portfolio_id
        ID of the portfolio to get data for.
    site_id
        ID of the site within that portfolio.
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
        An Epoch Compatible SiteData and a TaskData

    Raises
    ------
    HTTPException
        If that site isn't in that portfolio
    """
    repro_config = await get_result_configuration(portfolio_id=portfolio_id, http_client=http_client)

    if site_id not in repro_config.task_data:
        raise HTTPException(400, detail=f"No result found for (portfolio, site) pair: {portfolio_id}, {site_id}")

    task_data = repro_config.task_data[site_id]

    if isinstance(repro_config, LegacyResultReproConfig):
        site_data = repro_config.site_data[site_id]
        validate_for_necessary_datasets(site_data)
        site_data_entries = await fetch_specific_datasets(site_data=site_data, http_client=http_client)
        start_ts, end_ts = site_data.start_ts, site_data.end_ts

    else:
        bundle_id = repro_config.bundle_ids[site_id]
        site_data_entries = await get_bundled_data(bundle_id=bundle_id, http_client=http_client)
        start_ts, end_ts = await get_bundle_timestamps(bundle_id=bundle_id, http_client=http_client)

    epoch_data = site_data_entries_to_epoch_site_data(site_data_entries, start_ts, end_ts)

    return EpochInputData(task_data=task_data, site_data=epoch_data)


async def fetch_specific_datasets(site_data: LegacySiteMetaData, http_client: HTTPClient) -> SiteDataEntries:
    """
    Fetch some specificially chosen datasets from the database.

    Parameters
    ----------
    site_data
        Description of data.
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
    site_data_entries
        Dictionary of unprocessed datasets.
    """
    logger.info(f"Selecting specific datasets: {site_data}")
    response = await http_client.post(
        url=_DB_URL + "/get-specific-datasets",
        json=jsonable_encoder(site_data),
    )
    site_data_entries = response.json()
    return SiteDataEntries.model_validate(site_data_entries)


def validate_for_necessary_datasets(site_data: LegacySiteMetaData) -> None:
    """
    Check that the site_data contains all of the necessary datasets.

    Raises an Exception if this is not the case

    Parameters
    ----------
    site_data
        Data that we got from the database

    Returns
    -------
        None, if we got to the end

    Raises
    ------
    HTTPException
        If we were missing any datasets
    """
    # note that we don't define the SiteBaseline as necessary
    # when this is not provided, we allow the Data Service to provide a default baseline
    necessary_datasets = [
        DatasetTypeEnum.GasMeterData,
        DatasetTypeEnum.RenewablesGeneration,
        DatasetTypeEnum.HeatingLoad,
        DatasetTypeEnum.CarbonIntensity,
        DatasetTypeEnum.ASHPData,
        DatasetTypeEnum.ImportTariff,
    ]
    # Check that the dataset_ids have been saved to the database for this result
    missing_datasets: list[DatasetTypeEnum] = [key for key in necessary_datasets if getattr(site_data, key) is None]

    if (
        getattr(site_data, DatasetTypeEnum.ElectricityMeterData.value, None) is None
        and getattr(site_data, DatasetTypeEnum.ElectricityMeterDataSynthesised.value, None) is None
    ):
        missing_datasets.append(DatasetTypeEnum.ElectricityMeterData)

    if len(missing_datasets):
        list_as_string = ", ".join(missing_datasets)
        raise HTTPException(
            400,
            detail=f"{site_data.site_id} is missing the following datasets: {list_as_string}",
        )
