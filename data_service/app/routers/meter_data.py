import datetime
import uuid

import numpy as np
import pandas as pd
import pydantic
from fastapi import APIRouter, Form, HTTPException, Request, UploadFile

from ..internal.epl_typing import HHDataFrame, MonthlyDataFrame
from ..internal.gas_meters import try_meter_parsing
from ..internal.utils import hour_of_year
from ..models.core import (
    DatasetID,
    DatasetIDWithTime,
    FuelEnum,
    GasDatasetEntry,
    site_id_t,
)

router = APIRouter()


@router.post("/upload-meter-data", tags=["db", "add", "meter"])
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
            400,
            f"Fuel type {fuel_type} is not supported. Please select from ('gas', 'elec')",
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


class EpochElectricityEntry(pydantic.BaseModel):
    Date: str = pydantic.Field(examples=["Jan-01", "Dec-31"], pattern=r"[0-9][0-9]-[A-Za-z]*")
    StartTime: datetime.time = pydantic.Field(examples=["00:00", "13:30"])
    HourOfYear: float = pydantic.Field(examples=[1, 24 * 365 - 1])
    FixLoad1: float = pydantic.Field(examples=[0.123, 4.56])


@router.post("/get-electricity-load", tags=["get", "electricity"])
async def get_electricity_load(request: Request, params: DatasetIDWithTime) -> list[EpochElectricityEntry]:
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
    elec_df = elec_df.resample(pd.Timedelta(minutes=30)).sum().interpolate(method="time")

    assert isinstance(elec_df.index, pd.DatetimeIndex), "Heating dataframe must have a DatetimeIndex"
    elec_df["Date"] = elec_df.index.strftime("%d-%b")
    elec_df["StartTime"] = elec_df.index.strftime("%H:%M")
    elec_df["HourOfYear"] = elec_df.index.map(hour_of_year)
    elec_df = elec_df.rename(columns={"consumption": "FixLoad1"})
    return elec_df.to_dict(orient="records")
