import datetime
import json
import logging
import uuid

import httpx
import numpy as np
import pandas as pd
import pydantic
from fastapi import APIRouter, Form, HTTPException, Request, UploadFile

from ..internal.epl_typing import HHDataFrame, MonthlyDataFrame, WeatherDataFrame
from ..internal.gas_meters import hh_gas_to_monthly, monthly_to_hh_hload, try_meter_parsing
from ..internal.pvgis import get_pvgis_optima, get_renewables_ninja_data
from ..internal.utils import hour_of_year
from .models import DatasetID, DatasetIDWithTime, FuelEnum, GasDatasetEntry, RenewablesRequest, WeatherRequest, site_id_t
from .weather import get_weather

router = APIRouter()


@router.post("/upload-meter-data/")
async def upload_meter_data(
    request: Request,
    file: UploadFile,
    site_id: site_id_t = Form(...),  # noqa
    fuel_type: FuelEnum = Form(...),  # noqa
) -> dict[str, str | int]:
    """
    Upload a file of meter data to the database.

    This should also come with some form data about the site this meter is associated with, and the type of fuel that's
    being metered.

    The file should come as a multipart file upload, and the filename should represent the file it came from.
    The backend will attempt to identify everything about the file, including its format and how frequently the readings
    were taken. It may fail to parse.

    Parameters
    ----------
    *request*
        FastAPI request object that is handled automatically. This contains a database connection pool object.

    *file*
        Uploaded file, e.g. "consumption.csv" or "gas_meters.xlsx".

    *site_id*
        Name of the site that this dataset should be associated with. This will complain if that site doesn't already exist.

    *fuel_type*
        The type of fuel that the dataset is measuring. Currently accepts {"gas", "elec"}.

    Returns
    -------
    HTTP Status Code

    Raises
    ------
    400
        In case of parsing error
    """
    try:
        df: HHDataFrame | MonthlyDataFrame = try_meter_parsing(file.file)
    except NotImplementedError as ex:
        raise HTTPException(400, f"Could not parse {file.filename} due to an unknown format.") from ex

    def is_half_hourly(hh_or_monthly_df: HHDataFrame | MonthlyDataFrame) -> bool:
        timedeltas = np.ediff1d(hh_or_monthly_df.index)
        timedeltas_mask = np.logical_and(
            timedeltas > datetime.timedelta(seconds=1), timedeltas <= datetime.timedelta(minutes=30)
        )
        return np.mean(timedeltas_mask.astype(float)) > 0.5

    if is_half_hourly(df):
        reading_type = "halfhourly"
    else:
        reading_type = "manual"

    metadata = {
        "dataset_id": uuid.uuid4(),
        "created_at": datetime.datetime.now(tz=datetime.UTC),
        "site_id": site_id,
        "fuel_type": fuel_type,
        "reading_type": reading_type,
        "filename": file.filename,
    }

    if fuel_type == "gas":
        table_name = "gas_meters"
    elif fuel_type == "elec":
        table_name = "electricity_meters"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Fuel type {fuel_type} is not supported. Please select from ('gas', 'elec')",
        )

    async with request.state.pgpool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO
                    client_meters.metadata (
                        dataset_id,
                        created_at,
                        site_id,
                        fuel_type,
                        reading_type,
                        filename)
                VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5,
                        $6)""",
                metadata["dataset_id"],
                metadata["created_at"],
                metadata["site_id"],
                metadata["fuel_type"],
                metadata["reading_type"],
                metadata["filename"],
            )

            await conn.executemany(
                f"""INSERT INTO
                        client_meters.{table_name} (
                            dataset_id,
                            start_ts,
                            end_ts,
                            consumption_kwh
                        )
                    VALUES (
                        $1,
                        $2,
                        $3,
                        $4)""",
                list(
                    zip(
                        [metadata["dataset_id"] for _ in df.index],
                        df.index,
                        df.end_ts,
                        df.consumption,
                        strict=False,
                    )
                ),
            )

    return {"rows_uploaded": len(df), "reading_type": reading_type}


@router.post("/get-meter-data")
async def get_meter_data(request: Request, dataset_id: DatasetID) -> list[GasDatasetEntry]:
    """
    Get a specific set of meter data associated with a single dataset ID.

    Parameters
    ----------
    request

    dataset_id

    Returns
    -------
    list of records in the form `[{"start_ts": ..., "end_ts": ..., "consumption": ...}, ...]`
    """
    async with request.state.pgpool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                start_ts,
                end_ts,
                consumption_kwh as consumption
            FROM client_meters.gas_meters
            WHERE dataset_id = $1
            ORDER BY start_ts ASC""",
            dataset_id.dataset_id,
        )
    return [GasDatasetEntry(**item) for item in res]


