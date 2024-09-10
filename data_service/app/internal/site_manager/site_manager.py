"""Logic to combine multiple datasets into a single response for convenience."""

import asyncio

from app.dependencies import DatabasePoolDep, HttpClientDep, VaeDep
from app.models import EpochHeatingEntry, EpochRenewablesEntry
from app.models.carbon_intensity import EpochCarbonEntry
from app.models.client_data import SiteDataEntries
from app.models.core import DatasetIDWithTime, DatasetTypeEnum, MultipleDatasetIDWithTime
from app.models.import_tariffs import EpochTariffEntry
from app.models.meter_data import EpochElectricityEntry
from app.routers.air_source_heat_pump import get_ashp_input, get_ashp_output
from app.routers.carbon_intensity import get_grid_co2
from app.routers.heating_load import get_heating_load
from app.routers.import_tariffs import get_import_tariffs
from app.routers.meter_data import get_electricity_load
from app.routers.renewables import get_renewables_generation


async def fetch_electricity_load(
    params: DatasetIDWithTime, pool: DatabasePoolDep, client: HttpClientDep, vae: VaeDep
) -> list[EpochElectricityEntry]:
    """Wrap get_electricity_load to get a conn from the pool."""
    async with pool.acquire() as conn:
        return await get_electricity_load(params, conn=conn, http_client=client, elec_vae=vae)


async def fetch_heating_load(params: MultipleDatasetIDWithTime, pool: DatabasePoolDep) -> list[EpochHeatingEntry]:
    """Wrap get_heating_load to get a conn from the pool."""
    return await get_heating_load(params, pool=pool)


async def fetch_renewables_generation(params: MultipleDatasetIDWithTime, pool: DatabasePoolDep) -> list[EpochRenewablesEntry]:
    """Wrap get_renewables_generation to get a conn from the pool."""
    return await get_renewables_generation(params, pool=pool)


async def fetch_import_tariffs(params: DatasetIDWithTime, pool: DatabasePoolDep) -> list[EpochTariffEntry]:
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
    client: HttpClientDep,
    vae: VaeDep,
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
    heating_load = site_data_ids[DatasetTypeEnum.HeatingLoad]
    assert isinstance(heating_load, MultipleDatasetIDWithTime)
    renewables_generation = site_data_ids[DatasetTypeEnum.RenewablesGeneration]
    assert isinstance(renewables_generation, MultipleDatasetIDWithTime)
    import_tariff = site_data_ids[DatasetTypeEnum.ImportTariff]
    assert isinstance(import_tariff, DatasetIDWithTime)
    carbon_intensity = site_data_ids[DatasetTypeEnum.CarbonIntensity]
    assert isinstance(carbon_intensity, DatasetIDWithTime)
    ashp_data = site_data_ids[DatasetTypeEnum.ASHPData]
    assert isinstance(ashp_data, DatasetIDWithTime)

    async with asyncio.TaskGroup() as tg:
        eload_task = tg.create_task(fetch_electricity_load(electricity_meter_data, pool, client, vae))
        heat_task = tg.create_task(fetch_heating_load(heating_load, pool))
        rgen_task = tg.create_task(fetch_renewables_generation(renewables_generation, pool))
        tariff_task = tg.create_task(fetch_import_tariffs(import_tariff, pool))
        grid_co2_task = tg.create_task(fetch_grid_co2(carbon_intensity, pool))

        ashp_input_task = tg.create_task(get_ashp_input(ashp_data))
        ashp_output_task = tg.create_task(get_ashp_output(ashp_data))

    return SiteDataEntries(
        eload=eload_task.result(),
        heat=heat_task.result(),
        rgen=rgen_task.result(),
        import_tariffs=tariff_task.result(),
        grid_co2=grid_co2_task.result(),
        ashp_input=ashp_input_task.result(),
        ashp_output=ashp_output_task.result(),
    )
