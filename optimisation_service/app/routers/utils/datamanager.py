import asyncio
import datetime
import logging
import os
import shutil
from pathlib import Path

import httpx
import pandas as pd
from fastapi.encoders import jsonable_encoder
from pydantic import UUID4

from ..models.core import EndpointResult, TaskWithUUID
from ..models.database import DatasetIDWithTime
from ..models.site_data import FileLoc, SiteMetaData

logger = logging.getLogger("default")

_DB_URL = os.environ.get("DB_API_URL", "http://localhost:8000")
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
]


class DataManager:
    def __init__(self) -> None:
        self.db_url = _DB_URL
        self.temp_dir = _TEMP_DIR
        self.input_data_files = _INPUT_DATA_FILES

    async def process_site_data(self, site_data: SiteMetaData, task_id: UUID4) -> os.PathLike:
        """
        Process task site data.
        Either copy local files to temp dir or fetch and process data from database and save to temp dir.

        Parameters
        ----------
        site_data
            Description of data.
        """
        self.temp_data_dir = Path(self.temp_dir, str(task_id))
        logger.debug(f"Creating temporary directory {self.temp_data_dir}.")
        os.makedirs(self.temp_data_dir)
        if site_data.loc == FileLoc.local:
            self.copy_input_data(site_data.path, self.temp_data_dir)
        else:
            site_data_info = await self.fetch_site_data_info(site_data.site_id)
            site_data_ids = {}
            for dataset_name, dataset_metadata in site_data_info.items():
                site_data_ids[dataset_name] = {
                    "dataset_id": dataset_metadata["dataset_id"],
                    "start_ts": site_data.start_ts,
                    "end_ts": site_data.start_ts + datetime.timedelta(hours=8760),
                }
            dfs = await self.fetch_all_input_data(site_data_ids)
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

    async def fetch_site_data_info(self, site_data_id: str) -> dict[str, DatasetIDWithTime]:
        """
        Fetch site data info.

        Parameters
        ----------
        site_data_id
            ID to retreive data details from database.
        """
        logger.debug(f"Fetching site data info {site_data_id}.")
        async with httpx.AsyncClient() as client:
            return await self.db_post(client=client, subdirectory="/list-latest-datasets", data={"site_id": site_data_id})

    async def fetch_all_input_data(self, site_data_ids: dict[str, DatasetIDWithTime]) -> dict[str, pd.DataFrame]:
        """
        Fetch and process all necessary input data from database.

        Parameters
        ----------
        site_data_ids
            Dictionary of UUIDs with start and stop time for each input dataset.

        Returns
        -------
        site_data
            Dictionary of pandas DataFrame for each Epoch input data field.
        """
        logger.debug("Fetching site data input data.")
        site_data = {}
        async with httpx.AsyncClient() as client:
            await self.fetch_ASHP_input_data(site_data_ids["ASHPData"], client)
            async with asyncio.TaskGroup() as tg:
                Eload_task = tg.create_task(self.fetch_electricity_data(site_data_ids["ElectricityMeterData"], client))
                Hload_task = tg.create_task(self.fetch_heat_data(site_data_ids["HeatingLoad"], client))
                Airtemp_task = tg.create_task(self.fetch_airtemp_data(site_data_ids["HeatingLoad"], client))
                RGen_task = tg.create_task(self.fetch_rgen_data(site_data_ids["RenewablesGeneration"], client))
                ASHPinput_task = tg.create_task(self.fetch_ASHP_input_data(site_data_ids["ASHPData"], client))
                ASHPoutput_task = tg.create_task(self.fetch_ASHP_output_data(site_data_ids["ASHPData"], client))
                Importtariff_task = tg.create_task(self.fetch_import_tariff_data(site_data_ids["ImportTariff"], client))
                GridCO2_task = tg.create_task(self.fetch_grid_CO2_data(site_data_ids["CarbonIntensity"], client))
        site_data["Eload"] = Eload_task.result()
        site_data["Hload"] = Hload_task.result()
        site_data["Airtemp"] = Airtemp_task.result()
        site_data["RGen"] = RGen_task.result()
        site_data["ASHPinput"] = ASHPinput_task.result()
        site_data["ASHPoutput"] = ASHPoutput_task.result()
        site_data["Importtariff"] = Importtariff_task.result()
        site_data["GridCO2"] = GridCO2_task.result()
        return site_data

    async def db_post(self, client: httpx.AsyncClient, subdirectory: str, data: dict | DatasetIDWithTime):
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
            logger.error(f"Request error while requesting {e.request.url!r}: {str(e)}", exc_info=True)
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

    async def fetch_electricity_data(self, data_id_w_time: DatasetIDWithTime, client: httpx.AsyncClient) -> pd.DataFrame:
        """
        Fetch and process electricity load data.

        Parameters
        ----------
        data_id_w_time
            UUID, start and stop time of dataset to fetch.

        Returns
        -------
        df
            Pandas dataframe of electricity load data.
        """
        response = await self.db_post(client=client, subdirectory="/get-electricity-load", data=data_id_w_time)
        df = pd.DataFrame.from_dict(response)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "FixLoad1"])
        df["FixLoad2"] = 0
        df = df.sort_values("HourOfYear")
        return df

    async def fetch_rgen_data(self, data_id_w_time: DatasetIDWithTime, client: httpx.AsyncClient) -> pd.DataFrame:
        """
        Fetch and process renewable generation data.

        Parameters
        ----------
        data_id_w_time
            UUID, start and stop time of dataset to fetch.

        Returns
        -------
        df
            Pandas dataframe of renewable generation data.
        """
        response = await self.db_post(client=client, subdirectory="/get-renewables-generation", data=data_id_w_time)
        df = pd.DataFrame.from_dict(response)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "RGen1"])
        df = df.sort_values("HourOfYear")
        df["RGen2"] = 0
        df["RGen3"] = 0
        df["RGen4"] = 0
        return df

    async def fetch_heat_data(self, data_id_w_time: DatasetIDWithTime, client: httpx.AsyncClient) -> pd.DataFrame:
        """
        Fetch and process heat load data.

        Parameters
        ----------
        data_id_w_time
            UUID, start and stop time of dataset to fetch.

        Returns
        -------
        df
            Pandas dataframe of heat load data.
        """
        response = await self.db_post(client=client, subdirectory="/get-heating-load", data=data_id_w_time)
        df = pd.DataFrame.from_dict(response)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "HLoad1"])
        df = df.sort_values("HourOfYear")
        return df

    async def fetch_airtemp_data(self, data_id_w_time: DatasetIDWithTime, client: httpx.AsyncClient) -> pd.DataFrame:
        """
        Fetch and process air temp data.

        Parameters
        ----------
        data_id_w_time
            UUID, start and stop time of dataset to fetch.

        Returns
        -------
        df
            Pandas dataframe of air temp data.
        """
        response = await self.db_post(client=client, subdirectory="/get-heating-load", data=data_id_w_time)
        df = pd.DataFrame.from_dict(response)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "AirTemp"])
        df = df.sort_values("HourOfYear")
        return df

    async def fetch_ASHP_input_data(self, data_id_w_time: DatasetIDWithTime, client: httpx.AsyncClient) -> pd.DataFrame:
        """
        Fetch and process ASHP input data.

        Parameters
        ----------
        data_id_w_time
            UUID, start and stop time of dataset to fetch.

        Returns
        -------
        df
            Pandas dataframe of ASHP input data.
        """
        response = await self.db_post(client=client, subdirectory="/get-ashp-input", data=data_id_w_time)
        df = pd.DataFrame.from_dict(response, orient="tight")
        df = df.reset_index()
        df = df.rename(columns={"temperature": 0})
        df = df.reindex(columns=[0, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70])
        df = df.sort_values(0)
        return df

    async def fetch_ASHP_output_data(self, data_id_w_time: DatasetIDWithTime, client: httpx.AsyncClient) -> pd.DataFrame:
        """
        Fetch and process ASHP output data.

        Parameters
        ----------
        data_id_w_time
            UUID, start and stop time of dataset to fetch.

        Returns
        -------
        df
            Pandas dataframe of ASHP output data.
        """
        response = await self.db_post(client=client, subdirectory="/get-ashp-output", data=data_id_w_time)
        df = pd.DataFrame.from_dict(response, orient="tight")
        df = df.reset_index()
        df = df.rename(columns={"temperature": 0})
        df = df.reindex(columns=[0, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70])
        df = df.sort_values(0)
        return df

    async def fetch_import_tariff_data(self, data_id_w_time: DatasetIDWithTime, client: httpx.AsyncClient) -> pd.DataFrame:
        """
        Fetch and process import tariff data.

        Parameters
        ----------
        data_id_w_time
            UUID, start and stop time of dataset to fetch.

        Returns
        -------
        df
            Pandas dataframe of import tariff data.
        """
        response = await self.db_post(client=client, subdirectory="/get-import-tariffs", data=data_id_w_time)
        df = pd.DataFrame.from_dict(response)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "Tariff"])
        df = df.sort_values("HourOfYear")
        return df

    async def fetch_grid_CO2_data(self, data_id_w_time: DatasetIDWithTime, client: httpx.AsyncClient) -> pd.DataFrame:
        """
        Fetch and process grid CO2 data.

        Parameters
        ----------
        data_id_w_time
            UUID, start and stop time of dataset to fetch.

        Returns
        -------
        df
            Pandas dataframe of grid CO2 data.
        """
        response = await self.db_post(client=client, subdirectory="/get-grid-co2", data=data_id_w_time)
        df = pd.DataFrame.from_dict(response)
        df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "GridCO2"])
        df = df.sort_values("HourOfYear")
        return df
