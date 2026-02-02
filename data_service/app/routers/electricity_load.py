"""API endpoints for electrical loads, including resampling."""

import asyncio
import datetime
import functools
import itertools
import logging
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
from app.dependencies import DatabasePoolDep, ThreadPoolDep, VaeDep
from app.internal.elec_meters import daily_to_hh_eload, day_type, monthly_to_daily_eload
from app.internal.elec_meters.model_utils import OffsetMethodEnum
from app.internal.elec_meters.preprocessing import hh_to_square
from app.internal.epl_typing import DailyDataFrame, HHDataFrame, NonHHDataFrame, RecordMapping
from app.internal.site_manager.bundles import file_self_with_bundle
from app.internal.utils import get_bank_holidays
from app.internal.utils.uuid import uuid7
from app.models.core import DatasetIDWithTime, DatasetTypeEnum, FuelEnum
from app.models.electricity_load import ElectricalLoadMetadata, ElectricalLoadRequest, EpochElectricityEntry
from app.models.meter_data import ReadingTypeEnum
from fastapi import APIRouter, HTTPException

router = APIRouter()

WEEKEND_INDS = frozenset({5, 6})


def resample_daily_df(daily_df: DailyDataFrame, start_ts: datetime.datetime, end_ts: datetime.datetime) -> DailyDataFrame:
    """
    Resample and rearrange the daily dataframe to match the time period provided.

    We often end up with data in daily_df that runs across periods that aren't exactly a year.
    We need to resample and rearrange the daily data we have to match the period of interest.
    We do that by calculating the average usage on this type of day in this week of the year across the provided
    period, e.g. looking at the average usage on all Mondays/Fridays in Week 0. Then, if we're missing a Monday in Week 0
    in the period of interest, take the average usage of Mondays/Fridays in Week 0 across the provided period.

    If there isn't such a day or week in the dataset, interpolate between the usage of that day type in weeks either side.
    For example, if we can't find data for a Wednesday in Week 26, interpolate between Wednesday W25 and Wednesday W27.

    Parameters
    ----------
    daily_df
        Daily dataframe with `consumption_kwh` column covering as much time as possible (but not necessarily
        the `start_ts`, `end_ts` you've specified).

    start_ts
        Start time of the period you want

    end_ts
        End time of the period you want.

    Returns
    -------
    DailyDataFrame
        Dataframe with every day between `start_ts` and `end_ts` with a reasonable `consumption_kwh` reading.
    """
    public_holidays = get_bank_holidays()
    weekly_type_df = (
        daily_df[["consumption_kwh"]]
        .groupby([lambda dt, ph=public_holidays: day_type(dt, public_holidays=ph), lambda dt: dt.weekofyear])
        .mean()
    )
    synthetic_daily_df = DailyDataFrame(
        pd.DataFrame(
            index=pd.date_range(
                start_ts.astimezone(datetime.UTC),
                end_ts.astimezone(datetime.UTC),
                freq=pd.Timedelta(days=1),
                inclusive="both",
                tz=datetime.UTC,
            )
        )
    )
    all_consumptions: list[float] = []
    for day in synthetic_daily_df.index:
        if day in daily_df.index:
            # This day actually exists, so don't resample it.
            # Heads up that this might cause some trouble if your indexes don't perfectly align
            # (e.g. one is dates and another is midnight datetimes, or there is a timezone difference).
            all_consumptions.append(float(daily_df.loc[day, "consumption_kwh"]))
            continue

        day_class = day_type(day, public_holidays=public_holidays).value
        week_of_year = day.weekofyear
        if (day_class, week_of_year) in weekly_type_df.index:
            all_consumptions.append(float(weekly_type_df.loc[day_class, week_of_year].iloc[0]))
        else:
            # We interpolate between weeks with days of this type either side of this reading
            # (e.g. so the nearest weeks to week 3 might be weeks 50 and 10)
            weeks_with_type = (
                weekly_type_df[weekly_type_df.index.get_level_values(0) == day_class].index.get_level_values(1).to_numpy()
            )
            type_consumptions = weekly_type_df.loc[
                weekly_type_df.index.get_level_values(0) == day_class, "consumption_kwh"
            ].to_numpy()

            all_consumptions.append(float(np.interp(week_of_year, weeks_with_type, type_consumptions, period=52)))
    synthetic_daily_df["consumption_kwh"] = all_consumptions
    synthetic_daily_df["start_ts"] = synthetic_daily_df.index
    synthetic_daily_df["end_ts"] = synthetic_daily_df.index + pd.Timedelta(days=1)
    return synthetic_daily_df


