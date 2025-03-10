import json
import logging
import os
import typing
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import UUID4

from ..models.core import OptimisationResultEntry, Task
from ..models.database import DatasetTypeEnum
from ..models.simulate import EpochInputData, ResultReproConfig
from ..models.site_data import EpochSiteData, FileLoc, RemoteMetaData, SiteDataEntries

logger = logging.getLogger("default")

# When running within a docker network, this should be set to http://data:8762
_DB_URL = os.environ.get("EP_DATA_SERVICE_URL", "http://localhost:8762")
_TEMP_DIR = Path("app", "data", "temp")


class DataManager:
    def __init__(self) -> None:
        self.db_url = _DB_URL
        self.temp_dir = _TEMP_DIR

    async def fetch_portfolio_data(self, task: Task) -> None:
        """
        Fetch task site data.
        Either copy local files to temp dir or fetch and process data from database and save to temp dir.

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
            site_data = site.site_data
            if site_data.loc == FileLoc.remote:
                site._epoch_data = await self.get_latest_site_data(site_data)

            elif site_data.loc == FileLoc.local:
                site._epoch_data = load_epoch_data_from_file(site_data.path)

    async def get_latest_site_data(self, site_data: RemoteMetaData) -> EpochSiteData:
        """
        Get an EPOCH-compatible SiteData using the most recently generated datasets of each type.

        Parameters
        ----------
        site_data
            the metadata definition of the SiteData we want
        Returns
        -------

        """
        await self.hydrate_site_with_latest_dataset_ids(site_data)

        validate_for_necessary_datasets(site_data)

        dataset_entries = await self.fetch_specific_datasets(site_data)

        epoch_data = self.transform_all_input_data(dataset_entries, site_data.start_ts, site_data.end_ts)

        return epoch_data

    async def get_saved_epoch_input(self, portfolio_id: UUID4, site_id: str) -> EpochInputData:
        """
        Get the SiteData and TaskData that was used to produce a specific result in the database.

        Parameters
        ----------
        portfolio_id
        site_id

        Returns
        -------
            An Epoch Compatible SiteData and a TaskData

        """
        repro_config = await self.get_result_configuration(portfolio_id)

        if site_id not in repro_config.site_data or site_id not in repro_config.task_data:
            raise HTTPException(400, detail=f"No result found for (portfolio, site) pair: {portfolio_id}, {site_id}")

        site_data = repro_config.site_data[site_id]
        task_data = repro_config.task_data[site_id]

        validate_for_necessary_datasets(site_data)

        dataset_entries = await self.fetch_specific_datasets(site_data)

        epoch_data = self.transform_all_input_data(dataset_entries, site_data.start_ts, site_data.end_ts)

        return EpochInputData(task_data=task_data, site_data=epoch_data)

    async def hydrate_site_with_latest_dataset_ids(self, site_data: RemoteMetaData) -> None:
        """
        Obtain the latest dataset_ids for the given site and place them in the site_data

        This method should be called when site_data has not provided a specific set of IDs
        Parameters
        ----------
        site_data

        Returns
        -------
        None
        """
        datasetlist = await self.fetch_latest_dataset_ids(site_data)

        for key in DatasetTypeEnum:
            if not site_data.__getattribute__(key):
                curr_entries = datasetlist[key]
                if isinstance(curr_entries, list):
                    site_data.__setattr__(key, [uuid.UUID(item["dataset_id"]) for item in curr_entries])
                elif isinstance(curr_entries, dict):
                    site_data.__setattr__(key, uuid.UUID(curr_entries["dataset_id"]))
                else:
                    site_data.__setattr__(key, None)

    async def fetch_latest_dataset_ids(self, site_data: RemoteMetaData) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            latest_ids = await self.db_post(client=client, subdirectory="/list-latest-datasets", data=site_data)
            return latest_ids

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

    async def fetch_specific_datasets(self, site_data: RemoteMetaData) -> SiteDataEntries:
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
            building_eload=site_data_entries.eload.data,
            building_hload=site_data_entries.heat.data[0].reduced_hload,  # First heat_load is Baseline
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
            logger.error(f"Error response {e.response.status_code} while requesting {e.request.url!r}: {e.response.text}.")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error while requesting {e.request.url!r}: {e!s}", exc_info=True)
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
        portfolio_range, input_data = {}, {}
        for site in task.portfolio:
            portfolio_range[site.site_data.site_id] = site.site_range
            input_data[site.site_data.site_id] = site.site_data
        data = {
            "client_id": task.client_id,
            "task_id": task.task_id,
            "task_name": task.name,
            "objectives": task.objectives,
            "optimiser": task.optimiser,
            "created_at": task.created_at,
            "portfolio_range": portfolio_range,
            "input_data": input_data,
            "portfolio_constraints": task.portfolio_constraints,
        }
        async with httpx.AsyncClient() as client:
            await self.db_post(client=client, subdirectory="/add-optimisation-task", data=data)

    async def get_result_configuration(self, portfolio_id: UUID4) -> ResultReproConfig:
        """
        Get the configuration that was used to generate a portfolio result that is stored in the database

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
            return ResultReproConfig.model_validate(data)


DataManagerDep = typing.Annotated[DataManager, Depends(DataManager)]


def load_epoch_data_from_file(path: os.PathLike) -> EpochSiteData:
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
    with open(path) as f:
        epoch_data = EpochSiteData.model_validate(json.load(f))
    return epoch_data


def validate_for_necessary_datasets(site_data: RemoteMetaData) -> None:
    """
    Check that the site_data contains all of the necessary datasets.

    Raises an Exception if this is not the case

    Parameters
    ----------
    site_data

    Returns
    -------

    """
    necessary_datasets = [
        DatasetTypeEnum.GasMeterData,
        DatasetTypeEnum.RenewablesGeneration,
        DatasetTypeEnum.HeatingLoad,
        DatasetTypeEnum.CarbonIntensity,
        DatasetTypeEnum.ASHPData,
        DatasetTypeEnum.ImportTariff,
    ]
    # Check that the dataset_ids have been saved to the database for this result
    missing_datasets: list[DatasetTypeEnum] = [
        key for key in necessary_datasets if getattr(site_data, key) is None]

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
