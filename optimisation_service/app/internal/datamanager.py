import json
import logging
import os
import shutil
import typing
import uuid
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from pydantic import UUID4

from ..models.core import OptimisationResultEntry, Task
from ..models.database import DatasetTypeEnum
from ..models.simulate import ResultReproConfig
from ..models.site_data import (
    ASHPResult,
    FileLoc,
    RecordsList,
    RemoteMetaData,
    SiteDataEntries,
)

logger = logging.getLogger("default")

# When running within a docker network, this should be set to http://data:8762
_DB_URL = os.environ.get("EP_DATA_SERVICE_URL", "http://localhost:8762")
_TEMP_DIR = Path("app", "data", "temp")
_INPUT_DATA_FILES = [
    "CSVEload.csv",
    "CSVHload.csv",
    "CSVAirtemp.csv",
    "CSVRGen.csv",
    "CSVASHPinput.csv",
    "CSVASHPoutput.csv",
    "CSVImporttariff.csv",
    "CSVGridCO2.csv",
    "CSVDHWdemand.csv",
]


class DataManager:
    def __init__(self) -> None:
        self.db_url = _DB_URL
        self.temp_dir = _TEMP_DIR
        self.input_data_files = _INPUT_DATA_FILES

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
        task._input_dir = Path(self.temp_dir, str(task.task_id))
        logger.debug(f"Creating temporary directory {task._input_dir}.")
        os.makedirs(task._input_dir)
        logger.info(f"Saving site data to {task._input_dir}.")

        # TODO: makes this async
        for site in task.portfolio:
            site._input_dir = Path(task._input_dir, site.site_data.site_id)
            os.makedirs(site._input_dir)
            site_data = site.site_data
            if site_data.loc == FileLoc.remote:
                await self.hydrate_site_with_latest_dataset_ids(site_data)

                site_data_entries = await self.fetch_specific_datasets(site_data)

                self.write_input_data_to_files(site_data_entries, site._input_dir)

            elif site_data.loc == FileLoc.local:
                self.copy_input_data(site_data.path, site._input_dir)

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

    def write_input_data_to_files(self, site_data_entries: SiteDataEntries, destination: os.PathLike) -> None:
        """
        Write the input data to a target folder.

        Parameters
        ----------
        site_data_entries
            Input site data.
        destination
            Folder to write files to.

        Returns
        -------
        None
        """
        dfs = self.transform_all_input_data(site_data_entries)
        logger.info(f"Saving site data to {destination}.")
        for name, df in dfs.items():
            df.to_csv(Path(destination, f"CSV{name}.csv"), index=False)

    def copy_input_data(self, source: str | os.PathLike, destination: str | os.PathLike) -> None:
        """
        Copies input data files from source to destination folder.

        Parameters
        ----------
        source
            Folder to copy files from.
        destination
            Folder to copy files to.

        Returns
        -------
        None
        """
        logger.debug(f"Copying data from {source} to {destination}.")
        for file in self.input_data_files:
            shutil.copy(Path(source, file), Path(destination, file))

    def save_parameters(self, task: Task) -> None:
        """
        Save the parameters of a Task to file for debug.

        Parameters
        ----------
        task
            Task to save parameters for.
        """
        for site in task.portfolio:
            with open(Path(site._input_dir, "inputParameters.json"), "w") as fi:
                json.dump(site.site_range.model_dump(), fi)

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
        return site_data_entries

    def transform_all_input_data(self, site_data_entries: SiteDataEntries) -> dict[str, pd.DataFrame]:
        """
        Transform a response from /get-latest-datasets into a set of dataframes

        Parameters
        ----------
        site_data_entries
            The site data entries returned from the database

        Returns
        -------
        site_data
            Dictionary of pandas DataFrame for each Epoch input data field.
        """
        site_data = {
            "Eload": self.transform_electricity_data(site_data_entries["eload"]),
            "Hload": self.transform_heat_data(site_data_entries["heat"]),
            "Airtemp": self.transform_airtemp_data(site_data_entries["heat"]),
            "RGen": self.transform_rgen_data(site_data_entries["rgen"]),
            "ASHPinput": self.transform_ASHP_input_data(site_data_entries["ashp_input"]),
            "ASHPoutput": self.transform_ASHP_output_data(site_data_entries["ashp_output"]),
            "Importtariff": self.transform_import_tariff_data(site_data_entries["import_tariffs"]),
            "GridCO2": self.transform_grid_CO2_data(site_data_entries["grid_co2"]),
            "DHWdemand": self.transform_dhw_data(site_data_entries["heat"]),
        }
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

    def transform_electricity_data(self, eload: RecordsList) -> pd.DataFrame:
        """
        Transform electricity load data from records to a pandas DataFrame.

        Parameters
        ----------
        eload
            List of electricity load records.

        Returns
        -------
        df
            Pandas DataFrame of electricity load records.
        """
        df = pd.DataFrame.from_records(eload)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "FixLoad1"])
        df["FixLoad2"] = 0
        return df

    def transform_rgen_data(self, rgen: RecordsList) -> pd.DataFrame:
        """
        Transform renewables data from records to a pandas DataFrame.

        Parameters
        ----------
        rgen
            List of renewables records.

        Returns
        -------
        df
            Pandas DataFrame of renewables records.
        """
        df = pd.DataFrame.from_records(rgen)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "RGen1"])
        df["RGen2"] = 0
        df["RGen3"] = 0
        df["RGen4"] = 0
        return df

    def transform_heat_data(self, heat: RecordsList) -> pd.DataFrame:
        """
        Transform heat load data from records to a pandas DataFrame.

        Parameters
        ----------
        heat
            List of heat load records.

        Returns
        -------
        df
            Pandas DataFrame of heat load records.
        """
        df = pd.DataFrame.from_records(heat)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "HLoad1"])
        return df

    def transform_airtemp_data(self, heat: RecordsList) -> pd.DataFrame:
        """
        Transform air temperature data from records to a pandas DataFrame.

        Parameters
        ----------
        heat
            List of air temp records.

        Returns
        -------
        df
            Pandas DataFrame of air temp records.
        """
        df = pd.DataFrame.from_records(heat)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "AirTemp"])
        return df

    def transform_dhw_data(self, heat: RecordsList) -> pd.DataFrame:
        """
        Transform domestic hot water load data from records to a pandas DataFrame.

        Parameters
        ----------
        heat
            List of domestic hot water load records.

        Returns
        -------
        df
            Pandas DataFrame of domestic hot water load records.
        """
        df = pd.DataFrame.from_records(heat)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "DHWLoad1"])
        return df

    def transform_ASHP_input_data(self, ashp_input: ASHPResult) -> pd.DataFrame:
        """
        Transform ASHP input data from records to a pandas DataFrame.

        Parameters
        ----------
        ashp_input
            List of ASHP input records.

        Returns
        -------
        df
            Pandas DataFrame of ASHP input records.
        """
        df = (
            pd.DataFrame.from_dict(dict(ashp_input), orient="tight")
            .sort_index()
            .reset_index(drop=False)
            .rename(columns={"temperature": 0})
        )
        return df

    def transform_ASHP_output_data(self, ashp_output: ASHPResult) -> pd.DataFrame:
        """
        Transform ASHP output data from records to a pandas DataFrame.

        Parameters
        ----------
        ashp_output
            List of ASHP output records.

        Returns
        -------
        df
            Pandas DataFrame of ASHP output records.
        """
        df = (
            pd.DataFrame.from_dict(dict(ashp_output), orient="tight")
            .sort_index()
            .reset_index(drop=False)
            .rename(columns={"temperature": 0})
        )
        return df

    def transform_import_tariff_data(self, import_tariffs: RecordsList) -> pd.DataFrame:
        """
        Transform import tariff data from records to a pandas DataFrame.

        Parameters
        ----------
        import_tariffs
            List of import tariff records.

        Returns
        -------
        df
            Pandas DataFrame of import tariff records.
        """
        df = pd.DataFrame.from_records(import_tariffs)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "Tariff", "Tariff1", "Tariff2", "Tariff3"])
        return df

    def transform_grid_CO2_data(self, grid_co2: RecordsList) -> pd.DataFrame:
        """
        Transform grid CO2 data from records to a pandas DataFrame.

        Parameters
        ----------
        grid_co2
            List of grid CO2 records.

        Returns
        -------
        df
            Pandas DataFrame of grid CO2 records.
        """
        df = pd.DataFrame.from_records(grid_co2)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "GridCO2"])
        return df


DataManagerDep = typing.Annotated[DataManager, Depends(DataManager)]
