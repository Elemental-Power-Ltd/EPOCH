"""
Replace datasets where they've gone wrong.

These endpoints generally take in an old dataset_id, and a new CSV of data to replace them with.
The old dataset is left in the database but is orphaned, and the bundle will point towards this replacement dataset from now on.
This may change previous results that have relied on this bundle before you updated it, so be careful.
"""

import datetime
import json
from itertools import repeat

import pandas as pd
from app.dependencies import DatabasePoolDep
from app.internal.utils.uuid import uuid7
from app.models.core import DatasetTypeEnum, FuelEnum, dataset_id_t
from app.models.electricity_load import ElectricalLoadMetadata
from app.models.heating_load import FabricCostBreakdown, HeatingLoadMetadata, HeatingLoadModelEnum
from app.models.import_tariffs import TariffMetadata, TariffProviderEnum
from app.models.meter_data import ReadingTypeEnum
from app.models.renewables import RenewablesMetadata
from fastapi import APIRouter, HTTPException, UploadFile

router = APIRouter(tags=["replace", "db"])


@router.route("/replace-solar-generation")
async def replace_solar_generation(dataset_id: dataset_id_t, data: UploadFile, pool: DatabasePoolDep) -> RenewablesMetadata:
    """
    Replace a solar generation dataset in the database.

    Provide the dataset_id of the old dataset that you want to replace, and upload a file which should be a CSV
    with columns "start_ts", "end_ts" and "data", where the timestamps are in ISO-8601 format and "data" should be
    fraction of peak generation at that timestamp.

    Parameters
    ----------
    dataset_id
        ID of the old dataset you wish to replace
    data
         CSV with columns "start_ts", "end_ts" and "data", where the timestamps are in ISO-8601 format and "data" should be
    fraction of peak generation at that timestamp.

    Returns
    -------
    RenewablesMetadata
        Information about the new dataset you've uploaded.
    """
    old_metadata = await pool.fetchrow(
        """SELECT site_id, renewables_location_id FROM renewables.metadata WHERE dataset_id = $1 LIMIT 1"""
    )
    if old_metadata is None:
        raise HTTPException(404, f"Couldn't find a solar dataset with ID {dataset_id} to replace.")
    site_id, renewables_location_id = old_metadata

    provided_df = pd.read_csv(
        data.file,
        names=["start_ts", "end_ts", "data"],
        header=0,
        parse_dates=["start_ts", "end_ts"],
        nrows=17521,
        date_format="ISO8601",
    )

    if len(provided_df) < 17520:
        raise HTTPException(400, f"Got {len(provided_df)} rows instead of expected 17520.")
    if provided_df.isna().any().any():
        raise HTTPException(400, "Got NA in replacement data.")
    if (provided_df["data"] < 0).any():
        raise HTTPException(400, "Got negative entries in the replacement. data, must all be >0.")
    if (provided_df["data"] > 1.0).any():
        raise HTTPException(400, "Got entries with value >1 in the replacement data, must all be normalised.")

    metadata = RenewablesMetadata(
        dataset_id=uuid7(),
        site_id=site_id,
        data_source=data.filename if data.filename is not None else "custom",
        created_at=datetime.datetime.now(datetime.UTC),
        parameters=None,
        renewables_location_id=renewables_location_id,
    )
    async with pool.acquire() as conn, conn.transaction():
        await conn.execute(
            """INSERT INTO
                    renewables.metadata (
                        dataset_id,
                        site_id,
                        created_at,
                        data_source,
                        parameters,
                        renewables_location_id
            ) VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5,
                        $6)""",
            metadata.dataset_id,
            metadata.site_id,
            metadata.created_at,
            metadata.data_source,
            None,  # We deliberately don't add the parameters as we don't know them.
            metadata.renewables_location_id,
        )

        await conn.copy_records_to_table(
            schema_name="renewables",
            table_name="solar_pv",
            columns=["dataset_id", "start_ts", "end_ts", "solar_generation"],
            records=zip(
                repeat(metadata.dataset_id, len(provided_df)),
                provided_df.start_ts,
                provided_df.end_ts,
                provided_df.data,
                strict=True,
            ),
        )
        # Replace this entry in the bundle with
        # the new dataset
        await conn.execute(
            """UPDATE data_bundles.dataset_links SET dataset_id = $1 WHERE dataset_id = $2""", dataset_id, metadata.dataset_id
        )
    return metadata


