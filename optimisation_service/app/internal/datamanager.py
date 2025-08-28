import json
import logging
import operator
import os
import typing
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import httpx
from fastapi import Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import UUID7, AwareDatetime

from app.models.core import OptimisationResultEntry, Site, Task
from app.models.database import bundle_id_t, dataset_id_t
from app.models.simulate import EpochInputData, LegacyResultReproConfig, NewResultReproConfig, result_repor_config_t
from app.models.site_data import DatasetTypeEnum, EpochSiteData, SiteDataEntries, SiteMetaData

logger = logging.getLogger("default")

# When running within a docker network, this should be set to http://data:8762
_DB_URL = os.environ.get("EP_DATA_SERVICE_URL", "http://localhost:8762")
_TEMP_DIR = Path("app", "data", "temp")


class DataManager:
    """
    Handle caching of datasets and connections to the database.

    DataManagers are complex and usually associated with tasks.
    """

    def __init__(self) -> None:
        self.db_url = _DB_URL
        self.temp_dir = _TEMP_DIR

    async def fetch_portfolio_data(self, task: Task) -> None:
        """
        Fetch task site data.

        Parameters
        ----------
        task
            Task to fetch site data for.

        Returns
        -------
        None
        """
        # TODO: makes this async
        for site in task.portfolio:
            site._epoch_data = await self.get_latest_site_data(site.site_data)
            # Check here that the data is good, as we partially constructed the site
            # before we got going.
            site = Site.model_validate(site)

    async def get_latest_site_data(self, site_data: SiteMetaData) -> EpochSiteData:
        """
        Get an EPOCH-compatible SiteData using the most recently generated datasets of each type.

        Parameters
        ----------
        site_data
            the metadata definition of the SiteData we want

        Returns
        -------
        EpochSiteData
            Data about timeseries inputs for EPOCH to use
        """
        if site_data.bundle_id is None:
            bundle_id = await self.get_latest_bundle_id(
                site_id=site_data.site_id, start_ts=site_data.start_ts, end_ts=site_data.end_ts
            )
            site_data.bundle_id = bundle_id

        site_data_entries = await self.get_bundled_data(bundle_id=site_data.bundle_id)

        site_data.start_ts, site_data.end_ts = await self.get_bundle_timestamps(bundle_id=site_data.bundle_id)

        epoch_data = self.transform_all_input_data(site_data_entries, site_data.start_ts, site_data.end_ts)

        return epoch_data

    async def get_latest_bundle_id(self, site_id: str, start_ts: AwareDatetime, end_ts: AwareDatetime) -> UUID7:
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

        Returns
        -------
            Bundle ID.
        """
        data = {"site_id": site_id}
        async with httpx.AsyncClient() as client:
            bundles = await self.db_post(client=client, subdirectory="/list-dataset-bundles", data=data)
        matching_bundles = [
            bundle
            for bundle in bundles
            if datetime.fromisoformat(bundle["start_ts"]) == start_ts and datetime.fromisoformat(bundle["end_ts"]) == end_ts
        ]

        if not matching_bundles:
            raise ValueError(f"Unable to find a bundle with matching start and end timestamps: {start_ts}, {end_ts}")

        return cast(UUID7, max(matching_bundles, key=operator.itemgetter("created_at"))["bundle_id"])

    async def get_bundled_data(self, bundle_id: bundle_id_t) -> SiteDataEntries:
        """
        Get all the site data entries associated to a bundle_id.

        Parameters
        ----------
        bundle_id
            ID of the bundle.

        Returns
        -------
            Dictionary of datasets associated with the bundle.
        """
        async with httpx.AsyncClient() as client:
            res = await client.post(url=self.db_url + "/get-dataset-bundle", params={"bundle_id": str(bundle_id)}, timeout=30.0)
        site_data_entries = res.json()
        try:
            site_data_entries = SiteDataEntries.model_validate(site_data_entries)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to validate site data: {e!s}") from e
        return site_data_entries

    async def get_bundle_timestamps(self, bundle_id: bundle_id_t) -> tuple[AwareDatetime, AwareDatetime]:
        """
        Get a bundle's start and end timestamps.

        Parameters
        ----------
        bundle_id
            ID of the bundle.

        Returns
        -------
            Tuple with start and end timestamps.
        """
        async with httpx.AsyncClient() as client:
            res = await client.post(
                url=self.db_url + "/list-bundle-contents", params={"bundle_id": str(bundle_id)}, timeout=30.0
            )
        bundle_content = res.json()
        starts_ts: AwareDatetime = bundle_content["start_ts"]
        end_ts: AwareDatetime = bundle_content["end_ts"]
        return (starts_ts, end_ts)

    async def get_saved_epoch_input(self, portfolio_id: dataset_id_t, site_id: str) -> EpochInputData:
        """
        Get the SiteData and TaskData that was used to produce a specific result in the database.

        Parameters
        ----------
        portfolio_id
            ID of the portfolio to get data for
        site_id
            ID of the site within that portfolio

        Returns
        -------
            An Epoch Compatible SiteData and a TaskData

        Raises
        ------
        HTTPException
            If that site isn't in that portfolio
        """
        repro_config = await self.get_result_configuration(portfolio_id)

        if site_id not in repro_config.task_data:
            raise HTTPException(400, detail=f"No result found for (portfolio, site) pair: {portfolio_id}, {site_id}")

        task_data = repro_config.task_data[site_id]

        if isinstance(repro_config, LegacyResultReproConfig):
            site_data = repro_config.site_data[site_id]
            validate_for_necessary_datasets(site_data)
            site_data_entries = await self.fetch_specific_datasets(site_data)
            start_ts, end_ts = site_data.start_ts, site_data.end_ts

        elif isinstance(repro_config, NewResultReproConfig):
            bundle_id = repro_config.bundle_ids[site_id]
            site_data_entries = await self.get_bundled_data(bundle_id=bundle_id)
            start_ts, end_ts = await self.get_bundle_timestamps(bundle_id=bundle_id)

        epoch_data = self.transform_all_input_data(site_data_entries, start_ts, end_ts)

        return EpochInputData(task_data=task_data, site_data=epoch_data)

    def save_parameters(self, task: Task) -> None:
        """
        Save the parameters of a Task to file for debug.

        Parameters
        ----------
        task
            Task to save parameters for.
        """
        for site in task.portfolio:
            site_temp_dir = Path(self.temp_dir, str(task.task_id), site.site_data.site_id)
            site_temp_dir.mkdir(parents=True, exist_ok=True)
            Path(site_temp_dir, "site_range.json").write_text(site.site_range.model_dump_json())

    async def fetch_specific_datasets(self, site_data: SiteMetaData) -> SiteDataEntries:
        """
        Fetch some specificially chosen datasets from the database.

        Parameters
        ----------
        site_data
            Description of data.

        Returns
        -------
        site_data_entries
            Dictionary of unprocessed datasets.
        """
        logger.info(f"Selecting specific datasets: {site_data}")
        async with httpx.AsyncClient() as client:
            site_data_entries = await self.db_post(
                client=client,
                subdirectory="/get-specific-datasets",
                data=site_data,
            )
        return SiteDataEntries.model_validate(site_data_entries)

    def transform_all_input_data(
        self, site_data_entries: SiteDataEntries, start_ts: datetime, end_ts: datetime
    ) -> EpochSiteData:
        """
        Transform a response from /get-latest-datasets into EPOCH ingestable data.

        Parameters
        ----------
        site_data_entries
            The site data entries returned from the database

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

    async def db_post(self, client: httpx.AsyncClient, subdirectory: str, data: Any) -> Any:
        """
        Send a post request to the database api server.

        Parameters
        ----------
        client
            Asynchronous http client to use in request.
        subdirectory
            Subdirectory to target.
        data
            JSON encoded data to send with post request.

        Returns
        -------
        dict
            Post request response message.
        """
        try:
            response = await client.post(url=self.db_url + subdirectory, json=jsonable_encoder(data), timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.exception(f"Error response {e.response.status_code} while requesting {e.request.url!r}: {e.response.text}.")
            raise
        except httpx.RequestError as e:
            logger.exception(f"Request error while requesting {e.request.url!r}", exc_info=True)
            raise

    async def transmit_results(self, results: OptimisationResultEntry) -> None:
        """
        Transmit optimisation results to database.

        Parameters
        ----------
        results
            List of optimisation results.
        """
        logger.info("Adding results to database.")
        async with httpx.AsyncClient() as client:
            await self.db_post(client=client, subdirectory="/add-optimisation-results", data=jsonable_encoder(results))

    async def transmit_task(self, task: Task) -> None:
        """
        Transmit optimisation task to database.

        Parameters
        ----------
        task
            Optimisation task.
        """
        logger.info(f"Adding {task.task_id} to database.")
        portfolio_range, bundle_ids, site_constraints = {}, {}, {}
        for site in task.portfolio:
            site_id = site.site_data.site_id
            portfolio_range[site_id] = site.site_range
            site_constraints[site_id] = site.constraints
            bundle_ids[site_id] = site.site_data.bundle_id
        data = {
            "client_id": task.client_id,
            "task_id": task.task_id,
            "task_name": task.name,
            "objectives": task.objectives,
            "optimiser": task.optimiser,
            "created_at": task.created_at,
            "portfolio_range": portfolio_range,
            "bundle_ids": bundle_ids,
            "portfolio_constraints": task.portfolio_constraints,
            "site_constraints": site_constraints,
        }
        async with httpx.AsyncClient() as client:
            await self.db_post(client=client, subdirectory="/add-optimisation-task", data=data)

    async def get_result_configuration(self, portfolio_id: dataset_id_t) -> result_repor_config_t:
        """
        Get the configuration that was used to generate a portfolio result that is stored in the database.

        Parameters
        ----------
        portfolio_id
            UUID associated with a portfolio optimisation result.

        Returns
        -------
        ResultReproConfig
            Portfolio configuration
        """
        async with httpx.AsyncClient() as client:
            data = await self.db_post(client, subdirectory="/get-result-configuration", data={"result_id": portfolio_id})
            logger.info("Repro with:", data)
            if "site_data" in data:
                return LegacyResultReproConfig.model_validate(data)
            return NewResultReproConfig.model_validate(data)


DataManagerDep = typing.Annotated[DataManager, Depends(DataManager)]


def load_epoch_data_from_file(path: Path) -> EpochSiteData:
    """
    Load EpochSiteData from file path.

    Parameters
    ----------
    path
        Path to EpochSiteData (including filename: *.json).

    Returns
    -------
    epoch_data
        Contents of file converted to EpochSiteData.
    """
    return EpochSiteData.model_validate(json.loads(path.read_text()))


def validate_for_necessary_datasets(site_data: SiteMetaData) -> None:
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
        site_data.__getattribute__(DatasetTypeEnum.ElectricityMeterData) is None
        and site_data.__getattribute__(DatasetTypeEnum.ElectricityMeterDataSynthesised) is None
    ):
        missing_datasets.append(DatasetTypeEnum.ElectricityMeterData)

    if len(missing_datasets):
        list_as_string = ", ".join(missing_datasets)
        raise HTTPException(
            400,
            detail=f"{site_data.site_id} is missing the following datasets: {list_as_string}",
        )
