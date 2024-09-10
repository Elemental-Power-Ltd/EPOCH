"""Lazy endpoints for bundling everything together."""

import asyncio
import datetime
import uuid

from fastapi import APIRouter, HTTPException

from ..dependencies import DatabasePoolDep, HttpClientDep
from ..models.core import DatasetEntry, DatasetIDWithTime, DatasetTypeEnum, SiteID, SiteIDWithTime
from ..models.import_tariffs import TariffRequest
from ..models.renewables import RenewablesRequest
from .carbon_intensity import generate_grid_co2
from .client_data import list_latest_datasets
from .heating_load import generate_heating_load
from .import_tariffs import generate_import_tariffs, select_arbitrary_tariff
from .renewables import generate_renewables_generation

router = APIRouter()


@router.post("/generate-all")
async def generate_all(
    params: SiteIDWithTime, pool: DatabasePoolDep, http_client: HttpClientDep
) -> dict[DatasetTypeEnum, DatasetEntry]:
    """
    Run all dataset generation tasks for this site.

    This includes heating load, grid CO2, electrical load, carbon intensity and solar PV.
    Currently it uses a simple tariff that covers a long period of time, and optimal solar PV parameters.
    You almost certainly want the timestamps to be 2021 or 2022 so we can use renewables.ninja data, and relatively recent
    tariff data.

    Parameters
    ----------
    params
        SiteIDWithTime, including two relatively far back timestamps for Renewables Ninja to use.

    Returns
    -------
    datasets
        Dataset Type: Dataset Entry mapping, including UUIDs under the 'dataset_id' key that you can retrieve from `get-*`.
    """
    async with pool.acquire() as conn:
        datasets = await list_latest_datasets(SiteID(site_id=params.site_id), conn=conn)

    if DatasetTypeEnum.GasMeterData not in datasets:
        raise HTTPException(400, f"No gas meter data for {params.site_id}.")
    if DatasetTypeEnum.ElectricityMeterData not in datasets:
        raise HTTPException(400, f"No electrical meter data for {params.site_id}.")
    heating_load_dataset = datasets[DatasetTypeEnum.GasMeterData]
    tariff_name = await select_arbitrary_tariff(params, http_client=http_client)
    async with asyncio.TaskGroup() as tg:
        heating_load_response = tg.create_task(
            generate_heating_load(
                DatasetIDWithTime(dataset_id=heating_load_dataset.dataset_id, start_ts=params.start_ts, end_ts=params.end_ts),
                pool=pool,
                http_client=http_client,
            )
        )
        grid_co2_response = tg.create_task(generate_grid_co2(params, pool=pool, http_client=http_client))

        import_tariff_response = tg.create_task(
            generate_import_tariffs(
                TariffRequest(site_id=params.site_id, tariff_name=tariff_name, start_ts=params.start_ts, end_ts=params.end_ts),
                pool=pool,
                http_client=http_client,
            )
        )
        renewables_response = tg.create_task(
            generate_renewables_generation(
                RenewablesRequest(
                    site_id=params.site_id, start_ts=params.start_ts, end_ts=params.end_ts, azimuth=None, tilt=None
                ),
                pool=pool,
                http_client=http_client,
            )
        )

    return {
        DatasetTypeEnum.HeatingLoad: DatasetEntry(
            dataset_id=heating_load_response.result().dataset_id,
            dataset_type=DatasetTypeEnum.HeatingLoad,
            created_at=heating_load_response.result().created_at,
        ),
        DatasetTypeEnum.CarbonIntensity: DatasetEntry(
            dataset_id=grid_co2_response.result().dataset_id,
            dataset_type=DatasetTypeEnum.CarbonIntensity,
            created_at=grid_co2_response.result().created_at,
        ),
        DatasetTypeEnum.ImportTariff: DatasetEntry(
            dataset_id=import_tariff_response.result().dataset_id,
            dataset_type=DatasetTypeEnum.ImportTariff,
            created_at=import_tariff_response.result().created_at,
        ),
        DatasetTypeEnum.RenewablesGeneration: DatasetEntry(
            dataset_id=renewables_response.result().dataset_id,
            dataset_type=DatasetTypeEnum.RenewablesGeneration,
            created_at=renewables_response.result().created_at,
        ),
        DatasetTypeEnum.ElectricityMeterData: datasets[DatasetTypeEnum.ElectricityMeterData],
        DatasetTypeEnum.ASHPData: DatasetEntry(
            dataset_id=uuid.uuid4(), dataset_type=DatasetTypeEnum.ASHPData, created_at=datetime.datetime.now(datetime.UTC)
        ),
    }
