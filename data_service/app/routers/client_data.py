import logging

import asyncpg
from fastapi import APIRouter, HTTPException, Request

from ..internal.pvgis import get_pvgis_optima
from .models import (
    ClientData,
    ClientID,
    ClientIdNamePair,
    DatasetEntry,
    SiteData,
    SiteID,
    SiteIdNamePair,
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

    logging.info(f"Returning {len(res)} datasets for {site_id}")
    return [
        DatasetEntry(
            dataset_id=item["dataset_id"],
            fuel_type=item["fuel_type"],
            reading_type=item["reading_type"]) for item in res
    ]


@router.post("/get-location")
async def get_location(request: Request, site_id: SiteID) -> location_t:
    """
    Get the location name for this site.

    Parameters

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