@router.route("/replace-import-tariff")
async def replace_import_tariff(dataset_id: dataset_id_t, data: UploadFile, pool: DatabasePoolDep) -> TariffMetadata:
    """
    Replace a solar generation dataset in the database.

    Provide the dataset_id of the old dataset that you want to replace, and upload a file which should be a CSV
    with columns "start_ts", "end_ts" and "data", where the timestamps are in ISO-8601 format and "data" should be
    costs in pence per kWh.

    Parameters
    ----------
    dataset_id
        ID of the old dataset you wish to replace
    data
         CSV with columns "start_ts", "end_ts" and "data", where the timestamps are in ISO-8601 format and "data" should be
    fraction of peak generation at that timestamp.

    Returns
    -------
    TariffMetadata
        Information about the new dataset you've uploaded.
    """
    site_id = await pool.fetchval("""SELECT site_id FROM import_tariffs.metadata WHERE dataset_id = $1 LIMIT 1""")
    if site_id is None:
        raise HTTPException(404, f"Couldn't find an import tariff dataset with ID {dataset_id} to replace.")

    price_df = pd.read_csv(
        data.file,
        names=["start_ts", "end_ts", "data"],
        header=0,
        parse_dates=["start_ts", "end_ts"],
        nrows=17521,
        date_format="ISO8601",
    )

    if len(price_df) < 17520:
        raise HTTPException(400, f"Got {len(price_df)} rows instead of expected 17520.")
    if price_df.isna().any().any():
        raise HTTPException(400, "Got NA in replacement data.")

    metadata = TariffMetadata(
        dataset_id=uuid7(),
        site_id=site_id,
        created_at=datetime.datetime.now(datetime.UTC),
        provider=TariffProviderEnum.Synthetic,
        product_name=data.filename if data.filename is not None else "custom",
        tariff_name=data.filename if data.filename is not None else "custom",
        # Just pick some data from there to make it look reasonable.
        day_cost=max(price_df["data"].mode()),
        night_cost=price_df["data"].min(),
        peak_cost=price_df["data"].max(),
        valid_from=None,
        valid_to=None,
    )

    # Note that it doesn't matter that we've got "too  much" tariff data here, as we'll sort it out when we get it.
    async with pool.acquire() as conn, conn.transaction():
        # We insert the dataset ID into metadata, but we must wait to validate the
        # actual data insert until the end
        await conn.execute("SET CONSTRAINTS tariffs.electricity_dataset_id_metadata_fkey DEFERRED;")
        await conn.execute(
            """
                INSERT INTO
                    tariffs.metadata (
                        dataset_id,
                        site_id,
                        created_at,
                        provider,
                        product_name,
                        tariff_name,
                        valid_from,
                        valid_to)
                VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5,
                        $6,
                        $7,
                        $8)""",
            metadata.dataset_id,
            metadata.site_id,
            metadata.created_at,
            metadata.provider,
            metadata.product_name,
            metadata.tariff_name,
            metadata.valid_from,
            metadata.valid_to,
        )

        await conn.copy_records_to_table(
            table_name="electricity",
            schema_name="tariffs",
            records=zip(
                repeat(metadata.dataset_id, len(price_df)),
                price_df["start_ts"],
                price_df["end_ts"],
                price_df["cost"],
                strict=True,
            ),
            columns=["dataset_id", "start_ts", "end_ts", "unit_cost"],
        )
        # Replace this entry in the bundle with
        # the new dataset
        await conn.execute(
            """UPDATE data_bundles.dataset_links SET dataset_id = $1 WHERE dataset_id = $2""", dataset_id, metadata.dataset_id
        )
    return metadata


