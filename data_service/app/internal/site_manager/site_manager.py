"""Logic to combine multiple datasets into a single response for convenience."""

import asyncio
from typing import cast

from fastapi import HTTPException

from app.dependencies import DatabasePoolDep
from app.models.client_data import SiteDataEntries
from app.models.core import DatasetIDWithTime, DatasetTypeEnum, MultipleDatasetIDWithTime
from app.routers.air_source_heat_pump import get_ashp_input, get_ashp_output
from app.routers.carbon_intensity import get_grid_co2
from app.routers.electricity_load import get_blended_electricity_load
from app.routers.heating_load.get_heating_loads import get_air_temp, get_dhw_load, get_heating_load
from app.routers.import_tariffs import get_import_tariffs
from app.routers.renewables import get_renewables_generation


async def fetch_all_input_data(
    site_data_ids: dict[DatasetTypeEnum, DatasetIDWithTime | MultipleDatasetIDWithTime],
    pool: DatabasePoolDep,
) -> SiteDataEntries:
    """
    Take a list of dataset IDs with a timespan and fetch the data for each one from the database.

    All of those datasets must already exist in the database, ideally after a generate-all run.

    Parameters
    ----------
    site_data_ids
        specification of the data sources

    Returns
    -------
        The full data for each dataset
    """

    class DummyTask:
        """Placeholder to mimic a task with a .result() where we got a None dataset."""

        def result(self) -> None:
            """Return a boring None value for this dummy task."""
            return None

    try:
        async with asyncio.TaskGroup() as tg:
            # We create a blended electricity load if we got either a real set of data or a blended set of data.
            eload_task = (
                tg.create_task(
                    get_blended_electricity_load(
                        real_params=cast(DatasetIDWithTime | None, site_data_ids[DatasetTypeEnum.ElectricityMeterData]),
                        synthetic_params=cast(
                            DatasetIDWithTime | None, site_data_ids.get(DatasetTypeEnum.ElectricityMeterDataSynthesised)
                        ),
                        pool=pool,
                    )
                )
                if site_data_ids.get(DatasetTypeEnum.ElectricityMeterData) is not None
                or site_data_ids.get(DatasetTypeEnum.ElectricityMeterDataSynthesised) is not None
                else DummyTask()
            )

            heat_task = (
                tg.create_task(
                    get_heating_load(cast(MultipleDatasetIDWithTime, site_data_ids[DatasetTypeEnum.HeatingLoad]), pool)
                )
                if site_data_ids.get(DatasetTypeEnum.HeatingLoad) is not None
                else DummyTask()
            )
            dhw_task = (
                tg.create_task(
                    get_dhw_load(
                        DatasetIDWithTime(
                            dataset_id=cast(MultipleDatasetIDWithTime, site_data_ids[DatasetTypeEnum.HeatingLoad]).dataset_id[
                                0
                            ],
                            start_ts=cast(MultipleDatasetIDWithTime, site_data_ids[DatasetTypeEnum.HeatingLoad]).start_ts,
                            end_ts=cast(MultipleDatasetIDWithTime, site_data_ids[DatasetTypeEnum.HeatingLoad]).end_ts,
                        ),
                        pool,
                    )
                )
                if site_data_ids.get(DatasetTypeEnum.HeatingLoad) is not None
                else DummyTask()
            )

            air_temp_task = (
                tg.create_task(
                    get_air_temp(
                        DatasetIDWithTime(
                            dataset_id=cast(MultipleDatasetIDWithTime, site_data_ids[DatasetTypeEnum.HeatingLoad]).dataset_id[
                                0
                            ],
                            start_ts=cast(MultipleDatasetIDWithTime, site_data_ids[DatasetTypeEnum.HeatingLoad]).start_ts,
                            end_ts=cast(MultipleDatasetIDWithTime, site_data_ids[DatasetTypeEnum.HeatingLoad]).end_ts,
                        ),
                        pool,
                    )
                )
                if site_data_ids.get(DatasetTypeEnum.HeatingLoad) is not None
                else DummyTask()
            )

            rgen_task = (
                tg.create_task(
                    get_renewables_generation(
                        cast(MultipleDatasetIDWithTime, site_data_ids[DatasetTypeEnum.RenewablesGeneration]), pool
                    )
                )
                if site_data_ids.get(DatasetTypeEnum.RenewablesGeneration) is not None
                else DummyTask()
            )

            tariff_task = (
                tg.create_task(
                    get_import_tariffs(cast(MultipleDatasetIDWithTime, site_data_ids[DatasetTypeEnum.ImportTariff]), pool)
                )
                if site_data_ids.get(DatasetTypeEnum.ImportTariff)
                else DummyTask()
            )

            grid_co2_task = (
                tg.create_task(get_grid_co2(cast(DatasetIDWithTime, site_data_ids[DatasetTypeEnum.CarbonIntensity]), pool))
                if site_data_ids.get(DatasetTypeEnum.CarbonIntensity) is not None
                else DummyTask()
            )

            ashp_input_task = (
                tg.create_task(get_ashp_input(cast(DatasetIDWithTime, site_data_ids[DatasetTypeEnum.ASHPData])))
                if site_data_ids.get(DatasetTypeEnum.ASHPData) is not None
                else DummyTask()
            )
            ashp_output_task = (
                tg.create_task(get_ashp_output(cast(DatasetIDWithTime, site_data_ids[DatasetTypeEnum.ASHPData])))
                if site_data_ids.get(DatasetTypeEnum.ASHPData) is not None
                else DummyTask()
            )

    except* ValueError as excgroup:
        raise HTTPException(500, detail=str(list(excgroup.exceptions))) from excgroup
    except* TypeError as excgroup:
        raise HTTPException(500, detail=str(list(excgroup.exceptions))) from excgroup

    return SiteDataEntries(
        eload=eload_task.result(),
        heat=heat_task.result(),
        air_temp=air_temp_task.result(),
        dhw=dhw_task.result(),
        rgen=rgen_task.result(),
        import_tariffs=tariff_task.result(),
        grid_co2=grid_co2_task.result(),
        ashp_input=ashp_input_task.result(),
        ashp_output=ashp_output_task.result(),
    )
