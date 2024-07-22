import datetime
import logging
import uuid

import pandas as pd
from fastapi import APIRouter, Form, HTTPException, Request, UploadFile

from ..internal.epl_typing import HHDataFrame, MonthlyDataFrame, WeatherDataFrame
from ..internal.gas_meters import (
    hh_gas_to_monthly,
    monthly_to_hh_hload,
    parse_be_st_format,
    parse_octopus_half_hourly,
)
from .models import (
    DatasetID,
    DatasetIDWithTime,
    FuelEnum,
    GasDatasetEntry,
    WeatherRequest,
    site_id_t,
)
from .weather import get_weather

router = APIRouter()


@router.post("/upload-meter-data/")
async def upload_meter_data(
    request: Request,
    file: UploadFile,
    site_id: site_id_t = Form(...), # noqa
    fuel_type: FuelEnum = Form(...), # noqa
):
    """
    Upload a file of meter data to the database.

    This should also come with some form data about the site this meter is associated with, and the type of fuel that's
    being metered.

    The file should come as a multipart file upload, and the filename should represent the file it came from.
    The backend will attempt to identify everything about the file, including its format and how frequently the readings
    were taken. It may fail to parse.

    Parameters
    ----------
    request
        FastAPI request object that is handled automatically. This contains a database connection pool object.
    file
        Uploaded file, e.g. "consumption.csv" or "gas_meters.xlsx".
    site_id
        Name of the site that this dataset should be associated with. This will complain if that site doesn't already exist.
    fuel_type
        The type of fuel that the dataset is measuring. Currently accepts {"gas", "elec"}.

    Returns
    -------
    HTTP Status Code

    Raises
    ------
    400
        In case of parsing error
    """
    if file.filename is None:
        raise HTTPException(400, f"Received empty file: {file.filename}")
    if file.filename.endswith(".csv"):
        df = parse_octopus_half_hourly(file.file)
        reading_type = "halfhourly"
    elif file.filename.endswith(".xlsx"):
        df = parse_be_st_format(file.file)
        reading_type = "manual"
    else:
        raise HTTPException(400, f"Could not parse {file.filename} due to an unknown format.")

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
                """INSERT INTO client_meters.metadata (dataset_id, created_at, site_id, fuel_type, reading_type, filename)
                            VALUES ($1, $2, $3, $4, $5)""",
                metadata["dataset_id"],
                metadata["created_at"],
                metadata["site_id"],
                metadata["fuel_type"],
                metadata["reading_type"],
                metadata["filename"],
            )

            await conn.executemany(
                f"""INSERT INTO client_meters.{table_name} (dataset_id, start_ts, end_ts, consumption_kwh)
                                VALUES ($1, $2, $3, $4)""",
                list(zip(
                        [metadata["dataset_id"] for _ in df.index],
                        df.index,
                        df.end_ts,
                        df.consumption,
                        strict=False,
                    )
                )
            )

    return 200


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
    list of records in the form [{"start_ts": ..., "end_ts": ..., "consumption": ...}, ...]
    """
    async with request.state.pgpool.acquire() as conn:
        res = await conn.fetch(
            """SELECT
                                start_ts,
                               end_ts,
                               consumption_kwh as consumption
                               FROM client_meters.gas_meters
                               WHERE dataset_id = $1
                               ORDER BY start_ts ASC""",
            dataset_id.dataset_id,
        )
    return [{"start_ts": item[0], "end_ts": item[1], "consumption": item[2]} for item in res]


@router.post("/get-heating-load")
async def get_heating_load(request: Request, params: DatasetIDWithTime):
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
            params.dataset_id,
        )
        location, reading_type = await conn.fetchrow(
            """SELECT
            location,
            m.reading_type
            FROM
            client_meters.metadata AS m
            LEFT JOIN client_info.site_info AS s
            ON s.site_id = m.site_id WHERE dataset_id = $1
            LIMIT 1""",
            params.dataset_id,
        )
        if location is None:
            raise HTTPException(400, f"Did not find a location for dataset {params.dataset_id}.")

    weather = await get_weather(
        request,
        WeatherRequest(location=location, start_ts=params.start_ts, end_ts=params.end_ts),
    )

    gas_df = pd.DataFrame.from_records(res, columns=["start_ts", "end_ts", "consumption"], index="start_ts")
    gas_df["start_ts"] = gas_df.index
    if gas_df.empty:
        raise HTTPException(
            400,
            f"Got an empty dataset for {location} between {params.start_ts} and {params.end_ts}",
        )

    weather_df = WeatherDataFrame(
        pd.DataFrame.from_records(
            weather,
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
        logging.info(f"Got reading type hh for {params.dataset_id} in {location}, so resampling.")
        gas_df = hh_gas_to_monthly(HHDataFrame(gas_df))
    elif reading_type in {"automatic", "manual"}:
        print(f"Got reading type {reading_type} for {params.dataset_id} in {location}.")
        gas_df = MonthlyDataFrame(gas_df)
        gas_df["days"] = (gas_df["end_ts"] - gas_df["start_ts"]).dt.total_seconds() / pd.Timedelta(days=1).total_seconds()
    else:
        raise HTTPException(400, f"Unknown reading type {reading_type} for this dataset.")

    processed_df = monthly_to_hh_hload(gas_df, weather_df)
    processed_df["timestamp"] = processed_df.index
    response = processed_df.to_json(orient="records")
    return response
