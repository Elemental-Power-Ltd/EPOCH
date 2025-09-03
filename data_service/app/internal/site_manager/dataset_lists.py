"""Database connection utilities to list various types of dataset."""

from app.internal.epl_typing import db_pool_t
from app.models.core import DatasetEntry, DatasetTypeEnum, site_id_t


async def list_gas_datasets(site_id: site_id_t, pool: db_pool_t) -> list[DatasetEntry]:
    """
    List the gas meter datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    res = await pool.fetch(
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
        site_id,
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


async def list_elec_datasets(site_id: site_id_t, pool: db_pool_t) -> list[DatasetEntry]:
    """
    List the true electricity meter datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.
    """
    res = await pool.fetch(
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
        site_id,
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


async def list_thermal_models(site_id: site_id_t, pool: db_pool_t) -> list[DatasetEntry]:
    """
    List the available thermal models datasets we have for a given site.

    Parameters
    ----------
    site_id
        The ID of the site that we've generated datasets for.

    Returns
    -------
    list[DatasetEntry]
        List of the thermal models with some metadata nulled out
    """
    res = await pool.fetch(
        """
        SELECT
            dataset_id,
            created_at
        FROM
            heating.thermal_model
        WHERE site_id = $1""",
        site_id,
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