@router.post("/get-heating-load")
async def get_heating_load(request: Request, params: DatasetIDWithTime) -> list:
    async with request.state.pgpool.acquire() as conn:
        location, reading_type, fuel_type = await conn.fetchrow(
            """
            SELECT
                location,
                m.reading_type,
                m.fuel_type
            FROM client_meters.metadata AS m
            LEFT JOIN client_info.site_info AS s
            ON s.site_id = m.site_id WHERE dataset_id = $1
            LIMIT 1""",
            params.dataset_id,
        )
        if location is None:
            raise HTTPException(400, f"Did not find a location for dataset {params.dataset_id}.")

        if fuel_type != "gas":
            raise HTTPException(400, f"Dataset ID {params.dataset_id} is for fuel type {fuel_type}, not gas.")
        res = await conn.fetch(
            """
            SELECT
                start_ts,
                end_ts,
                consumption_kwh as consumption
            FROM client_meters.gas_meters
            WHERE dataset_id = $1
            ORDER BY start_ts ASC""",
            params.dataset_id,
        )

    gas_df = pd.DataFrame.from_records(res, columns=["start_ts", "end_ts", "consumption"], index="start_ts")
    gas_df["start_ts"] = gas_df.index
    if gas_df.empty:
        raise HTTPException(
            400,
            f"Got an empty dataset for {location} between {params.start_ts} and {params.end_ts}",
        )
    try:
        start_ts = max(params.start_ts, gas_df["start_ts"].min())
        end_ts = min(params.end_ts, gas_df["end_ts"].max())
        weather = await get_weather(
            request,
            WeatherRequest(location=location, start_ts=start_ts, end_ts=end_ts),
        )
    except HTTPException as ex:
        raise ex

    weather_df = WeatherDataFrame(
        pd.DataFrame.from_records(
            [item.model_dump() for item in weather],
            columns=[
                "timestamp",
                "temp",
                "humidity",
                "solarradiation",
                "windspeed",
                "pressure",
            ],
            index="timestamp",
        )
    )
    if reading_type == "halfhourly":
        logging.info(f"Got reading type {reading_type} for {params.dataset_id} in {location} so resampling.")
        gas_df = hh_gas_to_monthly(HHDataFrame(gas_df))
    elif reading_type in {"automatic", "manual"}:
        logging.info(f"Got reading type {reading_type} for {params.dataset_id} in {location}.")
        gas_df = MonthlyDataFrame(gas_df)
        gas_df["days"] = (gas_df["end_ts"] - gas_df["start_ts"]).dt.total_seconds() / pd.Timedelta(days=1).total_seconds()
    else:
        raise HTTPException(400, f"Unknown reading type {reading_type} for this dataset.")

    if gas_df.shape[0] < 3:
        raise HTTPException(400, f"Dataset covered too little time: {gas_df.index.min()} to {gas_df.index.max()}")
    heating_df = monthly_to_hh_hload(gas_df, weather_df).drop(columns=["timedelta"])
    heating_df = heating_df.resample(pd.Timedelta(minutes=60)).sum()
    assert isinstance(heating_df.index, pd.DatetimeIndex), "Heating dataframe must have a DatetimeIndex"
    heating_df["Date"] = heating_df.index.strftime("%d-%b")
    heating_df["StartTime"] = heating_df.index.strftime("%H:%M")
    heating_df["HourOfYear"] = heating_df.index.map(hour_of_year)
    heating_df = heating_df.rename(columns={"heating": "HLoad1", "dhw": "DHWLoad1"}).drop(columns=["predicted", "hdd"])

    heating_df = heating_df.join(weather_df["temp"]).rename(columns={"temp": "Air-temp"})
    return heating_df.to_dict(orient="records")


@router.post("/get-electricity-load")
async def get_electricity_load(request: Request, params: DatasetIDWithTime) -> list:
    async with request.state.pgpool.acquire() as conn:
        reading_type = await conn.fetchval(
            """
            SELECT
                m.reading_type
            FROM client_meters.metadata AS m
            LEFT JOIN client_info.site_info AS s
            ON s.site_id = m.site_id WHERE dataset_id = $1
            LIMIT 1""",
            params.dataset_id,
        )
        if reading_type != "halfhourly":
            raise HTTPException(500, "Electrical load resampling not yet supported, pick a half hourly dataset.")

        res = await conn.fetch(
            """
            SELECT
                start_ts,
                consumption_kwh AS consumption
            FROM client_meters.electricity_meters
            WHERE dataset_id = $1
            ORDER BY start_ts ASC""",
            params.dataset_id,
        )

    # Now restructure for EPOCH
    elec_df = pd.DataFrame.from_records(
        res, columns=["start_ts", "consumption"], coerce_float=["consumption"], index="start_ts"
    )
    elec_df = elec_df.resample(pd.Timedelta(minutes=60)).sum().interpolate(method="time")
    assert isinstance(elec_df.index, pd.DatetimeIndex), "Heating dataframe must have a DatetimeIndex"
    elec_df["Date"] = elec_df.index.strftime("%d-%b")
    elec_df["StartTime"] = elec_df.index.strftime("%H:%M")
    elec_df["HourOfYear"] = elec_df.index.map(hour_of_year)
    elec_df = elec_df.rename(columns={"consumption": "FixLoad1"})
    return elec_df.to_dict(orient="records")


