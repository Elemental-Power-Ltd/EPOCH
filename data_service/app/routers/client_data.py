"""
Client data and database manipulation endpoints.

Endpoints in here generally add or list clients, sites, or their datasets.
The structure is that clients are the top level, each client has zero or more sites, and each
site has zero or more datasets of different kinds.
"""

import logging

import asyncpg
from fastapi import APIRouter, HTTPException

from ..dependencies import DatabaseDep
from ..models.core import (
    ClientData,
    ClientID,
    ClientIdNamePair,
    DatasetEntry,
    DatasetTypeEnum,
    SiteData,
    SiteID,
    SiteIdNamePair,
    client_id_t,
    location_t,
    site_id_t,
)

router = APIRouter()


@router.post("/add-client", tags=["db", "add"])
async def add_client(client_data: ClientData, conn: DatabaseDep) -> tuple[ClientData, str]:
    """
    Add a new client into the database.

    Clients are the top level of organisation, and each client has a set of "sites" underneath it.
    Each client has a human readable name and an internal database ID.
    You get to choose the database ID, but please pick something easily memorable from the name, all in lowercase
    and joined by underscores.

    This will reject duplicate clients with an error.

    Parameters
    ----------
    *client_data*
        Metadata about the client, currently a client_id and name pair.

    Returns
    -------
    client_data, status
        Original client data and Postgres response.
    """
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


@router.post("/add-site", tags=["db", "add"])
async def add_site(site_data: SiteData, conn: DatabaseDep) -> tuple[SiteData, str]:
    """
    Add a new site into the database.

    Sites are one level below clients, e.g. the `demo` client will have `demo_london` and `demo_cardiff`
    as two sites.
    Each site has a name, a location (roughly the nearest town), latitude and longitude coordinates, and a street address.
    Please make sure the street address contains a postcode.

    You get to pick a unique site_id for this site. Please pick one that is easily memorable from the name, and
    is lowercase joined by underscores. If there's a clash with another site with a similar name, you could prefix
    with the client ID. This function will return an error if the site id already exists.

    You are responsible for ensuring that the relevant client is already in the database.

    Parameters
    ----------
    request
        Internal FastAPI request object
    site_data
        Metadata about the site, including client_id, site_id, name, location, coordinates and address.

    Returns
    -------
        Data you inserted and postgres response string.
    """
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
        raise HTTPException(400, f"No such client `{site_data.client_id}` exists in the database. Please create one.") from ex
    return (site_data, status)


@router.post("/list-clients", tags=["db", "list"])
async def list_clients(conn: DatabaseDep) -> list[ClientIdNamePair]:
    """
    Get a list of all the clients we have, and their human readable names.

    Generally you should query this and display the `name` field, and keep the `client_id` field for your next queries.

    Parameters
    ----------
    *conn*

    Returns
    -------
    list of (client_id, name) pairs, where `client_id` is the DB foreign key and `name` is human readable.
    """
    res = await conn.fetch("""
        SELECT DISTINCT
            client_id,
            name
        FROM client_info.clients""")
    return [ClientIdNamePair(client_id=client_id_t(item[0]), name=str(item[1])) for item in res]


@router.post("/list-sites", tags=["db", "list"])
async def list_sites(client_id: ClientID, conn: DatabaseDep) -> list[SiteIdNamePair]:
    """
    Get all the sites associated with a particular client, including their human readable names.

    Parameters
    ----------
    *client_id*
        Database ID of this specific client.

    Returns
    -------
    list of (site_id, name) pairs where `site_id` is the database foreign key and `name` is human readable.
    """
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
    return [SiteIdNamePair(site_id=site_id_t(item[0]), name=str(item[1])) for item in res]


@router.post("/get-location", tags=["db"])
async def get_location(site_id: SiteID, conn: DatabaseDep) -> location_t:
    """
    Get the location name for this site.

    Location names are generally the closest town that we can look up weather for.

    Parameters
    ----------
    request

    site_id
        Database ID of the site you are interested in.

    Returns
    -------
    location
        Name of the location e.g. "Worksop", "Retford", "Cardiff"
    """
    location = await conn.fetchval(
        """SELECT location FROM client_info.site_info WHERE site_id = $1""",
        site_id.site_id,
    )
    if location is None:
        raise HTTPException(400, f"Site ID `{site_id.site_id}` has no location in the database.")
    return location
