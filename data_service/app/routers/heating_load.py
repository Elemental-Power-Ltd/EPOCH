"""
Endpoints for heating load calculations, including heating:dhw splits.

These generally use a combination of gas meters and external weather to perform regression.
"""

import datetime
import json
import logging
import uuid

import numpy as np
import pandas as pd
import sklearn  # type: ignore
from fastapi import APIRouter, HTTPException

from ..database import DatabaseDep, HttpClientDep
from ..internal.epl_typing import HHDataFrame, MonthlyDataFrame, WeatherDataFrame
from ..internal.gas_meters import hh_gas_to_monthly, monthly_to_hh_hload
from ..internal.utils import hour_of_year
from ..models.core import DatasetIDWithTime
from ..models.heating_load import EpochHeatingEntry, HeatingLoadMetadata
from ..models.weather import WeatherRequest
from .weather import get_weather

router = APIRouter()


@router.post("/generate-heating-load", tags=["generate", "heating"])
async def generate_heating_load(
    params: DatasetIDWithTime, conn: DatabaseDep, http_client: HttpClientDep
) -> HeatingLoadMetadata:
    """Generate a heating load for this specific site, using regression analysis.

    Given a specific dataset, this will look up the associated site and get some weather data.
    Then, it will use the heating degree days over that time period and regress them against the
    actual gas usage.
    The regression will then provide a measure of domestic hot water and heating load for the building,
    which we can reconstruct into a demand curve (which is different to the heating that was actually provided).

    It might be helpful to have called `get-weather` for this location beforehand to make sure the relevant weather
    is cached in the database (otherwise we can do it here, but it might be inconveniently slow).

    Be aware that this will take a few seconds to complete.

    Parameters
    ----------
    *request*
        Internal FastAPI request object

    *params*
        Dataset (linked to a site), and timestamps you're interested in.
        This dataset ID is the gas dataset you want to use for the calculation, and shouldn't be confused
        with the returned dataset ID that you'll get at the end of this function.

    Returns
    -------
    heating_load_metadata
        Some useful information about the heating load we've inserted into the database.
    """
    res = await conn.fetchrow(
        """
        SELECT
            location,
            s.site_id,
            m.reading_type,
            m.fuel_type
        FROM client_meters.metadata AS m
        LEFT JOIN client_info.site_info AS s
        ON s.site_id = m.site_id WHERE dataset_id = $1
        LIMIT 1""",
        params.dataset_id,
    )

    if res is None:
        raise HTTPException(400, f"{params.dataset_id} is not a valid gas meter dataset.")
    location, site_id, reading_type, fuel_type = res
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
            WeatherRequest(location=location, start_ts=start_ts, end_ts=end_ts), conn=conn, http_client=http_client
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
    heating_df = HHDataFrame(monthly_to_hh_hload(gas_df, weather_df).drop(columns=["timedelta"]))
    heating_df = HHDataFrame(heating_df.join(weather_df["temp"]).rename(columns={"temp": "air_temperature"}))
    heating_df = HHDataFrame(heating_df.resample(pd.Timedelta(minutes=30)).mean().interpolate(method="time"))

    monthly_predicteds = []
    for start_ts, end_ts in zip(gas_df.start_ts, gas_df.end_ts, strict=False):
        mask = np.logical_and(start_ts <= heating_df.index, heating_df.index < end_ts)
        monthly_predicteds.append(heating_df.loc[mask, "predicted"].sum())
    score = sklearn.metrics.r2_score(monthly_predicteds, gas_df["consumption"])

    metadata = {
        "dataset_id": uuid.uuid4(),
        "site_id": site_id,
        "created_at": datetime.datetime.now(datetime.UTC),
        "params": json.dumps({"source_dataset_id": str(params.dataset_id), "r2_score": score}),
    }

    async with conn.transaction():
        await conn.execute(
            """
            INSERT INTO
                heating.metadata (
                    dataset_id,
                    site_id,
                    created_at,
                    params)
            VALUES ($1, $2, $3, $4)""",
            metadata["dataset_id"],
            metadata["site_id"],
            metadata["created_at"],
            metadata["params"],
        )

        await conn.executemany(
            """
            INSERT INTO
                heating.synthesised (
                    dataset_id,
                    start_ts,
                    end_ts,
                    heating,
                    dhw,
                    air_temperature)
            VALUES ($1, $2, $3, $4, $5, $6)""",
            zip(
                [metadata["dataset_id"] for _ in heating_df.index],
                heating_df.index,
                heating_df.index + pd.Timedelta(minutes=30),
                heating_df["heating"],
                heating_df["dhw"],
                heating_df["air_temperature"],
                strict=True,
            ),
        )
    return HeatingLoadMetadata(**metadata)


@router.post("/get-heating-load", tags=["get", "heating"])
async def get_heating_load(params: DatasetIDWithTime, conn: DatabaseDep) -> list[EpochHeatingEntry]:
    """
    Get a previously generated heating load in an EPOCH friendly format.

    Provided with a given heating load dataset (not the dataset of gas data!) and timestamps,
    this will return an EPOCH json.
    Currently just supplies one heating load, but will be extended in future to provide many.

    Parameters
    ----------
    request
        Internal FastAPI request object
    *params*
        Heating Load dataset ID (not a gas dataset ID!) and timestamps you're interested in (probably a whole year)

    Returns
    -------
    epoch_heating_entries
        JSON with HLoad1 and DHWLoad1, oriented by records.
    """
    res = await conn.fetch(
        """
        SELECT
            start_ts AS timestamp,
            heating,
            dhw,
            air_temperature
        FROM heating.synthesised
        WHERE
            dataset_id = $1
            AND $2 <= start_ts
            AND end_ts <= $3""",
        params.dataset_id,
        params.start_ts,
        params.end_ts,
    )
    heating_df = pd.DataFrame.from_records(res, index="timestamp", columns=["timestamp", "heating", "dhw", "air_temperature"])
    heating_df.index = pd.to_datetime(heating_df.index)
    assert isinstance(heating_df.index, pd.DatetimeIndex), "Heating dataframe must have a DatetimeIndex"
    heating_df["Date"] = heating_df.index.strftime("%d-%b")
    heating_df["StartTime"] = heating_df.index.strftime("%H:%M")
    heating_df["HourOfYear"] = heating_df.index.map(hour_of_year)
    heating_df = heating_df.rename(columns={"heating": "HLoad1", "dhw": "DHWLoad1", "air_temperature":"AirTemp"})
    return [
        EpochHeatingEntry(
            Date=item["Date"],
            StartTime=item["StartTime"],
            HourOfYear=item["HourOFYear"],
            HLoad1=item["HLoad1"],
            DHWLoad1=item["DHWLoad1"],
            AirTemp=item["AirTemp"]
        )
        for item in heating_df.to_dict(orient="records")
    ]
