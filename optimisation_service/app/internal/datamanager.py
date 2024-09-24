import logging
import os
import shutil
from pathlib import Path

import httpx
import pandas as pd
from fastapi.encoders import jsonable_encoder
from pydantic import UUID4

from ..models.core import EndpointResult, TaskWithUUID
from ..models.site_data import ASHPResult, FileLoc, LocalMetaData, RecordsList, RemoteMetaData, SiteDataEntries, SiteMetaData

logger = logging.getLogger("default")

_DB_URL = os.environ.get("DB_API_URL", "http://localhost:8762")
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

    async def process_site_data(self, site_data: SiteMetaData, task_id: UUID4) -> None:
        """
        Process task site data.
        Either copy local files to temp dir or fetch and process data from database and save to temp dir.

        Parameters
        ----------
        site_data
            Description of data.
        task_id
            The task id
        """
        self.temp_data_dir = Path(self.temp_dir, str(task_id))
        logger.debug(f"Creating temporary directory {self.temp_data_dir}.")
        os.makedirs(self.temp_data_dir)

        if site_data.loc == FileLoc.local:
            self.copy_input_data(site_data.path, self.temp_data_dir)
        else:
            site_data_entries = await self.fetch_latest_datasets(site_data)
            dfs = self.transform_all_input_data(site_data_entries)
            logger.info(f"Saving site data to {self.temp_data_dir}.")
            for name, df in dfs.items():
                df.to_csv(Path(self.temp_data_dir, f"CSV{name}.csv"), index=False)

    def copy_input_data(self, source: str | os.PathLike, destination: str | os.PathLike) -> None:
        """
        Copies input data files from source to destination folder.

        Parameters
        ----------
        source
            Folder to copy files from.
        destination
            Folder to copy files to.
        """
        logger.debug(f"Copying data from {source} to {destination}.")
        for file in self.input_data_files:
            shutil.copy(Path(source, file), Path(destination, file))

    async def fetch_latest_datasets(self, site_data: SiteMetaData) -> SiteDataEntries:
        """
        Fetch from the database the datasets relevant to the site data.

        Parameters
        ----------
        site_data
            Description of data.

        Returns
        -------
        site_data_entries
            Dictionary of unprocessed datasets.
        """
        async with httpx.AsyncClient() as client:
            site_data_entries = await self.db_post(client=client, subdirectory="/get-latest-datasets", data=site_data)
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
            "DHWdemand": self.transform_grid_CO2_data(site_data_entries["heat"]),
        }
        return site_data

    async def db_post(
        self, client: httpx.AsyncClient, subdirectory: str, data: RemoteMetaData | LocalMetaData
    ) -> SiteDataEntries:
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
            response = await client.post(url=self.db_url + subdirectory, json=jsonable_encoder(data))
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error response {e.response.status_code} while requesting {e.request.url!r}: {e.response.text}.")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error while requesting {e.request.url!r}: {e!s}", exc_info=True)
            raise

    async def transmit_results(self, results: list[EndpointResult]) -> None:
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

    async def transmit_task(self, task: TaskWithUUID) -> None:
        """
        Transmit optimisation task to database.

        Parameters
        ----------
        task
            Optimisation task.
        """
        logger.info(f"Adding {task.task_id} to database.")
        async with httpx.AsyncClient() as client:
            await self.db_post(client=client, subdirectory="/add-optimisation-task", data=jsonable_encoder(task))

    def transform_electricity_data(self, eload: RecordsList) -> pd.DataFrame:
        df = pd.DataFrame.from_records(eload)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "FixLoad1"])
        df["FixLoad2"] = 0
        df = df.sort_values("HourOfYear")
        return df

    def transform_rgen_data(self, rgen: RecordsList) -> pd.DataFrame:
        df = pd.DataFrame.from_records(rgen)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "RGen1"])
        df = df.sort_values("HourOfYear")
        df["RGen2"] = 0
        df["RGen3"] = 0
        df["RGen4"] = 0
        return df

    def transform_heat_data(self, heat: RecordsList) -> pd.DataFrame:
        df = pd.DataFrame.from_records(heat)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "HLoad1"])
        df = df.sort_values("HourOfYear")
        return df

    def transform_airtemp_data(self, heat: RecordsList) -> pd.DataFrame:
        df = pd.DataFrame.from_records(heat)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "AirTemp"])
        df = df.sort_values("HourOfYear")
        return df

    def transform_dhw_data(self, heat: RecordsList) -> pd.DataFrame:
        df = pd.DataFrame.from_records(heat)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "DHWLoad1", "DHWLoad2", "DHWLoad3", "DHWLoad4"])
        df = df.sort_values("HourOfYear")
        return df

    def transform_ASHP_input_data(self, ashp_input: ASHPResult) -> pd.DataFrame:
        df = pd.DataFrame.from_dict(dict(ashp_input), orient="tight")
        df = df.reset_index()
        df = df.rename(columns={"temperature": 0})
        df = df.reindex(columns=[0, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70])
        df = df.sort_values(str(0))
        return df

    def transform_ASHP_output_data(self, ashp_output: ASHPResult) -> pd.DataFrame:
        df = pd.DataFrame.from_dict(dict(ashp_output), orient="tight")
        df = df.reset_index()
        df = df.rename(columns={"temperature": 0})
        df = df.reindex(columns=[0, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70])
        df = df.sort_values(str(0))
        return df

    def transform_import_tariff_data(self, import_tariffs: RecordsList) -> pd.DataFrame:
        df = pd.DataFrame.from_records(import_tariffs)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "Tariff"])
        df = df.sort_values("HourOfYear")
        return df

    def transform_grid_CO2_data(self, grid_co2: RecordsList) -> pd.DataFrame:
        df = pd.DataFrame.from_records(grid_co2)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "GridCO2"])
        df = df.sort_values("HourOfYear")
        return df
