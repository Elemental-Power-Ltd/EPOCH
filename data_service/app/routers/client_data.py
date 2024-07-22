
import pydantic
from fastapi import APIRouter, Request

from .models import ClientID, SiteID, client_id_t, dataset_id_t, location_t, site_id_t

router = APIRouter()


class ClientIdNamePair(pydantic.BaseModel):
    """
    A client_id, name pair.
    """
    client_id: client_id_t
    name: str


class SiteIdNamePair(pydantic.BaseModel):
    site_id: site_id_t
    name: str


@router.post("/get-clients")
async def get_clients(request: Request) -> list[ClientIdNamePair]:
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
        res = await conn.fetch(
            """SELECT DISTINCT
                client_id,
                name
                FROM client_info.clients
                """
        )
    return [{"client_id": item[0], "name": item[1]} for item in res]


@router.post("/get-sites")
async def get_sites(request: Request, client_id: ClientID) -> list[SiteIdNamePair]:
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
            """SELECT DISTINCT
                site_id,
                name
                FROM client_info.site_info
                WHERE client_id = $1
                ORDER BY site_id ASC
                """,
            client_id.client_id,
        )
    return [{"site_id": item[0], "name": item[1]} for item in res]


@router.post("/get-datasets")
async def get_datasets(request: Request, site_id: SiteID) -> list[dataset_id_t]:
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
            """SELECT dataset_id FROM client_meters.metadata WHERE site_id = $1 ORDER BY created_at ASC""",
            site_id.site_id,
        )

    return list(res)


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
