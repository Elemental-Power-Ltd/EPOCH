import datetime
import uuid

import httpx
import pandas as pd
from fastapi import APIRouter, Request

from ..internal.utils import hour_of_year
from ..models.core import DatasetIDWithTime
from ..models.import_tariffs import EpochTariffEntry, TariffMetadata, TariffRequest

router = APIRouter()


@router.post("/generate-import-tariffs", tags=["generate", "tariff"])
async def generate_import_tariffs(request: Request, params: TariffRequest) -> TariffMetadata:
    """
    Generate a set of import tariffs, initially from Octopus.

    This gets hourly import costs for a specific Octopus tariff.
    For consistent tariffs, this will be the same price at every timestamp.
    For agile or time-of-use tariffs this will vary.

    Parameters
    ----------
    *request*
        FastAPI request object, not necessary for external callers.
    *params*
        with attributes `tariff_name`, `start_ts`, and `end_ts`

    Returns
    -------
    *tariff_metadata*
        Some useful metadata about the tariff entry in the database
    """
    BASE_URL = "https://api.octopus.energy/v1/products"
    dataset_id = uuid.uuid4()
    url = f"{BASE_URL}/{params.tariff_name}/"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        products = response.json()
        tariff_codes = sorted([
            region["direct_debit_monthly"]["code"] for region in products["single_register_electricity_tariffs"].values()
        ])
        tariff_code = tariff_codes[0]  # for the moment just take the first

        price_url = url + f"electricity-tariffs/{tariff_code}/standard-unit-rates/"

        start_ts = datetime.datetime(year=2024, month=5, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2024, month=6, day=1, tzinfo=datetime.UTC)
        price_response = await client.get(
            price_url,
            params={
                "period_from": start_ts.isoformat(),
                "period_to": end_ts.isoformat(),
            },
        )

        price_data = price_response.json()
        price_records = list(price_data["results"])
        requests_made = 0
        while price_data.get("next") is not None:
            requests_made += 1
            price_response = await client.get(price_data["next"])
            price_data = price_response.json()
            price_records.extend(price_data["results"])

    price_df = pd.DataFrame.from_records(price_records)
    if "payment_method" in price_df:
        price_df = price_df.drop(columns=["payment_method"])
    price_df["valid_from"] = pd.to_datetime(price_df["valid_from"], utc=True, format="ISO8601")
    price_df["valid_to"] = pd.to_datetime(price_df["valid_to"], utc=True, format="ISO8601")
    price_df = price_df.set_index("valid_from").sort_index().resample(pd.Timedelta(hours=1)).max().ffill()

    price_df = price_df[["value_exc_vat"]].rename(columns={"value_exc_vat": "price", "valid_from": "start_ts"})
    price_df["start_ts"] = price_df.index
    price_df["dataset_id"] = dataset_id
    async with request.state.pgpool.acquire() as conn:
        async with conn.transaction():
            metadata = {
                "dataset_id": dataset_id,
                "site_id": params.site_id,
                "created_at": datetime.datetime.now(datetime.UTC),
                "provider": "octopus",
                "product_name": params.tariff_name,
                "tariff_name": tariff_code,
                "valid_from": products.get("available_from"),
                "valid_to": products.get("available_to") if products.get("available_to") != "null" else None,
            }
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
                metadata["dataset_id"],
                metadata["site_id"],
                metadata["created_at"],
                metadata["provider"],
                metadata["product_name"],
                metadata["tariff_name"],
                pd.to_datetime(metadata["valid_from"], utc=True, format="ISO8601"),
                metadata["valid_to"],
            )

            await conn.executemany(
                """INSERT INTO
                tariffs.electricity (
                    dataset_id,
                    timestamp,
                    unit_cost,
                    flat_cost
                )
                VALUES (
                        $1,
                        $2,
                        $3,
                        $4)""",
                zip(
                    price_df["dataset_id"],
                    price_df["start_ts"],
                    price_df["price"],
                    [None for _ in range(len(price_df.index))],
                    strict=True,
                ),
            )
    return TariffMetadata(**metadata)


@router.post("/get-import-tariffs", tags=["get", "tariff"])
async def get_import_tariffs(request: Request, params: DatasetIDWithTime) -> list[EpochTariffEntry]:
    """
    Get the electricity import tariffs in p / kWh for this dataset.

    You can create tariffs with the `generate-import-tariffs` endpoint.
    These are currently just Octopus time-of-use tariffs.

    It always returns 30 minute tariff intervals, regardless of the original source data.
    Tariffs will be forward-filled if they were originally sparser.

    Parameters
    ----------
    *request*
        Internal FastAPI request object
    *params*
        The ID of the dataset you want, and the timestamps (usually the year) you want it for.

    Returns
    -------
    *epoch_tariff_entries*
        Tariff entries in an EPOCH friendly format, with HourOfYear and Date splits.
    """
    async with request.state.pgpool.acquire() as conn:
        # TODO (2024-08-02 MHJB): put start_ts/end_ts params here
        res = await conn.fetch(
            """
            SELECT
                timestamp,
                unit_cost
            FROM tariffs.electricity
            WHERE dataset_id = $1
            AND $2 <= timestamp
            AND timestamp < $3
            ORDER BY timestamp ASC""",
            params.dataset_id,
            params.start_ts,
            params.end_ts,
        )
    df = pd.DataFrame.from_records(res, index="timestamp", columns=["timestamp", "unit_cost"])
    df.index = pd.to_datetime(df.index)
    df = df.resample(pd.Timedelta(minutes=30)).max().ffill()
    return [
        EpochTariffEntry(Date=ts.strftime("%d-%b"), HourOfYear=hour_of_year(ts), StartTime=ts.strftime("%H:"), Tariff=val)
        for ts, val in zip(df.index, df["unit_cost"], strict=True)
    ]
