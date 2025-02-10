"""API endpoints for electrical loads, including resampling."""

import datetime
import logging
import uuid

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from ..dependencies import DatabaseDep, DatabasePoolDep, HttpClientDep, VaeDep
from ..internal.elec_meters import daily_to_hh_eload, day_type, load_all_scalers, monthly_to_daily_eload
from ..internal.epl_typing import DailyDataFrame, MonthlyDataFrame
from ..internal.utils import add_epoch_fields, get_bank_holidays
from ..models.core import DatasetIDWithTime, FuelEnum
from ..models.electricity_load import ElectricalLoadMetadata, ElectricalLoadRequest, EpochElectricityEntry

router = APIRouter()


@router.post("/generate-electricity-load", tags=["electricity", "generate"])
async def generate_electricity_load(
    params: ElectricalLoadRequest, vae: VaeDep, pool: DatabasePoolDep, http_client: HttpClientDep
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

    raw_df = pd.DataFrame.from_records(dataset, columns=["start_ts", "end_ts", "consumption_kwh"])
    raw_df.index = pd.DatetimeIndex(pd.to_datetime(raw_df["start_ts"]))

    public_holidays = await get_bank_holidays("England", http_client=http_client)
    if reading_type != "halfhourly":
        daily_df = monthly_to_daily_eload(MonthlyDataFrame(raw_df), public_holidays=public_holidays)
    else:
        # We've got half hourly data, so we can skip the horrible daily profiles bit
        daily_df = DailyDataFrame(raw_df[["consumption_kwh"]].resample(pd.Timedelta(days=1)).sum())
        daily_df["start_ts"] = daily_df.index
        daily_df["end_ts"] = daily_df.index + pd.Timedelta(days=1)

    weekly_type_df = (
        daily_df[["consumption_kwh"]]
        .groupby([lambda dt, ph=public_holidays: day_type(dt, public_holidays=ph), lambda dt: dt.weekofyear])
        .mean()
    )
    synthetic_daily_df = DailyDataFrame(
        pd.DataFrame(
            index=pd.date_range(
                params.start_ts.astimezone(datetime.UTC),
                params.end_ts.astimezone(datetime.UTC),
                freq=pd.Timedelta(days=1),
                inclusive="both",
                tz=datetime.UTC,
            )
        )
    )
    all_consumptions: list[float] = []
    for day in synthetic_daily_df.index:
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
    synthetic_hh_df = daily_to_hh_eload(synthetic_daily_df, scalers=load_all_scalers(), model=vae)

    new_dataset_id = uuid.uuid4()
    metadata = {
        "dataset_id": new_dataset_id,
        "created_at": datetime.datetime.now(tz=datetime.UTC),
        "site_id": site_id,
        "fuel_type": FuelEnum.elec,
        "reading_type": "halfhourly",
        "filename": str(params.dataset_id),
        "is_synthesised": True,
    }
    synthetic_hh_df["dataset_id"] = new_dataset_id
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
                metadata["dataset_id"],
                metadata["site_id"],
                metadata["created_at"],
                metadata["fuel_type"],
                metadata["reading_type"],
                metadata["filename"],
                metadata["is_synthesised"],
            )
        await conn.copy_records_to_table(
            table_name="electricity_meters_synthesised",
            schema_name="client_meters",
            records=synthetic_hh_df.itertuples(index=False),
            columns=synthetic_hh_df.columns.to_list(),
            timeout=10,
        )
    return ElectricalLoadMetadata(
        dataset_id=metadata["dataset_id"],
        created_at=metadata["created_at"],
        site_id=metadata["site_id"],
        fuel_type=metadata["fuel_type"],
        reading_type=metadata["reading_type"],
        filename=metadata["filename"],
        is_synthesised=metadata["is_synthesised"],
    )


@router.post("/get-electricity-load", tags=["get", "electricity"])
async def get_electricity_load(params: DatasetIDWithTime, conn: DatabaseDep) -> list[EpochElectricityEntry]:
    """
    Get a (possibly synthesised) half hourly electricity load dataset.

    Specify a dataset ID corresponding to a set of half hourly or monthly meter readings,
    and the timestamps you're interested in.
    Currently, if the dataset ID you specify is monthly, this method will fail.
    However, it will provide synthesised data in future (maybe via a `generate-` call?)

    Parameters
    ----------
    *params*
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
    rdgs_fuel_synthetic = await conn.fetchrow(
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

    if is_synthesised:
        table_name = "electricity_meters_synthesised"
    else:
        table_name = "electricity_meters"

    res = await conn.fetch(
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
        res, columns=["start_ts", "end_ts", "consumption_kwh"], coerce_float=["consumption_kwh"], index="start_ts"
    )
    elec_df["start_ts"] = elec_df.index
    print(params.start_ts, params.end_ts)
    in_timestamps_mask = np.logical_and(elec_df.start_ts >= params.start_ts, elec_df.end_ts <= params.end_ts)
    elec_df = elec_df[in_timestamps_mask]
    if elec_df.empty:
        logging.warning(
            f"Got an empty electricity meter dataset for {params.dataset_id} between {params.start_ts} and {params.end_ts}"
        )
        return []

    assert isinstance(elec_df.index, pd.DatetimeIndex), "Heating dataframe must have a DatetimeIndex"
    # Now restructure for EPOCH
    elec_df = elec_df[["consumption_kwh"]].interpolate(method="time").ffill().bfill()
    elec_df = add_epoch_fields(elec_df)

    return [
        EpochElectricityEntry(
            Date=item["Date"], StartTime=item["StartTime"], HourOfYear=item["HourOfYear"], FixLoad1=item["consumption_kwh"]
        )
        for item in elec_df.to_dict(orient="records")
    ]


@router.post("/get-blended-electricity-load", tags=["get", "electricity"])
async def get_blended_electricity_load(
    real_params: DatasetIDWithTime | None, synthetic_params: DatasetIDWithTime | None, pool: DatabasePoolDep
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
    if real_params is None and synthetic_params is None:
        raise HTTPException(400, "Got None for both real and synthetic electrical datasets. Are they both missing?")
    logger = logging.getLogger(__name__)
    async with pool.acquire() as conn:
        if real_params is not None:
            try:
                real_data = await get_electricity_load(real_params, conn=conn)
            except HTTPException as ex:
                logger.warning(f"Couldn't get electricity load data for {real_params}, returning only synthetic. Due to {ex}")
                real_data = []

        if synthetic_params is not None:
            synth_data = await get_electricity_load(synthetic_params, conn=conn)
        else:
            # Early return as we've got no synthetic data
            logger.warning(f"Got no synthetic data, returning only {real_params}")
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
