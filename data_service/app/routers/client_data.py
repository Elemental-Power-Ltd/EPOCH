"""
Client data and database manipulation endpoints.

Endpoints in here generally add or list clients, sites, or their datasets.
The structure is that clients are the top level, each client has zero or more sites, and each
site has zero or more datasets of different kinds.
"""

import json
import typing
import uuid
from logging import getLogger

import asyncpg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pydantic_core._pydantic_core import ValidationError

from ..dependencies import DatabaseDep, DatabasePoolDep
from ..models.core import (
    ClientData,
    ClientID,
    ClientIdNamePair,
    DatasetID,
    SiteData,
    SiteID,
    SiteIdNamePair,
    client_id_t,
    location_t,
    site_id_t,
)
from ..models.epoch_types.task_data_type import Building, Config, GasHeater, Grid, TaskData

router = APIRouter()

logger = getLogger(__name__)


@router.post("/add-site-baseline", tags=["db", "baseline", "site"])
async def add_baseline(site_id: SiteID, baseline: TaskData, pool: DatabasePoolDep) -> None:
    """
    Add the baseline configuration for a site in the database.

    The baseline contains all the infrastructure that is already there:
    by default, this is just a Building, a Grid and a Gas heater.
    However, for some sites this will also include heat pumps or solar arrays.

    This will override previous baselines that are stored in the database, as we only ever fetch the latest.
    Baselines are given a UUID when generated that you can use for a task_config object later on.

    Parameters
    ----------
    site_id
        The database ID of the site you want to get the baseline configuration for.
    baseline
        The configuration of the current elements you wish to insert, stored as a TaskData.
    pool
        Connection pool to the database storing the baseline configurations.

    Returns
    -------
    None
    """
    try:
        await pool.execute(
            """
            INSERT INTO client_info.site_baselines (baseline_id, site_id, baseline) VALUES ($1, $2, $3)""",
            uuid.uuid4(),
            site_id.site_id,
            baseline.model_dump_json(),
        )
    except asyncpg.exceptions.ForeignKeyViolationError as ex:
        raise HTTPException(400, f"Site {site_id.site_id} not found in the database.") from ex


async def get_default_baseline() -> TaskData:
    """
    Provide a default baseline for sites where there is no baseline in the database.

    Returns
    -------
        A default baseline
    """
    return TaskData(
        building=Building(incumbent=True),
        grid=Grid(grid_import=1e3, grid_export=1e3, incumbent=True),
        gas_heater=GasHeater(maximum_output=1e3, incumbent=True),  # this is unusually large to meet all the heat demand.
        config=Config(),
    )