@router.post("/generate-electricity-load", tags=["electricity", "generate"])
async def generate_electricity_load(
    params: ElectricalLoadRequest, vae: VaeDep, pool: DatabasePoolDep, thread_pool: ThreadPoolDep
) -> ElectricalLoadMetadata:
    """
    Generate a synthetic electrical load from a set of real data.

    This uses a daily profiles from monthly data (or daily if we have it) and resamples up from there using a VAE.

    Parameters
    ----------
    params
        Dataset ID to resample from, and timestamps you'd like to resample to.

    Returns
    -------
    Metadata about the generated synthetic half hourly dataset, that you can now request with `get-electrical-load`
    """
    logger = logging.getLogger(__name__)
    async with pool.acquire() as conn:
        ds_meta = await conn.fetchrow(
            """SELECT site_id, fuel_type, reading_type FROM client_meters.metadata WHERE dataset_id = $1 LIMIT 1""",
            params.dataset_id,
        )
        if ds_meta is not None:
            site_id, fuel_type, reading_type = ds_meta
        else:
            raise HTTPException(400, f"Could not read metadata for {params.dataset_id}; is it a correct electrical meter set?")

        if fuel_type != "elec":
            raise HTTPException(400, f"Got wrong fuel type for {params.dataset_id}; got {fuel_type} but expected 'elec'.")

        dataset = await conn.fetch(
            """
            SELECT
                start_ts,
                end_ts,
                consumption_kwh
            FROM client_meters.electricity_meters
            WHERE dataset_id = $1""",
            params.dataset_id,
        )

    raw_df = pd.DataFrame.from_records(cast(RecordMapping, dataset), columns=["start_ts", "end_ts", "consumption_kwh"])
    raw_df.index = pd.DatetimeIndex(pd.to_datetime(raw_df["start_ts"]))

    if reading_type != "halfhourly":
        daily_df = monthly_to_daily_eload(NonHHDataFrame(raw_df))
    else:
        # We've got half hourly data, so we can skip the horrible daily profiles bit
        daily_df = DailyDataFrame(raw_df[["consumption_kwh"]].resample(pd.Timedelta(days=1)).sum())
        daily_df["start_ts"] = daily_df.index
        daily_df["end_ts"] = daily_df.index + pd.Timedelta(days=1)

    synthetic_daily_df = resample_daily_df(daily_df, params.start_ts, params.end_ts)

    if reading_type == "halfhourly":
        logger.info("Generating electricity load with observed HH")
        resid_model_path = None
        target_hh_observed_df = hh_to_square(cast(HHDataFrame, raw_df))
        offset_method = OffsetMethodEnum.DetectChgpt
    else:
        logger.info("Generating electricity load with pretrained ARIMA")
        resid_model_path = Path("models", "final", "arima")
        target_hh_observed_df = None
        offset_method = OffsetMethodEnum.CompareActiveNeighbours

    loop = asyncio.get_running_loop()
    synthetic_hh_df = await loop.run_in_executor(
        thread_pool,
        functools.partial(
            daily_to_hh_eload,
            synthetic_daily_df,
            model=vae,
            resid_model_path=resid_model_path,
            target_hh_observed_df=target_hh_observed_df,
            weekend_inds=WEEKEND_INDS,
            offset_method=offset_method,
        ),
    )

    # If we used the observed data, then there's a chance we get either negative or enormous days.
    # Patch those out with model path data.
    # This upper threshold is either a kettle + an oven for a small site, or a whole day's usage in a single reading.
    OVER_THRESHOLD = max(2.5, synthetic_hh_df["consumption_kwh"].mean() * 48)
    is_bad_mask = np.logical_or(
        synthetic_hh_df["consumption_kwh"].to_numpy() >= OVER_THRESHOLD, synthetic_hh_df["consumption_kwh"].to_numpy() < 0.0
    )
    if np.any(is_bad_mask) and target_hh_observed_df is not None:
        new_synth_hh_df = await loop.run_in_executor(
            thread_pool,
            functools.partial(
                daily_to_hh_eload,
                synthetic_daily_df,
                model=vae,
                resid_model_path=Path("models", "final", "arima"),
                target_hh_observed_df=None,
                weekend_inds=WEEKEND_INDS,
                offset_method=offset_method,
            ),
        )
        assert isinstance(synthetic_hh_df.index, pd.DatetimeIndex)
        for day in sorted(set(synthetic_hh_df.index.date)):
            in_day_mask = synthetic_hh_df.index.date == day
            # This is true if there are any entries in this day that are bad.
            # In that case, sub out the entire day.
            if np.any(np.logical_and(in_day_mask, is_bad_mask)):
                synthetic_hh_df[in_day_mask] = new_synth_hh_df[in_day_mask].to_numpy()

    # As a final check, interpolate any remaining bad entries.
    is_bad_mask = np.logical_or(
        synthetic_hh_df["consumption_kwh"].to_numpy() >= OVER_THRESHOLD, synthetic_hh_df["consumption_kwh"].to_numpy() < 0.0
    )
    synthetic_hh_df.loc[is_bad_mask, "consumption_kwh"] = float("NaN")
    synthetic_hh_df["consumption_kwh"] = synthetic_hh_df["consumption_kwh"].interpolate(method="time")

    metadata = ElectricalLoadMetadata(
        dataset_id=params.bundle_metadata.dataset_id if params.bundle_metadata is not None else uuid7(),
        created_at=datetime.datetime.now(tz=datetime.UTC),
        site_id=site_id,
        fuel_type=FuelEnum.elec,
        reading_type=ReadingTypeEnum.HalfHourly,
        filename=str(params.dataset_id),
        is_synthesised=True,
    )

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
            INSERT INTO
                client_meters.metadata (
                    dataset_id,
                    site_id,
                    created_at,
                    fuel_type,
                    reading_type,
                    filename,
                    is_synthesised)
            VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                metadata.dataset_id,
                metadata.site_id,
                metadata.created_at,
                metadata.fuel_type,
                metadata.reading_type,
                metadata.filename,
                metadata.is_synthesised,
            )
        await conn.copy_records_to_table(
            table_name="electricity_meters_synthesised",
            schema_name="client_meters",
            records=zip(
                itertools.repeat(metadata.dataset_id, len(synthetic_hh_df)),
                synthetic_hh_df["start_ts"],
                synthetic_hh_df["end_ts"],
                synthetic_hh_df["consumption_kwh"],
                strict=True,
            ),
            columns=["dataset_id", "start_ts", "end_ts", "consumption_kwh"],
        )

        if params.bundle_metadata is not None:
            assert params.bundle_metadata.dataset_type == DatasetTypeEnum.ElectricityMeterDataSynthesised
            await file_self_with_bundle(conn, bundle_metadata=params.bundle_metadata)

            # If we didn't file the associated electricity meter data in the bundle that we used to generate this,
            # do so now.
            base_in_db = await conn.fetchval(
                """SELECT exists
                (SELECT 1
                FROM data_bundles.dataset_links
                WHERE bundle_id = $1 AND dataset_id = $2 AND dataset_type = $3)""",
                params.bundle_metadata.bundle_id,
                params.dataset_id,  # the ID of the underlying meter dataset
                DatasetTypeEnum.ElectricityMeterData,
            )
            if not base_in_db:
                meter_meta = params.bundle_metadata.model_copy(deep=True)
                meter_meta.dataset_id = params.dataset_id
                meter_meta.dataset_type = DatasetTypeEnum.ElectricityMeterData
                await file_self_with_bundle(conn, bundle_metadata=meter_meta)

    logger = logging.getLogger(__name__)
    logger.info(f"Electricity load generation {metadata.dataset_id} completed.")
    return metadata