@router.route("/replace-electricity-load")
async def replace_electricity_load(dataset_id: dataset_id_t, data: UploadFile, pool: DatabasePoolDep) -> ElectricalLoadMetadata:
    """
    Replace an electrical load dataset in the database.

    Provide the dataset_id of the old dataset that you want to replace, and upload a file which should be a CSV
    with columns "start_ts", "end_ts" and "data", where the timestamps are in ISO-8601 format and "data" should be
    costs in pence per kWh.

    Parameters
    ----------
    dataset_id
        ID of the old dataset you wish to replace
    data
         CSV with columns "start_ts", "end_ts" and "consumption_kwh", where the timestamps are in ISO-8601 format and
         "consumption_kwh" should be the electrical demand during that half hour.

    Returns
    -------
    ElectricalLoadMetadata
        Information about the new dataset you've uploaded.
    """
    site_id = await pool.fetchval("""SELECT site_id FROM client_meters.metadata WHERE dataset_id = $1 LIMIT 1""")
    if site_id is None:
        raise HTTPException(404, f"Couldn't find an import tariff dataset with ID {dataset_id} to replace.")

    synthetic_hh_df = pd.read_csv(
        data.file,
        names=["start_ts", "end_ts", "consumption_kwh"],
        header=0,
        parse_dates=["start_ts", "end_ts"],
        nrows=17521,
        date_format="ISO8601",
    )

    if len(synthetic_hh_df) < 17520:
        raise HTTPException(400, f"Got {len(synthetic_hh_df)} rows instead of expected 17520.")
    if synthetic_hh_df.isna().any().any():
        raise HTTPException(400, "Got NA in replacement data.")

    metadata = ElectricalLoadMetadata(
        dataset_id=uuid7(),
        created_at=datetime.datetime.now(tz=datetime.UTC),
        site_id=site_id,
        fuel_type=FuelEnum.elec,
        reading_type=ReadingTypeEnum.HalfHourly,
        filename=data.filename,
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
                repeat(metadata.dataset_id, len(synthetic_hh_df)),
                synthetic_hh_df["start_ts"],
                synthetic_hh_df["end_ts"],
                synthetic_hh_df["consumption_kwh"],
                strict=True,
            ),
            columns=["dataset_id", "start_ts", "end_ts", "consumption_kwh"],
        )
        # Replace this entry in the bundle with
        # the new dataset
        await conn.execute(
            """UPDATE data_bundles.dataset_links SET dataset_id = $1 WHERE dataset_id = $2""", dataset_id, metadata.dataset_id
        )
    return metadata


