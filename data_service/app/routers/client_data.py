import datetime
import logging
import uuid

import asyncpg
import httpx
import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from ..internal.pvgis import get_pvgis_optima
from .models import (
    ClientData,
    ClientID,
    ClientIdNamePair,
    DatasetEntry,
    FuelEnum,
    ReadingTypeEnum,
    SiteData,
    SiteID,
    SiteIdNamePair,
    TariffRequest,
    client_id_t,
    location_t,
    site_id_t,
)

router = APIRouter()


@router.post("/add-client")
async def add_client(request: Request, client_data: ClientData) -> tuple[ClientData, str]:
    async with request.state.pgpool.acquire() as conn:
        try:
            status = await conn.execute(
                """
                INSERT INTO client_info.clients (
                    client_id,
                    name)
                VALUES ($1, $2)""",
                client_data.client_id,
                client_data.name,
            )
        except asyncpg.exceptions.UniqueViolationError as ex:
            raise HTTPException(400, f"Client ID {client_data.client_id} already exists in the database.") from ex
        logging.info(f"Inserted client {client_data.client_id} with return status {status}")
    return (client_data, status)


@router.post("/add-site")
async def add_site(request: Request, site_data: SiteData) -> tuple[SiteData, str]:
    async with request.state.pgpool.acquire() as conn:
        try:
            status = await conn.execute(
                """
                INSERT INTO
                    client_info.site_info (
                    client_id,
                    site_id,
                    name,
                    location,
                    coordinates,
                    address)
                VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6)""",
                site_data.client_id,
                site_data.site_id,
                site_data.name,
                site_data.location,
                site_data.coordinates,
                site_data.address,
            )
            logging.info(f"Inserted client {site_data.client_id} with return status {status}")
        except asyncpg.exceptions.UniqueViolationError as ex:
            raise HTTPException(400, f"Site ID `{site_data.site_id}` already exists in the database.") from ex
        except asyncpg.exceptions.ForeignKeyViolationError as ex:
            raise HTTPException(
                400, f"No such client `{site_data.client_id}` exists in the database. Please create one."
            ) from ex
    return (site_data, status)


@router.post("/get-clients", response_model=list[ClientIdNamePair])
async def get_clients(request: Request) -> list[dict[str, str | client_id_t]]:
    """
    Get a list of all the clients we have, and their human readable names.

    Generally you should query this and display the `name` field, and keep the `client_id` field for your next queries.

    Parameters
    ----------
    *request*

    Returns
    -------
    list of (client_id, name) pairs, where `client_id` is the DB foreign key and `name` is human readable.
    """
    async with request.state.pgpool.acquire() as conn:
        res = await conn.fetch("""
            SELECT DISTINCT
                client_id,
                name
            FROM client_info.clients""")
    return [{"client_id": client_id_t(item[0]), "name": str(item[1])} for item in res]


@router.post("/get-sites", response_model=list[SiteIdNamePair])
async def get_sites(request: Request, client_id: ClientID) -> list[dict[str, str | site_id_t]]:
    """
    Get all the sites associated with a particular client, including their human readable names.

    Parameters
    ----------
    *request*

    *client_id*
        Database ID of this specific client.

    Returns
    -------
    list of (site_id, name) pairs where `site_id` is the database foreign key and `name` is human readable.
    """
    async with request.state.pgpool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT DISTINCT
                site_id,
                name
            FROM client_info.site_info
            WHERE client_id = $1
            ORDER BY site_id ASC""",
            client_id.client_id,
        )
    return [{"site_id": site_id_t(item[0]), "name": str(item[1])} for item in res]


@router.post("/get-datasets")
async def get_datasets(request: Request, site_id: SiteID) -> list[DatasetEntry]:
    """
    Get all the datasets associated with a particular site, in the form of a list of UUID strings.

    Parameters
    ----------
    *request*

    *site_id*

    Returns
    -------
    A list of UUID dataset strings, with the earliest at the start and the latest at the end.
    """
    datasets = []
    async with request.state.pgpool.acquire() as conn:
        res = await conn.fetch(
            """
            SELECT
                dataset_id,
                fuel_type,
                reading_type
            FROM
                client_meters.metadata
            WHERE site_id = $1
            ORDER BY created_at ASC""",
            site_id.site_id,
        )
        datasets.extend(
            [
                DatasetEntry(dataset_id=item["dataset_id"], fuel_type=item["fuel_type"], reading_type=item["reading_type"])
                for item in res
            ]
        )

        res = await conn.fetch(
            """
            SELECT
                dataset_id
            FROM
                tariffs.metadata
            WHERE site_id = $1
            ORDER BY created_at ASC""",
            site_id.site_id,
        )
        datasets.extend(
            [
                DatasetEntry(dataset_id=item["dataset_id"], fuel_type=FuelEnum.elec, reading_type=ReadingTypeEnum.tariff)
                for item in res
            ]
        )

        res = await conn.fetch(
            """
            SELECT
                dataset_id
            FROM
                renewables.metadata
            WHERE site_id = $1
            ORDER BY created_at ASC""",
            site_id.site_id,
        )
        datasets.extend(
            [
                DatasetEntry(dataset_id=item["dataset_id"], fuel_type=FuelEnum.elec, reading_type=ReadingTypeEnum.solar_pv)
                for item in res
            ]
        )
    logging.info(f"Returning {len(res)} datasets for {site_id}")
    return datasets


@router.post("/get-location")
async def get_location(request: Request, site_id: SiteID) -> location_t:
    """
    Get the location name for this site.

    Location names are generally the closest town that we can look up weather for.

    Parameters
    ----------
    request

    site_id

    Returns
    -------
    location
        Name of the location e.g. "Worksop", "Retford", "Cardiff"
    """
    async with request.state.pgpool.acquire() as conn:
        location = await conn.fetchval(
            """SELECT location FROM client_info.site_info WHERE site_id = $1""",
            site_id.site_id,
        )
    return location


@router.post("/get-pv-optima")
async def get_pv_optima(request: Request, site_id: SiteID) -> dict[str, float | int | str]:
    """
    Get some optimal angles and azimuths for this specific site.

    Parameters
    ----------
    request

    site_id

    Returns
    -------
    information about the optimal azimuth, tilt, and some metadata about the technologies used.
    """
    async with request.state.pgpool.acquire() as conn:
        latitude, longitude = await conn.fetchval(
            """SELECT coordinates FROM client_info.site_info WHERE site_id = $1""",
            site_id.site_id,
        )
    optima = await get_pvgis_optima(latitude=latitude, longitude=longitude)
    return optima


@router.post("/generate-import-tariffs")
async def generate_import_tariffs(
    request: Request, params: TariffRequest
) -> dict[str, float | int | str | datetime.datetime | None]:
    """
    Generate a set of import tariffs, initially from Octopus.

    This gets hourly import costs for a specific Octopus tariff.
    For consistent tariffs, this will be the same price at every timestamp.
    For agile or time-of-use tariffs this will vary.

    Parameters
    ----------
    request

    params
        with attributes `tariff_name`, `start_ts`, and `end_ts`

    Returns
    -------
        Some useful metadata about the tariff entry in the database
    """
    BASE_URL = "https://api.octopus.energy/v1/products"
    dataset_id = uuid.uuid4()
    url = f"{BASE_URL}/{params.tariff_name}/"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        products = response.json()
        tariff_codes = sorted(
            [region["direct_debit_monthly"]["code"] for region in products["single_register_electricity_tariffs"].values()]
        )
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
                    strict=False,
                ),
            )
    return metadata