@router.post("/get-site-baseline", tags=["db", "baseline", "get"])
async def get_baseline(site_or_dataset_id: SiteID | DatasetID, pool: DatabasePoolDep) -> TaskData:
    """
    Get the baseline configuration for a site in the database.

    The baseline contains all the infrastructure that is already there:
    by default, this is just a Building, a Grid and a Gas heater.
    However, for some sites this will also include heat pumps or solar arrays.
    This will fetch the most recent baseline that is stored in the database.

    Where keys are necessary but were not stored in the database, this will fill in with the relevant default
    from TaskData (e.g. if you do not provide a grid_import when storing the baseline, you'll get the default grid_import out.)

    Parameters
    ----------
    site_or_dataset_id
        One of either:
            the database ID of the site you want to get the baseline configuration for.
            the database ID of the specific configuration you want to get.
    pool
        Connection pool to the database storing the baseline configurations.

    Returns
    -------
    TaskData
        Single-scenario task data representing the baseline configuration of what infrastructure is already at the site.
    """
    DEFAULT_CONFIG = await get_default_baseline()

    async def get_baseline_from_site_id(site_id: SiteID) -> asyncpg.Record | None:
        """
        Get the baseline scenario from a Site ID.

        This will select the most recent scenario, or None if there isn't one.
        It'll raise an error if the specified site isn't valid.

        Parameters
        ----------
        site_id
            Database ID of the site you want to get

        Returns
        -------
        Jsonable | None
            Raw baseline scenario JSON for later processing, or None if there's nothing there.
        """
        # We want to error differently if this site doesn't exist, as opposed to checking the baseline for a real site and
        # getting the default.
        is_valid_site = await pool.fetchval(
            """
            SELECT exists (
                SELECT 1 FROM client_info.site_info WHERE site_id = $1 LIMIT 1
            )""",
            site_id.site_id,
        )
        if not is_valid_site:
            raise HTTPException(400, f"Site {site_id.site_id} not found in the database.")

        # We only want the most recent baseline config, so select them ordered by their created_at timestamps.
        # The rest are stored only for historical interest, or for different EPOCH versions.
        baseline_rec = await pool.fetchrow(
            """
            SELECT
                baseline
            FROM
                client_info.site_baselines
            WHERE site_id = $1
            ORDER BY created_at DESC LIMIT 1""",
            site_id.site_id,
        )
        return baseline_rec

    async def get_baseline_from_dataset_id(dataset_id: DatasetID) -> asyncpg.Record | None:
        """
        Get the baseline scenario from a Dataset ID.

        This will select a single scenario corresponding to that dataset ID, or error if it doesn't exist.

        Parameters
        ----------
        dataset_id
            Database ID of the scenario you want to get

        Returns
        -------
        Jsonable | None
            Raw baseline scenario JSON for later processing, or None if there's nothing there.

        Raises
        ------
        HTTPException
            If the baseline scenario doesn't exist
        """
        # We want to error differently if this dataset doesn't exist
        is_valid_dataset = await pool.fetchval(
            """
            SELECT exists (
                SELECT 1 FROM client_info.site_baselines WHERE baseline_id = $1 LIMIT 1
            )""",
            dataset_id.dataset_id,
        )
        if not is_valid_dataset:
            raise HTTPException(400, f"Site {dataset_id.dataset_id} not found in the database.")

        # We only want the most recent baseline config, so select them ordered by their created_at timestamps.
        # The rest are stored only for historical interest, or for different EPOCH versions.
        baseline_rec = await pool.fetchrow(
            """
            SELECT
                baseline
            FROM
                client_info.site_baselines
            WHERE baseline_id = $1""",
            dataset_id.dataset_id,
        )
        return baseline_rec

    if isinstance(site_or_dataset_id, SiteID):
        baseline_rec = await get_baseline_from_site_id(site_id=site_or_dataset_id)
    else:
        baseline_rec = await get_baseline_from_dataset_id(dataset_id=site_or_dataset_id)

    if baseline_rec is None:
        return DEFAULT_CONFIG

    def pydantic_strict_validate(unpacked: dict) -> TaskData:
        """
        Try to validate this dictionary against the pydantic model, throwing out extra keys.

        This checks two keys deep and tries to replicate the extra: forbid behaviour from pydantic.
        We would normally set that on the model specifically, but here our models are auto generated so we can't edit them.
        So here, we iterate through the first two layers of the dictionary and check if there are any missing keys.
        If there are multiple potential types for a given field, check if the defined field is valid for any of them
        (note that this will falsely succeed if your new sub component is a mixture of the two valid components, but is
        itself invalid).

        Parameters
        ----------
        unpacked
            TaskData-like dictionary

        Returns
        -------
        TaskData
            parsed taskdata, if we succeeded

        Raises
        ------
        HTTPException
            If we failed to generate this
        """
        for key, subdict in unpacked.items():
            if key not in TaskData.model_fields:
                raise HTTPException(400, f"Bad component in stored baseline: {key}")
            if isinstance(subdict, dict):
                for subkey in subdict.keys():
                    expected_type = TaskData.model_fields[key].annotation
                    found_in_any = False
                    for subtype in typing.get_args(expected_type):
                        expected_mdl = subtype()
                        # Check that we got a valid pydantic Model here to rule out None and NoneType, which have
                        # a habit of sneaking through (and can be surprisingly hard to construct!)
                        if isinstance(expected_mdl, BaseModel) and subkey in expected_mdl.model_fields:
                            found_in_any = True
                    if not found_in_any:
                        raise HTTPException(400, f"Bad component subvalue in stored baseline: {key}[{subkey}]")
        # We're not strict here to allow the enums to get through
        return TaskData.model_validate(unpacked, strict=False)

    try:
        baseline = json.loads(baseline_rec["baseline"])
        # We use this strict validate to complain if we allowed extra keys through the baseline
        # which pydantic would normally allow
        return pydantic_strict_validate(baseline)

    except ValidationError as ex:
        raise HTTPException(
            400, "Could not construct this baseline; has the format changed since it was filed?" + str(ex)
        ) from ex


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
    logger.info(f"Inserted client {client_data.client_id} with return status {status}")
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
                address,
                epc_lmk,
                dec_lmk)
            VALUES (
                $1,
                $2,
                $3,
                $4,
                $5,
                $6,
                $7,
                $8)""",
            site_data.client_id,
            site_data.site_id,
            site_data.name,
            site_data.location,
            site_data.coordinates,
            site_data.address,
            site_data.epc_lmk,
            site_data.dec_lmk,
        )
        logger.info(f"Inserted client {site_data.client_id} with return status {status}")
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
        """SELECT location FROM client_info.site_info WHERE site_id = $1 LIMIT 1""",
        site_id.site_id,
    )
    if location is None:
        raise HTTPException(400, f"Site ID `{site_id.site_id}` has no location in the database.")
    return str(location)


@router.post("/get-site-data", tags=["db"])
async def get_site_data(site_id: SiteID, pool: DatabasePoolDep) -> SiteData:
    """
    Get the metadata, including human readable name, address and coordinates, for this site.

    Parameters
    ----------
    site_id
        Database ID of the site you are interested in.

    Returns
    -------
    SiteData
        Metadata about this site, including the location and coordinates.
    """
    result = await pool.fetchrow(
        """
        SELECT
            client_id,
            name,
            location,
            coordinates,
            address,
            epc_lmk,
            dec_lmk
        FROM
            client_info.site_info
        WHERE
            site_id = $1""",
        site_id.site_id,
    )
    if result is None:
        raise HTTPException(400, f"Site ID `{site_id.site_id}` has no metadata in the database.")

    return SiteData(
        client_id=result["client_id"],
        site_id=site_id.site_id,
        name=result["name"],
        location=result["location"],
        coordinates=result["coordinates"],
        address=result["address"],
        epc_lmk=result["epc_lmk"],
        dec_lmk=result["dec_lmk"],
    )
