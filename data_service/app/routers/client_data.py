"""
Client data and database manipulation endpoints.

Endpoints in here generally add or list clients, sites, or their datasets.
The structure is that clients are the top level, each client has zero or more sites, and each
site has zero or more datasets of different kinds.
"""

import json
import typing
from logging import getLogger
from typing import cast

import asyncpg
from app.routers.heating_load.phpp import list_phpp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pydantic_core._pydantic_core import ValidationError

from ..dependencies import DatabasePoolDep
from ..internal.utils.uuid import uuid7
from ..models.client_data import BaselineMetadata, SolarLocation
from ..models.core import (
    ClientData,
    ClientID,
    ClientIdNamePair,
    DatasetID,
    SiteData,
    SiteID,
    SiteIdNamePair,
    dataset_id_t,
    location_t,
)
from ..models.epoch_types.task_data_type import Building, Config, GasHeater, Grid, TaskData

router = APIRouter()

logger = getLogger(__name__)


@router.post("/list-site-baselines", tags=["db", "baseline", "site"])
async def list_site_baselines(site_id: SiteID, pool: DatabasePoolDep) -> list[BaselineMetadata]:
    """
    List all the available baselines for this site.

    A baseline has a unique ID, a timestamp, a blob of JSON for the actual components, and maybe a tariff ID.

    Parameters
    ----------
    site_id
        ID of the site to look up a baseline for

    pool
        Database connection pool to look up into

    Returns
    -------
    list[BaselineMetadata]
        List of all available baselines for this site. An empty list if there are none, which would mean you get the
        default baseline for your simulations of this site.
        Note that we don't unpack the baseline JSON properly, as it might not be parseable as a valid TaskData.
    """
    res = await pool.fetch(
        """
        SELECT
            baseline_id, created_at, baseline, tariff_id
        FROM client_info.site_baselines
        WHERE site_id = $1
        ORDER BY created_at ASC""",
        site_id.site_id,
    )
    return [
        BaselineMetadata(
            baseline_id=item["baseline_id"],
            created_at=item["created_at"],
            baseline=json.loads(item["baseline"]),
            tariff_id=item["tariff_id"],
        )
        for item in res
    ]


