"""Endpoints for uploading, manipulating and getting client meter data.

When clients provide us with meter data, we store it raw in the database.
These functions provider wrappers to get it in more sensible formats.
"""

import datetime
import itertools
import uuid

import numpy as np
from fastapi import APIRouter, Form, HTTPException, UploadFile

from ..dependencies import DatabaseDep
from ..internal.epl_typing import HHDataFrame, MonthlyDataFrame
from ..internal.gas_meters import try_meter_parsing
from ..models.core import (
    DatasetID,
    FuelEnum,
    site_id_t,
)
from ..models.meter_data import GasDatasetEntry, MeterEntries, MeterMetadata

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
                    filename,
                    is_synthesised)
            VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6,
                    $7)""",
            entries.metadata.dataset_id,
            entries.metadata.created_at,
            entries.metadata.site_id,
            entries.metadata.fuel_type,
            entries.metadata.reading_type,
            entries.metadata.filename,
            entries.metadata.is_synthesised,
        )

        await conn.copy_records_to_table(
            table_name=table_name,
            schema_name="client_meters",
            records=[(entries.metadata.dataset_id, item.start_ts, item.end_ts, item.consumption) for item in entries.data],
            columns=["dataset_id", "start_ts", "end_ts", "consumption_kwh"],
        )

    return MeterMetadata(
        dataset_id=entries.metadata.dataset_id,
        created_at=entries.metadata.created_at,
        site_id=entries.metadata.site_id,
        fuel_type=entries.metadata.fuel_type,
        reading_type=entries.metadata.reading_type,
        filename=entries.metadata.filename,
        is_synthesised=entries.metadata.is_synthesised,
    )


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
        df, _ = try_meter_parsing(file.file)
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
        "is_synthesised": False,
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

    df["start_ts"] = df.index
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
                    filename,
                    is_synthesised)
            VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6,
                    $7)""",
            metadata["dataset_id"],
            metadata["created_at"],
            metadata["site_id"],
            metadata["fuel_type"],
            metadata["reading_type"],
            metadata["filename"],
            metadata["is_synthesised"],
        )

        await conn.copy_records_to_table(
            table_name=table_name,
            schema_name="client_meters",
            records=zip(
                itertools.repeat(metadata["dataset_id"], len(df)),
                df["start_ts"].dt.to_pydatetime(),
                df["end_ts"].dt.to_pydatetime(),
                df["consumption"],
                strict=True,
            ),
            columns=["dataset_id", "start_ts", "end_ts", "consumption_kwh"],
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
    fuel_type = await conn.fetchval("""SELECT fuel_type FROM client_meters.metadata WHERE dataset_id = $1""", dataset_id)
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
        dataset_id,
    )
    if not res:
        raise HTTPException(400, f"Got an empty meter dataset for {dataset_id}.")
    return [GasDatasetEntry(**item) for item in res]
