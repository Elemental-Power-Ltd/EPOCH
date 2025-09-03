"""Disaggregation functions for renewables-contaminated readings."""

import logging
from typing import cast

import httpx
import numpy as np
import pandas as pd

from ...models.core import dataset_id_t
from ..epl_typing import RecordMapping, db_conn_t
from ..pvgis import get_pvgis_optima, get_renewables_ninja_data

logger = logging.getLogger(__name__)


async def disaggregate_electricity_dataframe(
    elec_df: pd.DataFrame,
    http_client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    azimuth: float | None = None,
    tilt: float | None = None,
    system_size: float = 1.0,
) -> pd.DataFrame:
    """
    Disaggregrate the effect of solar generation from electrical meter readings in a dataframe.

    Use this function if you want to disaggregate a set of electrical meter data before upload.
    This function will generate solar data over the time period you've got meter data for, then
    calculate how much generation there was likely to have been in that time. Then subtract that from your
    total import to get your total used.
    This keeps the granularity of the original meter dataset: if it's monthly, we'll calculate your monthly consumption.
    If it's halfhourly, we'll calculate your halfhourly consumption (but this is likely to be less accurate)

    Parameters
    ----------
    elec_df
        Dataset of the electricity readings with `start_ts`, `end_ts` and `consumption_kwh`.
    http_client
        HTTP connection client used to contact Renewables.Ninja
    latitude
        Latitude of site in degrees
    longitude
        Longitude of site in degrees
    azimuth
        Angle between the solar panels and true north in degrees. If None, we'll estimate this.
    tilt
        Angle between the solar panels and the surface normal in degrees. If None, we'll estimate this.
    system_size
        Rated size of the system in kWp

    Returns
    -------
    pd.DataFrame
        Disaggregrated electrical data with columns `consumption_kwh`, `import` and `generation`
    """
    if azimuth is None or tilt is None:
        logger.info("Got no azimuth or tilt data, so getting optima from PVGIS.")
        optimal_params = await get_pvgis_optima(latitude=latitude, longitude=longitude, client=http_client)
        azimuth, tilt = float(optimal_params.azimuth), float(optimal_params.tilt)

    renewables_df = await get_renewables_ninja_data(
        latitude=latitude,
        longitude=longitude,
        start_ts=elec_df.start_ts.min() - pd.Timedelta(hours=1),
        end_ts=elec_df.end_ts.max() + pd.Timedelta(hours=1),
        azimuth=azimuth,
        tilt=tilt,
        tracking=False,
        client=http_client,
    )
    # Convert to half hourly kWh readings
    renewables_df = renewables_df.resample(pd.Timedelta(minutes=30)).mean().interpolate(method="time").ffill()
    renewables_df["pv"] *= 0.5
    # Convert into the appropriately sized system
    renewables_df["pv"] *= system_size

    total_pv = []
    for start_ts, end_ts in zip(elec_df.start_ts, elec_df.end_ts, strict=False):
        within_mask = np.logical_and(renewables_df.index >= start_ts, renewables_df.index < end_ts)
        total_pv.append(renewables_df.loc[within_mask, "pv"].sum())

    elec_df["generation"] = total_pv
    # We've assumed that the data we've been provided is the net import / export of electricity.
    # Positive values are imports, negative values are exports
    elec_df["import"] = elec_df["consumption_kwh"].clip(0)
    elec_df["export"] = (-elec_df["consumption_kwh"]).clip(0)

    # The total consumption is then the provided net import/export plus the on-site generation
    elec_df["consumption_kwh"] += elec_df["generation"]
    return elec_df


async def disaggregate_readings(
    elec_meter_dataset_id: dataset_id_t,
    pool: db_conn_t,
    http_client: httpx.AsyncClient,
    azimuth: float | None = None,
    tilt: float | None = None,
    system_size: float = 1.0,
) -> pd.DataFrame:
    """
    Disaggregrate the effect of solar generation from electrical meter readings in the database.

    Use this function if you want to disaggregate an existing set of electrical meter data.
    This function will generate solar data over the time period you've got meter data for, then
    calculate how much generation there was likely to have been in that time. Then subtract that from your
    total import to get your total used.
    This keeps the granularity of the original meter dataset: if it's monthly, we'll calculate your monthly consumption.
    If it's halfhourly, we'll calculate your halfhourly consumption (but this is likely to be less accurate)

    Parameters
    ----------
    elec_meter_dataset_id
        Dataset of the electricity meters you want us to disaggregate. We'll look up the associated site and its
        location from the metadata associated with this dataset.
    azimuth
        Angle between the solar panels and true north in degrees. If None, we'll estimate this.
    tilt
        Angle between the solar panels and the surface normal in degrees. If None, we'll estimate this.
    pool
        Database containing electrical meter readings
    http_client
        HTTP connection client used to contact Renewables.Ninja
    system_size
        Rated size of the system in kWp

    Returns
    -------
    pd.DataFrame
        Disaggregrated electrical data with columns `consumption_kwh`, `import` and `generation`
    """
    elec_dataset = await pool.fetch(
        """
        SELECT
            start_ts,
            end_ts,
            consumption_kwh
        FROM client_meters.electricity_meters
        WHERE dataset_id = $1""",
        elec_meter_dataset_id,
    )
    elec_df = pd.DataFrame.from_records(cast(RecordMapping, elec_dataset), columns=["start_ts", "end_ts", "consumption_kwh"])

    row = await pool.fetchrow(
        """
        SELECT
            m.site_id,
            si.coordinates
        FROM client_meters.metadata AS m
        LEFT JOIN client_info.site_info AS si
        ON m.site_id = si.site_id
        WHERE m.dataset_id = $1 AND NOT is_synthesised AND fuel_type = 'elec' LIMIT 1""",
        elec_meter_dataset_id,
    )
    site_id, (latitude, longitude) = row if row is not None else (None, (None, None))

    if site_id is None:
        raise ValueError(f"Couldn't find electricity meter metadata for {elec_meter_dataset_id}")
    if latitude is None or longitude is None:
        raise ValueError(f"Did not find a location for site {site_id}.")

    return await disaggregate_electricity_dataframe(
        elec_df=elec_df,
        http_client=http_client,
        latitude=latitude,
        longitude=longitude,
        azimuth=azimuth,
        tilt=tilt,
        system_size=system_size,
    )
