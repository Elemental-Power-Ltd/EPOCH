"""Logic to combine multiple datasets into a single response for convenience."""

import asyncio
import logging

from fastapi import HTTPException

from app.dependencies import DatabasePoolDep
from app.models import EpochHeatingEntry, EpochRenewablesEntry
from app.models.carbon_intensity import EpochCarbonEntry
from app.models.client_data import SiteDataEntries
from app.models.core import DatasetIDWithTime, DatasetTypeEnum, MultipleDatasetIDWithTime
from app.models.electricity_load import EpochElectricityEntry
from app.models.import_tariffs import EpochTariffEntry
from app.routers.air_source_heat_pump import get_ashp_input, get_ashp_output
from app.routers.carbon_intensity import get_grid_co2
from app.routers.electricity_load import get_electricity_load
from app.routers.heating_load import get_heating_load
from app.routers.import_tariffs import get_import_tariffs
from app.routers.renewables import get_renewables_generation


async def fetch_blended_electricity_load(
    real_params: DatasetIDWithTime, synthetic_params: DatasetIDWithTime | None, pool: DatabasePoolDep
) -> list[EpochElectricityEntry]:
    """
    Fetch a combination of real and synthetic electricity data across a time period.

    This is because the electricity resampler is currently poor, so we want to use real data where we can.
    However, that's not always possible, or the time series might not align, so we'll use synthetic data to make up the gap.
    This fetches two datasets with similar parameters,
    and then preferentially selects real data for a time period if we have it.

    Parameters
    ----------
    real_params
        Parameters for the real electricity dataset you want to use (this will be the priority)
    synthetic_params
        Parameters for the synthetic elecitricty dataset. This provides the timestamps, but is second priority.
    pool
        Database connection pool

    Returns
    -------
    List of electricity entries, like the normal endpoints would give, but with synthetic data where required.
    """
    async with pool.acquire() as conn:
        try:
            real_data = await get_electricity_load(real_params, conn=conn)
        except HTTPException:
            real_data = []

        if synthetic_params is not None:
            synth_data = await get_electricity_load(synthetic_params, conn=conn)
        else:
            # Early return as we've got no synthetic data
            logging.warning(f"Got no synthetic data, returning only {real_params.dataset_id}")
            return real_data

    # The EPOCH format makes it a bit hard to just zip these together, so
    # assume each entry is uniquely identified by a (Date, StartTime) pair
    # and go from there.
    real_records = {(row.Date, row.StartTime): row for row in real_data}
    for idx, row in enumerate(synth_data):
        maybe_real = real_records.get((row.Date, row.StartTime))
        if maybe_real is not None:
            synth_data[idx] = row
    return synth_data


async def fetch_electricity_load(params: DatasetIDWithTime, pool: DatabasePoolDep) -> list[EpochElectricityEntry]:
    """Wrap get_electricity_load to get a conn from the pool."""
    async with pool.acquire() as conn:
        return await get_electricity_load(params, conn=conn)


async def fetch_heating_load(params: MultipleDatasetIDWithTime, pool: DatabasePoolDep) -> list[EpochHeatingEntry]:
    """Wrap get_heating_load to get a conn from the pool."""
    return await get_heating_load(params, pool=pool)


async def fetch_renewables_generation(params: MultipleDatasetIDWithTime, pool: DatabasePoolDep) -> list[EpochRenewablesEntry]:
    """Wrap get_renewables_generation to get a conn from the pool."""
    return await get_renewables_generation(params, pool=pool)


async def fetch_import_tariffs(params: MultipleDatasetIDWithTime, pool: DatabasePoolDep) -> list[EpochTariffEntry]:
    """Wrap get_import_tariffs to get a conn from the pool."""
    async with pool.acquire() as conn:
        return await get_import_tariffs(params, conn=conn)


async def fetch_grid_co2(params: DatasetIDWithTime, pool: DatabasePoolDep) -> list[EpochCarbonEntry]:
    """Wrap get_grid_co2 to get a conn from the pool."""
    async with pool.acquire() as conn:
        return await get_grid_co2(params, conn=conn)


async def fetch_all_input_data(
    site_data_ids: dict[DatasetTypeEnum, DatasetIDWithTime | MultipleDatasetIDWithTime],
    pool: DatabasePoolDep,
) -> SiteDataEntries:
    """
    Take a list of dataset IDs with a timespan and fetch the data for each one from the database.

    Parameters
    ----------
    site_data_ids
        specification of the data sources

    Returns
    -------
        The full data for each dataset
    """
    electricity_meter_data = site_data_ids[DatasetTypeEnum.ElectricityMeterData]
    assert isinstance(electricity_meter_data, DatasetIDWithTime)
    electricity_meter_data_synthetic = site_data_ids.get(DatasetTypeEnum.ElectricityMeterDataSynthesised)
    assert isinstance(electricity_meter_data_synthetic, DatasetIDWithTime | None)
    heating_load = site_data_ids[DatasetTypeEnum.HeatingLoad]
    assert isinstance(heating_load, MultipleDatasetIDWithTime)
    renewables_generation = site_data_ids[DatasetTypeEnum.RenewablesGeneration]
    assert isinstance(renewables_generation, MultipleDatasetIDWithTime)
    import_tariff = site_data_ids[DatasetTypeEnum.ImportTariff]
    assert isinstance(import_tariff, MultipleDatasetIDWithTime)
    carbon_intensity = site_data_ids[DatasetTypeEnum.CarbonIntensity]
    assert isinstance(carbon_intensity, DatasetIDWithTime)
    ashp_data = site_data_ids[DatasetTypeEnum.ASHPData]
    assert isinstance(ashp_data, DatasetIDWithTime)

    try:
        async with asyncio.TaskGroup() as tg:
            eload_task = tg.create_task(
                fetch_blended_electricity_load(
                    real_params=electricity_meter_data, synthetic_params=electricity_meter_data_synthetic, pool=pool
                )
            )
            heat_task = tg.create_task(fetch_heating_load(heating_load, pool))
            rgen_task = tg.create_task(fetch_renewables_generation(renewables_generation, pool))
            tariff_task = tg.create_task(fetch_import_tariffs(import_tariff, pool))
            grid_co2_task = tg.create_task(fetch_grid_co2(carbon_intensity, pool))

            ashp_input_task = tg.create_task(get_ashp_input(ashp_data))
            ashp_output_task = tg.create_task(get_ashp_output(ashp_data))
    except* ValueError as excgroup:
        raise HTTPException(500, detail=str(list(excgroup.exceptions))) from excgroup
    except* TypeError as excgroup:
        raise HTTPException(500, detail=str(list(excgroup.exceptions))) from excgroup

    return SiteDataEntries(
        eload=eload_task.result(),
        heat=heat_task.result(),
        rgen=rgen_task.result(),
        import_tariffs=tariff_task.result(),
        grid_co2=grid_co2_task.result(),
        ashp_input=ashp_input_task.result(),
        ashp_output=ashp_output_task.result(),
    )
