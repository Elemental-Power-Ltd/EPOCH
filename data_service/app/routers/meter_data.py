"""Endpoints for uploading, manipulating and getting client meter data.

When clients provide us with meter data, we store it raw in the database.
These functions provider wrappers to get it in more sensible formats.
"""

import datetime
import uuid

import numpy as np
import pandas as pd
from fastapi import APIRouter, Form, HTTPException, UploadFile

from ..dependencies import DatabaseDep
from ..internal.epl_typing import HHDataFrame, MonthlyDataFrame
from ..internal.gas_meters import try_meter_parsing
from ..internal.utils import hour_of_year
from ..models.core import (
    DatasetID,
    DatasetIDWithTime,
    FuelEnum,
    site_id_t,
)
from ..models.meter_data import EpochElectricityEntry, GasDatasetEntry, MeterEntries, MeterMetadata

router = APIRouter()


@router.post("/upload-meter-entries", tags=["db", "add", "meter"])
async def upload_meter_entries(conn: DatabaseDep, entries: MeterEntries) -> MeterMetadata:
    """
    Upload some pre-parsed meter data to the database.

    Parameters
    ----------
    *entries*
        Pre-parsed meter entries and associated metadata

    Returns
    -------
    HTTP Status Code

    Raises
    ------
    400
        In case of parsing error
    """
    if entries.metadata.fuel_type == FuelEnum.gas:
        table_name = "gas_meters"
    elif entries.metadata.fuel_type == FuelEnum.elec:
        table_name = "electricity_meters"
    else:
        raise HTTPException(
            400,
            f"Fuel type {entries.metadata.fuel_type} is not supported. Please select from ('gas', 'elec')",
        )

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
            entries.metadata.dataset_id,
            entries.metadata.created_at,
            entries.metadata.site_id,
            entries.metadata.fuel_type,
            entries.metadata.reading_type,
            entries.metadata.filename,
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
            [(entries.metadata.dataset_id, item.start_ts, item.end_ts, item.consumption) for item in entries.data],
        )

    return entries.metadata


@router.post("/upload-meter-file", tags=["db", "add", "meter"])
async def upload_meter_file(
    conn: DatabaseDep,
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
        The type of fuel that the dataset is measuring. Currently accepts `{"gas", "elec"}`.

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
        timedeltas = np.ediff1d(hh_or_monthly_df.index).astype(np.timedelta64)
        timedeltas_mask = np.logical_and(
            timedeltas > np.timedelta64(datetime.timedelta(seconds=1)),
            timedeltas <= np.timedelta64(datetime.timedelta(minutes=30)),
        )
        return bool(np.mean(timedeltas_mask.astype(float)) > 0.5)

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
            400,
            f"Fuel type {fuel_type} is not supported. Please select from ('gas', 'elec')",
        )

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
            zip(
                [metadata["dataset_id"] for _ in df.index],
                df.index,
                df.end_ts,
                df.consumption,
                strict=True,
            ),
        )

    return {"rows_uploaded": len(df), "reading_type": reading_type}


@router.post("/get-meter-data", tags=["db", "meter"])
async def get_meter_data(dataset_id: DatasetID, conn: DatabaseDep) -> list[GasDatasetEntry]:
    """
    Get a specific set of meter data associated with a single dataset ID.

    This exclusively retrieves gas meter data as we got them from the client, each one covering
    a specific period of time.

    Parameters
    ----------
    request
        FastAPI internal request object
    dataset_id
        Database ID for a set of gas meter readings.

    Returns
    -------
    list of records in the form `[{"start_ts": ..., "end_ts": ..., "consumption": ...}, ...]`
    """
    # TODO (2024-08-05 MHJB): make this return an EPOCH oriented object
    fuel_type = await conn.fetchval(
        """SELECT fuel_type FROM client_meters.metadata WHERE dataset_id = $1""", dataset_id.dataset_id
    )
    if not fuel_type:
        raise HTTPException(400, f"Dataset {dataset_id} not found in meter datasets. Could it be an ID for another type?")
    table_name = "gas_meters" if fuel_type == "gas" else "electricity_meters"
    res = await conn.fetch(
        f"""
        SELECT
            start_ts,
            end_ts,
            consumption_kwh as consumption
        FROM client_meters.{table_name}
        WHERE dataset_id = $1
        ORDER BY start_ts ASC""",
        dataset_id.dataset_id,
    )
    if not res:
        raise HTTPException(400, f"Got an empty meter dataset for {dataset_id}.")
    return [GasDatasetEntry(**item) for item in res]


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
    *request*
        FastAPI internal request object

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
    readings_and_fuel = await conn.fetchrow(
        """
        SELECT
            reading_type,
            fuel_type
        FROM client_meters.metadata AS m
        WHERE dataset_id = $1
        LIMIT 1""",
        params.dataset_id,
    )
    if readings_and_fuel is None:
        raise HTTPException(400, f"Could not find a reading or fuel type for {params.dataset_id}")
    reading_type, fuel_type = readings_and_fuel
    if reading_type != "halfhourly":
        raise HTTPException(400, "Electrical load resampling not yet supported, pick a half hourly dataset.")

    if fuel_type != "elec":
        raise HTTPException(400, f"Requested dataset {params.dataset_id} was for {fuel_type}, not 'elec' ")

    if (params.end_ts - params.start_ts) > datetime.timedelta(days=366):
        raise HTTPException(
            400,
            f"Timestamps {params.start_ts.isoformat()} and {params.end_ts.isoformat()}"
            + "are more than 1 year apart. This would result in duplicate readings.",
        )
    res = await conn.fetch(
        """
        SELECT
            start_ts,
            consumption_kwh AS consumption
        FROM client_meters.electricity_meters
        WHERE dataset_id = $1
        AND $2 <= start_ts
        AND end_ts < $3
        ORDER BY start_ts ASC""",
        params.dataset_id,
        params.start_ts,
        params.end_ts,
    )

    # Now restructure for EPOCH
    elec_df = pd.DataFrame.from_records(
        res, columns=["start_ts", "consumption"], coerce_float=["consumption"], index="start_ts"
    )
    if elec_df.empty:
        raise HTTPException(400, f"Got an empty dataset for {params.dataset_id}.")
    elec_df = elec_df.resample(pd.Timedelta(minutes=60)).sum().interpolate(method="time")

    assert isinstance(elec_df.index, pd.DatetimeIndex), "Heating dataframe must have a DatetimeIndex"
    elec_df["Date"] = elec_df.index.strftime("%d-%b")
    elec_df["StartTime"] = elec_df.index.strftime("%H:%M")
    elec_df["HourOfYear"] = elec_df.index.map(hour_of_year)
    elec_df = elec_df.rename(columns={"consumption": "FixLoad1"})

    return [
        EpochElectricityEntry(
            Date=item["Date"], StartTime=item["StartTime"], HourOfYear=item["HourOfYear"], FixLoad1=item["FixLoad1"]
        )
        for item in elec_df.to_dict(orient="records")
    ]
