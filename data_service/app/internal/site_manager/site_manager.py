"""Logic to combine multiple datasets into a single response for convenience."""

from app.dependencies import DatabaseDep, HttpClientDep, VaeDep
from app.models.client_data import SiteDataEntries
from app.models.core import DatasetIDWithTime
from app.routers.air_source_heat_pump import get_ashp_input, get_ashp_output
from app.routers.carbon_intensity import get_grid_co2
from app.routers.heating_load import get_heating_load
from app.routers.import_tariffs import get_import_tariffs
from app.routers.meter_data import get_electricity_load
from app.routers.renewables import get_renewables_generation


async def fetch_all_input_data(site_data_ids: dict[str, DatasetIDWithTime], conn: DatabaseDep, client: HttpClientDep,
                               vae: VaeDep) -> SiteDataEntries:
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
    eload = await get_electricity_load(site_data_ids["ElectricityMeterData"], conn=conn, http_client=client, elec_vae=vae)
    heat = await get_heating_load(site_data_ids["HeatingLoad"], conn=conn)
    rgen = await get_renewables_generation(site_data_ids["RenewablesGeneration"], conn=conn)
    import_tariffs = await get_import_tariffs(site_data_ids["ImportTariff"], conn=conn)
    grid_co2 = await get_grid_co2(site_data_ids["CarbonIntensity"], conn=conn)

    ashp_input = await get_ashp_input(site_data_ids["ASHPData"])
    ashp_output = await get_ashp_output(site_data_ids["ASHPData"])

    return SiteDataEntries(
        eload=eload,
        heat=heat,
        rgen=rgen,
        import_tariffs=import_tariffs,
        grid_co2=grid_co2,
        ashp_input=ashp_input,
        ashp_output=ashp_output
    )
