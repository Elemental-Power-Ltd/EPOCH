"""Database connection utilities to list various types of dataset."""

import datetime
import uuid

from ...dependencies import DatabasePoolDep
from ...models.core import (
    DatasetEntry,
    DatasetTypeEnum,
    SiteID,
)
from ...models.heating_load import InterventionEnum
from ...models.import_tariffs import SyntheticTariffEnum


async def list_gas_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the gas meter datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
                SELECT
                    cm.dataset_id,
                    MAX(cm.created_at) AS created_at,
                    MIN(gm.start_ts) AS start_ts,
                    MAX(gm.end_ts) AS end_ts,
                    COUNT(*) AS num_entries,
                    AVG(end_ts - start_ts) AS resolution
                FROM client_meters.metadata AS cm
                LEFT JOIN
                    client_meters.gas_meters AS gm
                ON gm.dataset_id = cm.dataset_id
                WHERE
                    (cm.is_synthesised = false)
                    AND cm.fuel_type = 'gas'
                    AND site_id = $1
                GROUP BY
                    cm.dataset_id
                """,
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.GasMeterData,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
        )
        for item in res
    ]


async def list_elec_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the true electricity meter datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                cm.dataset_id,
                MAX(cm.created_at) AS created_at,
                MIN(em.start_ts) AS start_ts,
                MAX(em.end_ts) AS end_ts,
                COUNT(*) AS num_entries,
                AVG(end_ts - start_ts) AS resolution
            FROM client_meters.metadata AS cm
            LEFT JOIN
                client_meters.electricity_meters AS em
            ON em.dataset_id = cm.dataset_id
            WHERE
                (cm.is_synthesised = false)
                AND cm.fuel_type = 'elec'
                AND site_id = $1
            GROUP BY
                cm.dataset_id""",
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.ElectricityMeterData,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
        )
        for item in res
    ]


async def list_elec_synthesised_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the synthetic electricity datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                cm.dataset_id,
                MAX(cm.created_at) AS created_at,
                MIN(em.start_ts) AS start_ts,
                MAX(em.end_ts) AS end_ts,
                COUNT(*) AS num_entries,
                AVG(end_ts - start_ts) AS resolution
            FROM client_meters.metadata AS cm
            LEFT JOIN
                client_meters.electricity_meters_synthesised AS em
            ON em.dataset_id = cm.dataset_id
            WHERE
                (cm.is_synthesised = true)
                AND cm.fuel_type = 'elec'
                AND site_id = $1
            GROUP BY
                cm.dataset_id""",
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.ElectricityMeterDataSynthesised,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
        )
        for item in res
        if item["num_entries"] > 1  # filter out bad entries here
    ]


async def list_import_tariff_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the import tariff datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                tm.dataset_id,
                MAX(tm.created_at) AS created_at,
                MIN(te.start_ts) AS start_ts,
                MAX(te.end_ts) AS end_ts,
                COUNT(*) AS num_entries,
                (MAX(te.end_ts) - MIN(te.start_ts)) / (COUNT(*) - 1) AS resolution,
                ANY_VALUE(provider) AS provider,
                ANY_VALUE(product_name) AS product_name
            FROM tariffs.metadata AS tm
            LEFT JOIN
                tariffs.electricity AS te
            ON tm.dataset_id = te.dataset_id
            WHERE site_id = $1
            GROUP BY tm.dataset_id""",
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.ImportTariff,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
            dataset_subtype=SyntheticTariffEnum(item["product_name"]) if item["provider"] == "synthetic" else None,
        )
        for item in res
    ]


async def list_renewables_generation_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the renewables generation (solar) datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                tm.dataset_id,
                MAX(tm.created_at) AS created_at,
                MIN(te.start_ts) AS start_ts,
                MAX(te.end_ts) AS end_ts,
                COUNT(*) AS num_entries,
                (MAX(te.end_ts) - MIN(te.start_ts)) / (COUNT(*) - 1) AS resolution
            FROM renewables.metadata AS tm
            LEFT JOIN
                renewables.solar_pv AS te
            ON tm.dataset_id = te.dataset_id
            WHERE site_id = $1
            GROUP BY tm.dataset_id""",
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.RenewablesGeneration,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
        )
        for item in res
    ]


async def list_thermal_models(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the available thermal models datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                dataset_id,
                created_at
            FROM
                heating.thermal_model
            WHERE site_id = $1""",
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.ThermalModel,
            created_at=item["created_at"],
            start_ts=None,
            end_ts=None,
            num_entries=None,
            resolution=None,
        )
        for item in res
    ]


async def list_heating_load_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the heating load datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                cm.dataset_id,
                MAX(cm.created_at) AS created_at,
                MIN(em.start_ts) AS start_ts,
                MAX(em.end_ts) AS end_ts,
                COUNT(*) AS num_entries,
                AVG(end_ts - start_ts) AS resolution,
                ANY_VALUE(interventions) AS interventions
            FROM heating.metadata AS cm
            LEFT JOIN
                heating.synthesised AS em
            ON em.dataset_id = cm.dataset_id
            WHERE
                site_id = $1
            GROUP BY
                cm.dataset_id""",
            site_id.site_id,
        )

    def maybe_convert_subtype(subtype: str) -> InterventionEnum | str:
        """Try to turn a given subtype into an enum, returning string if not."""
        try:
            return InterventionEnum(subtype)
        except ValueError:
            return subtype

    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.HeatingLoad,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
            dataset_subtype=[maybe_convert_subtype(subtype) for subtype in item["interventions"]]
            if item["interventions"]
            else None,
        )
        for item in res
    ]


async def list_carbon_intensity_datasets(site_id: SiteID, pool: DatabasePoolDep) -> list[DatasetEntry]:
    """
    List the Carbon Intensity datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    async with pool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                cm.dataset_id,
                MAX(cm.created_at) AS created_at,
                MIN(em.start_ts) AS start_ts,
                MAX(em.end_ts) AS end_ts,
                COUNT(*) AS num_entries,
                AVG(end_ts - start_ts) AS resolution
            FROM carbon_intensity.metadata AS cm
            LEFT JOIN
                carbon_intensity.grid_co2 AS em
            ON em.dataset_id = cm.dataset_id
            WHERE
                site_id = $1
            GROUP BY
                cm.dataset_id""",
            site_id.site_id,
        )
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            dataset_type=DatasetTypeEnum.CarbonIntensity,
            created_at=item["created_at"],
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            num_entries=item["num_entries"],
            resolution=item["resolution"],
        )
        for item in res
    ]


async def list_ashp_datasets() -> list[DatasetEntry]:
    """
    List the ASHP datasets we have in the database.

    This is a dummy function as we don't actually store them, but it returns a reasonable looking response.
    """
    return [
        DatasetEntry(
            dataset_id=uuid.uuid4(), dataset_type=DatasetTypeEnum.ASHPData, created_at=datetime.datetime.now(datetime.UTC)
        )
    ]