@router.post("/get-electricity-load", tags=["get", "electricity"])
async def get_electricity_load(params: DatasetIDWithTime, pool: DatabasePoolDep) -> EpochElectricityEntry:
    """
    Get a (possibly synthesised) half hourly electricity load dataset.

    Specify a dataset ID corresponding to a set of half hourly or monthly meter readings,
    and the timestamps you're interested in.
    Currently, if the dataset ID you specify is monthly, this method will fail.
    However, it will provide synthesised data in future (maybe via a `generate-` call?)

    Parameters
    ----------
    params
        An electricity meter dataset, and start / end timestamps corresponding to the time period of interest.

    Returns
    -------
    epoch_electricity_entries
        A list of EPOCH formatted JSON entries including consumption in kWh

    Raises
    ------
    *HTTPException(400)*
        If the requested meter dataset is half hourly.
    """
    logger = logging.getLogger(__name__)
    rdgs_fuel_synthetic = await pool.fetchrow(
        """
        SELECT
            reading_type,
            fuel_type,
            is_synthesised
        FROM client_meters.metadata AS m
        WHERE dataset_id = $1
        LIMIT 1""",
        params.dataset_id,
    )

    if rdgs_fuel_synthetic is None:
        raise HTTPException(400, f"Could not find a reading or fuel type for {params.dataset_id}")
    reading_type, fuel_type, is_synthesised = rdgs_fuel_synthetic

    if reading_type != "halfhourly":
        raise HTTPException(
            400,
            f"Requested dataset {params.dataset_id} was for {reading_type}, not 'halfhourly'. "
            + "Consider generating a new dataset with `generate-electrical-load`",
        )
    if fuel_type != "elec":
        raise HTTPException(400, f"Requested dataset {params.dataset_id} was for {fuel_type}, not 'elec' ")

    table_name = "electricity_meters_synthesised" if is_synthesised else "electricity_meters"

    res = await pool.fetch(
        f"""
        SELECT
            start_ts,
            end_ts,
            consumption_kwh
        FROM client_meters.{table_name}
        WHERE dataset_id = $1
        AND $2 <= start_ts
        AND end_ts <= $3
        ORDER BY start_ts ASC""",
        params.dataset_id,
        params.start_ts,
        params.end_ts,
    )

    elec_df = pd.DataFrame.from_records(
        cast(RecordMapping, res), columns=["start_ts", "end_ts", "consumption_kwh"], coerce_float=True, index="start_ts"
    )
    elec_df["start_ts"] = elec_df.index
    in_timestamps_mask = np.logical_and(elec_df.start_ts >= params.start_ts, elec_df.end_ts <= params.end_ts)
    elec_df = elec_df[in_timestamps_mask]
    if elec_df.empty:
        logger.warning(
            f"Got an empty electricity meter dataset for {params.dataset_id} between {params.start_ts} and {params.end_ts}"
        )
        return EpochElectricityEntry(timestamps=[], data=[])

    assert isinstance(elec_df.index, pd.DatetimeIndex), "Heating dataframe must have a DatetimeIndex"
    # Now restructure for EPOCH
    elec_df = elec_df[["consumption_kwh"]].interpolate(method="time").ffill().bfill()

    return EpochElectricityEntry(timestamps=elec_df.index.to_list(), data=elec_df["consumption_kwh"].to_list())


@router.post("/get-blended-electricity-load", tags=["get", "electricity"])
async def get_blended_electricity_load(
    real_params: DatasetIDWithTime | None, synthetic_params: DatasetIDWithTime | None, pool: DatabasePoolDep
) -> EpochElectricityEntry:
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
    if real_params is None and synthetic_params is None:
        raise HTTPException(400, "Got None for both real and synthetic electrical datasets. Are they both missing?")
    logger = logging.getLogger(__name__)
    if real_params is not None:
        try:
            real_data = await get_electricity_load(real_params, pool=pool)
        except HTTPException as ex:
            logger.info(f"Couldn't get electricity load data for {real_params}, returning only synthetic. Due to {ex}")
            real_data = EpochElectricityEntry(timestamps=[], data=[])

    if synthetic_params is not None:
        synth_data = await get_electricity_load(synthetic_params, pool=pool)
    else:
        # Early return as we've got no synthetic data
        logger.info(f"Got no synthetic data, returning only {real_params}")
        return real_data

    for idx, timestamp in enumerate(synth_data.timestamps):
        if timestamp in real_data.timestamps:
            synth_data.data[idx] = real_data.data[real_data.timestamps.index(timestamp)]

    return synth_data