@router.route("/replace-heat-load")
async def replace_heat_load(
    dataset_id: dataset_id_t,
    data: UploadFile,
    pool: DatabasePoolDep,
    fabric_cost_breakdown: list[FabricCostBreakdown] | None = None,
) -> HeatingLoadMetadata:
    """
    Replace an heat load dataset in the database.

    Provide the dataset_id of the old dataset that you want to replace, and upload a file which should be a CSV
    with columns "start_ts", "end_ts" and "data", where the timestamps are in ISO-8601 format and "data" should be
    costs in pence per kWh.

    Parameters
    ----------
    dataset_id
        ID of the old dataset you wish to replace
    data
        CSV with columns "start_ts", "end_ts", "heating", "dhw" and "air_temperature":
            the timestamps are in ISO-8601 format
            "heating" should be the heat demand in kWh during that half hour,
            "dhw" should be the domestic hot water demand in kWh during that half hour,
            "air_temperature" should be the mean air temperatures during that half hour in Celsius.

    Returns
    -------
    HeatingLoadMetadata
        Information about the new dataset you've uploaded.
    """
    site_id = await pool.fetchval("""SELECT site_id FROM client_meters.metadata WHERE dataset_id = $1 LIMIT 1""")
    if site_id is None:
        raise HTTPException(404, f"Couldn't find a heat load dataset with ID {dataset_id} to replace.")

    heating_df = pd.read_csv(
        data.file,
        names=["start_ts", "end_ts", "heating", "dhw", "air_temperature"],
        header=0,
        parse_dates=["start_ts", "end_ts"],
        nrows=17521,
        date_format="ISO8601",
    )

    if len(heating_df) < 17520:
        raise HTTPException(400, f"Got {len(heating_df)} rows instead of expected 17520.")
    if heating_df.isna().any().any():
        raise HTTPException(400, "Got NA in replacement data.")

    metadata = HeatingLoadMetadata(
        dataset_id=uuid7(),
        site_id=site_id,
        created_at=datetime.datetime.now(datetime.UTC),
        params=None,
        interventions=[],
        generation_method=HeatingLoadModelEnum.Regression,
    )

    async with pool.acquire() as conn, conn.transaction():
        await conn.execute(
            """
            INSERT INTO
                heating.metadata (
                    dataset_id,
                    site_id,
                    created_at,
                    params,
                    interventions,
                    fabric_cost_total,
                    fabric_cost_breakdown
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            metadata.dataset_id,
            metadata.site_id,
            metadata.created_at,
            None,
            metadata.interventions,
            sum(item.cost for item in fabric_cost_breakdown) if fabric_cost_breakdown else None,
            json.dumps([item.model_dump(mode="json") for item in fabric_cost_breakdown]) if fabric_cost_breakdown else None,
        )

        await conn.copy_records_to_table(
            schema_name="heating",
            table_name="synthesised",
            columns=["dataset_id", "start_ts", "end_ts", "heating", "dhw", "air_temperature"],
            records=zip(
                repeat(metadata.dataset_id, len(heating_df)),
                heating_df["start_ts"],
                heating_df["end_ts"],
                heating_df["heating"],
                heating_df["dhw"],
                heating_df["air_temperature"],
                strict=True,
            ),
        )
        # Replace this entry in the bundle with the new dataset
        await conn.execute(
            """UPDATE data_bundles.dataset_links SET dataset_id = $1 WHERE dataset_id = $2""", dataset_id, metadata.dataset_id
        )
    return metadata


@router.route("/replace-dataset")
async def replace_dataset(
    dataset_id: dataset_id_t,
    data: UploadFile,
    pool: DatabasePoolDep,
    fabric_cost_breakdown: list[FabricCostBreakdown] | None = None,
) -> RenewablesMetadata | TariffMetadata | ElectricalLoadMetadata | HeatingLoadMetadata:
    """
    Replace a dataset in the database by ID.

    This will take a dataset_id and a file of new data, identify which old dataset you want to replace, and upload
    the new data.
    This will re-write the bundle, so might change old results: be careful when doing so, and you might want to generate
    a new bundle before replacing any of the data.
    We'll identify what sort of dataset you want to replace, and try to generate sensible metadata as much as possible.
    This isn't always feasible, so the generated metadata may be wrong.

    Heat loads, domestic hot water and air temperatures are stored all together.
    If you want to replace a DHW time series or air temperature time series, then you should instead replace the
    "baseline" heat load time series which is the dataset ID at index 0.

    Parameters
    ----------
    dataset_id
        ID of the dataset you want to replace; this ID will be orphaned and we'll attach your new dataset to the
        bundle that this one was previously attached to.
    data
        A file containing data to put in to a new dataset.
        This has to be clean halfhourly data, generally with columns "start_ts", "end_ts" and at least one data column.
        See the relevant sub-functions for more documentation about what each one expects.
    pool
        Connection pool to the database we want to write to.
    fabric_cost_breakdown
        If you're replacing a heat load, enter a cost breakdown in the form [{"cost": ..., "area":..., "name":...}]
        here. Otherwise, you can leave this blank

    Returns
    -------
    RenewablesMetadata | TariffMetadata | ElectricalLoadMetadata | HeatingLoadMetadata
        Metadata about the new dataset we've written to the database.
    """
    dataset_type = await pool.fetchval("""SELECT dataset_type FROM data_bundles.dataset_links WHERE dataset_id = $1 LIMIT 1""")
    if dataset_type is None:
        raise HTTPException(400, f"Couldn't find a dataset with id {dataset_id} to replace.")
    try:
        dataset_type = DatasetTypeEnum(dataset_type)
    except ValueError as ex:
        raise HTTPException(400, f"Bad dataset type for {dataset_id} in database: {dataset_type}.") from ex

    match dataset_type:
        case DatasetTypeEnum.HeatingLoad:
            return await replace_heat_load(dataset_id, data, pool, fabric_cost_breakdown)
        case DatasetTypeEnum.ElectricityMeterDataSynthesised:
            return await replace_electricity_load(dataset_id, data, pool)
        case DatasetTypeEnum.ImportTariff:
            return await replace_import_tariff(dataset_id, data, pool)
        case DatasetTypeEnum.RenewablesGeneration:
            return await replace_solar_generation(dataset_id, data, pool)
        case _:
            raise HTTPException(400, f"Can't replace a dataset of type {dataset_type}.")