@router.post("/add-site-baseline", tags=["db", "baseline", "site"])
async def add_baseline(site_id: SiteID, baseline: TaskData, pool: DatabasePoolDep) -> dataset_id_t:
    """
    Add the baseline configuration for a site in the database.

    The baseline contains all the infrastructure that is already there:
    by default, this is just a Building, a Grid and a Gas heater.
    However, for some sites this will also include heat pumps or solar arrays.

    This will override previous baselines that are stored in the database, as we only ever fetch the latest.
    Baselines are given a UUID when generated that you can use for a task_config object later on.
    If there is an existing baseline in the database with a tariff set, we'll propagate that forwards to this new baseline
    for you.

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
    dataset_id_t
        The ID of the newly inserted baseline.
    """
    if baseline.building is not None and baseline.building.floor_area is None:
        all_phpps = await list_phpp(site_id=site_id, pool=pool)
        if all_phpps:
            latest_phpp = max(all_phpps, key=lambda x: x.created_at)
            logger.warning(f"No floor area provided for {site_id.site_id}, and found a PHPP with ID {latest_phpp.structure_id}")
            latest_floor_area = latest_phpp.floor_area
            baseline.building.floor_area = latest_floor_area
        else:
            logger.warning(f"No floor area provided for {site_id.site_id}, and couldn't find any PHPPs")

    # Check if the previous baseline had a tariff ID, if so, re-use it.
    baseline_tariff_id = cast(
        dataset_id_t | None,
        await pool.fetchval(
            """
            SELECT
                tariff_id
            FROM client_info.site_baselines
            WHERE site_id = $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            site_id.site_id,
        ),
    )
    baseline_id = uuid7()
    try:
        await pool.execute(
            """
            INSERT INTO client_info.site_baselines (baseline_id, site_id, baseline, tariff_id) VALUES ($1, $2, $3, $4)""",
            baseline_id,
            site_id.site_id,
            baseline.model_dump_json(),
            baseline_tariff_id,
        )
    except asyncpg.exceptions.ForeignKeyViolationError as ex:
        raise HTTPException(400, f"Site {site_id.site_id} not found in the database.") from ex
    else:
        return baseline_id


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
        return await pool.fetchrow(
            """
            SELECT
                baseline
            FROM
                client_info.site_baselines
            WHERE site_id = $1
            ORDER BY created_at DESC LIMIT 1""",
            site_id.site_id,
        )

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
        return await pool.fetchrow(
            """
            SELECT
                baseline
            FROM
                client_info.site_baselines
            WHERE baseline_id = $1""",
            dataset_id.dataset_id,
        )

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
                for subkey in subdict:
                    expected_type = TaskData.model_fields[key].annotation
                    found_in_any = False
                    for subtype in typing.get_args(expected_type):
                        expected_mdl = subtype()
                        # Check that we got a valid pydantic Model here to rule out None and NoneType, which have
                        # a habit of sneaking through (and can be surprisingly hard to construct!)
                        if isinstance(expected_mdl, BaseModel) and subkey in type(expected_mdl).model_fields:
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
async def add_client(client_data: ClientData, pool: DatabasePoolDep) -> ClientData:
    """
    Add a new client into the database.

    Clients are the top level of organisation, and each client has a set of "sites" underneath it.
    Each client has a human readable name and an internal database ID.
    You get to choose the database ID, but please pick something easily memorable from the name, all in lowercase
    and joined by underscores.

    This will reject duplicate clients with an error.

    Parameters
    ----------
    client_data
        Metadata about the client, currently a client_id and name pair.

    Returns
    -------
    client_data
        Original client data
    """
    try:
        status = await pool.execute(
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
    return client_data


@router.post("/add-site", tags=["db", "add"])
async def add_site(site_data: SiteData, pool: DatabasePoolDep) -> tuple[SiteData, str]:
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
    site_data
        Metadata about the site, including client_id, site_id, name, location, coordinates and address.

    Returns
    -------
        Data you inserted and postgres response string.
    """
    try:
        status = await pool.execute(
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
async def list_clients(pool: DatabasePoolDep) -> list[ClientIdNamePair]:
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
    res = await pool.fetch("""
        SELECT DISTINCT
            client_id,
            name
        FROM client_info.clients""")
    return [ClientIdNamePair(client_id=item[0], name=item[1]) for item in res]


@router.post("/list-sites", tags=["db", "list"])
async def list_sites(client_id: ClientID, pool: DatabasePoolDep) -> list[SiteIdNamePair]:
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
    res = await pool.fetch(
        """
        SELECT DISTINCT
            site_id,
            name
        FROM client_info.site_info
        WHERE client_id = $1
        ORDER BY name ASC""",
        client_id.client_id,
    )
    return [SiteIdNamePair(site_id=item[0], name=item[1]) for item in res]


@router.post("/get-solar-locations", tags=["db", "pv"])
async def get_solar_locations(site_id: SiteID, pool: DatabasePoolDep) -> list[SolarLocation]:
    """
    Get all the possible locations for solar arrays on this site.

    One site will have zero to many potential solar arrays, each with a maximum size, a tilt, an azimuth and
    a indication of roof / ground mounted.
    The maximum size is in kWp assuming 1x2m 440W panels laid out as densely as practical.
    The azimuth and tilt are the optimal arrangements of panels for that bit of roof or ground and are
    in degrees from true North and the surface normal respectively.
    For flat roofs, this may be split into two separate East/West locations.

    Each location is tagged with a human readable name so you know what it refers to.

    Parameters
    ----------
    site_id
        The ID of the site you want to get the potential solar locations of
    pool
        Database connection pool to look these up in

    Returns
    -------
    list[SolarLocation]
        List of all potential solar locations at the site, ordered alphabetically by their location ID
    """
    res = await pool.fetch(
        """
        SELECT
            site_id,
            renewables_location_id,
            name,
            tilt,
            azimuth,
            maxpower,
            mounting_type
        FROM
            client_info.solar_locations
        WHERE site_id = $1
        ORDER BY renewables_location_id
        """,
        site_id.site_id,
    )

    return [
        SolarLocation(
            site_id=item["site_id"],
            renewables_location_id=item["renewables_location_id"],
            name=item["name"],
            tilt=item["tilt"],
            azimuth=item["azimuth"],
            maxpower=item["maxpower"],
        )
        for item in res
    ]


@router.post("/add-solar-location", tags=["db", "solar_pv", "add"])
async def add_solar_locations(location: SolarLocation, pool: DatabasePoolDep) -> SolarLocation:
    """
    Get all the possible locations for solar arrays on this site.

    One site will have zero to many potential solar arrays, each with a maximum size, a tilt, an azimuth and
    a indication of roof / ground mounted.
    The maximum size is in kWp assuming 1x2m 440W panels laid out as densely as practical.
    The azimuth and tilt are the optimal arrangements of panels for that bit of roof or ground and are
    in degrees from true North and the surface normal respectively.
    For flat roofs, this may be split into two separate East/West locations.

    Each location is tagged with a human readable name so you know what it refers to.

    Parameters
    ----------
    location
        A solar location with a unique site name
    pool
        Database connection pool to add this to

    Returns
    -------
    location
        The location just added to the database
    """
    assert location.renewables_location_id is not None, "Renewables Location ID must not be None"
    if not location.renewables_location_id.startswith(location.site_id):
        raise HTTPException(
            422,
            f"Location ID {location.renewables_location_id} must include  site ID {location.site_id} for uniqueness (sorry!)",
        )

    if location.renewables_location_id == location.site_id:
        raise HTTPException(
            422,
            f"Location ID {location.renewables_location_id} must not be equal to {location.site_id} to avoid confusion.",
        )
    try:
        res = await pool.execute(
            """
            INSERT INTO client_info.solar_locations (
                site_id,
                renewables_location_id,
                name,
                tilt,
                azimuth,
                maxpower,
                mounting_type
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            location.site_id,
            location.renewables_location_id,
            location.name,
            location.tilt,
            location.azimuth,
            location.maxpower,
            location.mounting_type,
        )
    except asyncpg.exceptions.UniqueViolationError as ex:
        raise HTTPException(400, f"Non-unique renewables location ID: {location.renewables_location_id} already exists") from ex
    if res:
        return location
    raise HTTPException(400, "Error in adding solar location")


@router.post("/get-location", tags=["db"])
async def get_location(site_id: SiteID, pool: DatabasePoolDep) -> location_t:
    """
    Get the location name for this site.

    Location names are generally the closest town that we can look up weather for.

    Parameters
    ----------
    site_id
        Database ID of the site you are interested in.

    Returns
    -------
    location
        Name of the location e.g. "Worksop", "Retford", "Cardiff"
    """
    location = await pool.fetchval(
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
            dec_lmk,
        FROM
            client_info.site_info
        WHERE
            site_id = $1
        LIMIT 1""",
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