@router.post("/generate-renewables-generation")
async def generate_renewables_generation(
    request: Request, params: RenewablesRequest
) -> dict[str, str | datetime.datetime | pydantic.UUID4 | dict[str, float | bool]]:
    async with request.state.pgpool.acquire() as conn:
        location, (latitude, longitude) = await conn.fetchrow(
            """
            SELECT
                location,
                coordinates
            FROM client_info.site_info AS s
            WHERE site_id = $1
            LIMIT 1""",
            params.site_id,
        )
        if location is None:
            raise HTTPException(400, f"Did not find a location for dataset {params.site_id}.")

    if params.azimuth is None or params.tilt is None:
        logging.info("Got no azimuth or tilt data, so getting optima from PVGIS.")
        optimal_params = await get_pvgis_optima(latitude=latitude, longitude=longitude)
        azimuth, tilt = float(optimal_params["azimuth"]), float(optimal_params["tilt"])
    else:
        azimuth, tilt = params.azimuth, params.tilt

    try:
        renewables_df = await get_renewables_ninja_data(
            latitude=latitude, longitude=longitude, start_ts=params.start_ts, end_ts=params.end_ts, azimuth=azimuth, tilt=tilt
        )
    except httpx.ReadTimeout as ex:
        raise HTTPException(400, "Call to renewables.ninja timed out, please wait before trying again.") from ex
    if len(renewables_df) < 364 * 24:
        raise HTTPException(500, f"Could not get renewables information for {location}.")

    metadata: dict[str, str | datetime.datetime | pydantic.UUID4 | dict[str, float | bool]] = {
        "data_source": "renewables.ninja",
        "created_at": datetime.datetime.now(datetime.UTC),
        "dataset_id": uuid.uuid4(),
        "site_id": params.site_id,
        "parameters": json.dumps({"azimuth": azimuth, "tilt": tilt, "tracking": params.tracking}),
    }
    async with request.state.pgpool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO
                    renewables.metadata (
                        dataset_id,
                        site_id,
                        created_at,
                        data_source,
                        parameters)
                VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5)""",
                metadata["dataset_id"],
                metadata["site_id"],
                metadata["created_at"],
                metadata["data_source"],
                metadata["parameters"],
            )

            await conn.executemany(
                """INSERT INTO
                        renewables.solar_pv (
                            dataset_id,
                            timestamp,
                            solar_generation
                        )
                    VALUES (
                        $1,
                        $2,
                        $3)""",
                zip(
                    [metadata["dataset_id"] for _ in renewables_df.index],
                    renewables_df.index,
                    renewables_df.pv,
                    strict=True,
                ),
            )
    return metadata


@router.post("/get-renewables-generation")
async def get_renewables_generation(request: Request, params: DatasetIDWithTime) -> list:
    async with request.state.pgpool.acquire() as conn:
        dataset = await conn.fetch(
            """
                SELECT
                    timestamp,
                    solar_generation
                FROM renewables.solar_pv
                WHERE
                    dataset_id = $1
                    AND $2 <= timestamp
                    AND timestamp < $3
                ORDER BY timestamp ASC""",
            params.dataset_id,
            params.start_ts,
            params.end_ts,
        )
    renewables_df = pd.DataFrame.from_records(dataset, columns=["timestamp", "solar_generation"], index="timestamp")
    renewables_df.index = pd.to_datetime(renewables_df.index)
    assert isinstance(renewables_df.index, pd.DatetimeIndex), "Renewables dataframe must have a DatetimeIndex"
    renewables_df["Date"] = renewables_df.index.strftime("%d-%b")
    renewables_df["StartTime"] = renewables_df.index.strftime("%H:%M")
    renewables_df["HourOfYear"] = renewables_df.index.map(hour_of_year)
    renewables_df = renewables_df.rename(columns={"solar_generation": "RGen1"})
    return renewables_df.to_dict(orient="records")
