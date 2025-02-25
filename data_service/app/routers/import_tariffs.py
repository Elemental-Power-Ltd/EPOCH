"""
Endpoints for import tariffs, calculating electrical cost in p / kWh.

Currently just uses Octopus data, but will likely use RE24 data in future.
"""

import datetime
import logging
import uuid

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from ..dependencies import DatabaseDep, DatabasePoolDep, HttpClientDep
from ..internal.import_tariffs import (
    combine_tariffs,
    create_day_and_night_tariff,
    create_fixed_tariff,
    create_peak_tariff,
    get_day_and_night_rates,
    get_fixed_rates,
    get_octopus_tariff,
    resample_to_range,
    tariff_to_new_timestamps,
)
from ..models.core import MultipleDatasetIDWithTime, SiteID, SiteIDWithTime
from ..models.import_tariffs import (
    EpochTariffEntry,
    GSPCodeResponse,
    GSPEnum,
    SyntheticTariffEnum,
    TariffListEntry,
    TariffMetadata,
    TariffProviderEnum,
    TariffRequest,
)

router = APIRouter()
logger = logging.getLogger("default")
# The CarbonIntensity API uses a different region numbering to normal
# https://carbon-intensity.github.io/api-definitions/#region-list


AREA_ID_TO_GSP = {
    10: GSPEnum.A,
    11: GSPEnum.B,
    12: GSPEnum.C,
    13: GSPEnum.D,
    14: GSPEnum.E,
    15: GSPEnum.F,
    16: GSPEnum.G,
    17: GSPEnum.P,
    18: GSPEnum.N,
    19: GSPEnum.J,
    20: GSPEnum.H,
    21: GSPEnum.K,
    22: GSPEnum.L,
    23: GSPEnum.M,
}

CARBON_INTENSITY_ID_TO_AREA_ID = {
    1: 17,  # North Scotland
    2: 18,  # South Scotland
    3: 16,  # North West England
    4: 15,  # North East England
    5: 23,  # Yorkshire
    6: 13,  # North Wales
    7: 21,  # South Wales
    8: 14,  # West Midlands
    9: 11,  # East Midlands
    10: 10,  # East England
    11: 22,  # South West England
    12: 20,  # South England
    13: 12,  # London
    14: 19,  # South East England
    15: None,  # England
    16: None,  # Scotland
    17: None,  # Wales
}


@router.post("/get-gsp-code", tags=["list", "tariff"])
async def get_gsp_code(site_id: SiteID, http_client: HttpClientDep, conn: DatabaseDep) -> GSPCodeResponse:
    """
    Get a Grid Supply Point code, including regional information.

    This uses the National Grid ESO API to look up Grid Supply points
    and Distribution Network Operators for a given site.
    The site is looked up via its postcode and should exist in the database.

    Parameters
    ----------
    site_id
        Database ID of the site you're interested in; must have a UK postcode in the database.

    Returns
    -------
    GSPCodeResponse
        Details about the grid supply and DNO for this site.
    """
    postcode = await conn.fetchval(
        r"""
    SELECT
        (regexp_match(address, '[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}'))[1]
    FROM client_info.site_info
    WHERE site_id = $1""",
        site_id.site_id,
    )
    if postcode is None:
        raise HTTPException(400, f"Could not find a postcode (and thus GSP code) for {site_id}.")
    inbound_postcode, _ = postcode.split(" ")
    ci_result = await http_client.get(f"https://api.carbonintensity.org.uk/regional/postcode/{inbound_postcode}")
    if not ci_result.status_code == 200 or "data" not in ci_result.json():
        raise HTTPException(400, f"Got error from CarbonIntensity API: {ci_result.status_code}: {ci_result.json()}.")

    region_id = ci_result.json()["data"][0]["regionid"]
    dno_region_id = CARBON_INTENSITY_ID_TO_AREA_ID[region_id]
    if dno_region_id is None:
        raise HTTPException(400, f"A region ID without corresponding area id: {region_id}.")

    return GSPCodeResponse(
        ci_region_id=region_id,
        dno_region_id=dno_region_id,
        region_code=AREA_ID_TO_GSP[dno_region_id],
        dno_region=ci_result.json()["data"][0]["dnoregion"],
    )


@router.post("/list-import-tariffs", tags=["list", "tariff"])
async def list_import_tariffs(params: SiteIDWithTime, http_client: HttpClientDep) -> list[TariffListEntry]:
    """
    List all the import tariffs available from Octopus.

    This will look at what tariffs were available at the starting timestamp you specify,
    and will return some useful metadata including when the tariff ends (it may be before your end timestamp),
    and if it is a variable tariff.
    This will only look at business tariffs.

    Parameters
    ----------
    params
        A site ID, start_ts and end_ts set. This currently only uses the start timestamp.

    Returns
    -------
    tariff_entries
        A list of tariffs including names, valid dates and whether they're variable.
    """

    def extract_tariff(item: dict[str, str]) -> TariffListEntry:
        """Extract a single tariff from the Octopus Tariff list, and turn it into a pydantic model."""
        return TariffListEntry(
            tariff_name=item["code"] if "code" in item else item["CODE"],
            valid_from=datetime.datetime.fromisoformat(item["available_from"])
            if item.get("available_from") is not None
            else None,
            valid_to=datetime.datetime.fromisoformat(item["available_to"]) if item.get("available_to") is not None else None,
            provider=TariffProviderEnum.octopus,
            is_tracker=True if item.get("is_tracker") == "true" else False,
            is_prepay=True if item.get("is_prepay") == "true" else False,
            is_variable=True if item.get("is_variable") == "true" else False,
        )

    tariff_list = (
        await http_client.get(
            "https://api.octopus.energy/v1/products/",
            params={"available_at": params.start_ts.isoformat(), "is_business": False},
        )
    ).json()

    all_tariffs = [extract_tariff(item) for item in tariff_list["results"] if item.get("direction", "").upper() == "IMPORT"]
    while tariff_list.get("next") is not None:
        tariff_list = (await http_client.get(tariff_list["next"])).json()

        all_tariffs.extend([extract_tariff(item) for item in tariff_list["results"]])

    return all_tariffs


@router.post("/select-arbitrary-tariff")
async def select_arbitrary_tariff(params: SiteIDWithTime, http_client: HttpClientDep) -> str:
    """
    Select an arbitrary tariff that will work for these time periods.

    Useful for when you need a tariff, but don't hugely care which.
    Will preferentially select a variable tariff that covers the entire time period you asked for.
    However, it will select a fixed tariff if only they are available, and the longest possible tariff.

    Parameters
    ----------
    params
        A site ID and (start, end) timestamp pair. Will aim to select a tariff that covers the whole time.

    Returns
    -------
    string name of the chosen tariff that you can use elsehwere.
    """
    listed_tariffs = await list_import_tariffs(params=params, http_client=http_client)
    ranking = []
    BROKEN_TARIFFS = {"QWPP_PP", "QWLOCAL_PP"}
    for tariff in listed_tariffs:
        if tariff.tariff_name in BROKEN_TARIFFS:
            continue
        valid_to = tariff.valid_to if tariff.valid_to is not None else datetime.datetime.now(datetime.UTC)
        valid_from = tariff.valid_from if tariff.valid_from is not None else params.start_ts
        overlap = min(
            (valid_to - max(valid_from, params.start_ts)).total_seconds() / (params.end_ts - params.start_ts).total_seconds(),
            1,
        )

        ranking.append((overlap, tariff.is_tracker, not tariff.is_prepay, tariff.tariff_name))

    ranking = sorted(ranking, reverse=True)

    if ranking[0][0] < 1.0:
        logger = logging.getLogger("default")
        logger.warning(
            f"Could not find a 100% overlapping tariff for {params.site_id} between {params.start_ts} and {params.end_ts}. "
            + f"Instead got {ranking[0][0]:.1%}."
        )
    return ranking[0][3]


@router.post("/generate-import-tariffs", tags=["generate", "tariff"])
async def generate_import_tariffs(params: TariffRequest, pool: DatabasePoolDep, http_client: HttpClientDep) -> TariffMetadata:
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
    async with pool.acquire() as conn:
        region_code = (await get_gsp_code(SiteID(site_id=params.site_id), http_client=http_client, conn=conn)).region_code

    if isinstance(params.tariff_name, SyntheticTariffEnum):
        provider = TariffProviderEnum.Synthetic
        if params.tariff_name == SyntheticTariffEnum.Agile:
            logger.info(f"Generating an Agile tariff in {region_code} between {params.start_ts} and {params.end_ts}")
            underlying_tariff = "AGILE-24-10-01"
            # Request "None" timestamps to get as much data as we have available.
            price_df_new = await get_octopus_tariff(
                underlying_tariff, region_code=region_code, start_ts=None, end_ts=None, client=http_client
            )
            # Combine with the previous agile tariff to get enough coverage
            price_df_old = await get_octopus_tariff(
                "AGILE-23-12-06", region_code=region_code, start_ts=None, end_ts=None, client=http_client
            )
            price_df = combine_tariffs([price_df_old, price_df_new])
            price_df = resample_to_range(price_df)
            price_df = tariff_to_new_timestamps(
                price_df, pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30))
            )
        elif params.tariff_name == SyntheticTariffEnum.Peak:
            # use the FIX prices and the Octopus Cosy pricing structure
            # https://octopus.energy/smart/cosy-octopus/
            logger.info(f"Generating a Peak tariff in {region_code} between {params.start_ts} and {params.end_ts}")
            underlying_tariff = "LOYAL-FIX-12M-23-12-30"
            timestamps = pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="both")
            night_cost, day_cost = await get_day_and_night_rates(
                tariff_name=underlying_tariff, region_code=region_code, client=http_client
            )
            price_df = create_peak_tariff(timestamps, day_cost=day_cost, night_cost=day_cost * 0.49, peak_cost=day_cost * 0.5)
        elif params.tariff_name == SyntheticTariffEnum.Overnight:
            logger.info(f"Generating an Overnight tariff in {region_code} between {params.start_ts} and {params.end_ts}")
            underlying_tariff = "LOYAL-FIX-12M-23-12-30"
            timestamps = pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="both")
            night_cost, day_cost = await get_day_and_night_rates(
                tariff_name=underlying_tariff, region_code=region_code, client=http_client
            )
            price_df = create_day_and_night_tariff(timestamps, day_cost=day_cost, night_cost=night_cost)
        elif params.tariff_name == SyntheticTariffEnum.Fixed:
            logger.info(f"Generating a Fixed tariff in {region_code} between {params.start_ts} and {params.end_ts}")
            underlying_tariff = "LOYAL-FIX-12M-23-12-30"
            timestamps = pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="both")
            fixed_cost = await get_fixed_rates(tariff_name=underlying_tariff, region_code=region_code, client=http_client)
            price_df = create_fixed_tariff(timestamps, fixed_cost=fixed_cost)
    else:
        logger.info(
            f"Generating a tariff with real Octopus data for {params.tariff_name} in {region_code}"
            + f" between {params.start_ts} and {params.end_ts}"
        )
        underlying_tariff = params.tariff_name
        provider = TariffProviderEnum.octopus
        price_df = await get_octopus_tariff(params.tariff_name, region_code, params.start_ts, params.end_ts, http_client)
        if len(price_df) == 1:
            # We got a fixed tariff!
            timestamps = pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="both")
            price_df = create_fixed_tariff(timestamps, fixed_cost=max(price_df["cost"]))
        elif len(price_df) == 2:
            # We got a varying day / night tariff.
            timestamps = pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="both")
            price_df = create_day_and_night_tariff(timestamps, day_cost=max(price_df["cost"]), night_cost=min(price_df["cost"]))
        # Otherwise we got a varying tariff that we can resample.
        price_df = resample_to_range(price_df, freq=pd.Timedelta(minutes=30), start_ts=params.start_ts, end_ts=params.end_ts)
    dataset_id = uuid.uuid4()

    if price_df.empty:
        raise HTTPException(400, f"Got an empty dataframe for {params.tariff_name}")

    mask = np.logical_and(price_df.index >= params.start_ts, price_df.index < params.end_ts)
    price_df = price_df[mask]
    price_df["start_ts"] = price_df.index
    price_df["end_ts"] = price_df.index + pd.Timedelta(minutes=30)
    price_df["dataset_id"] = dataset_id
    # Note that it doesn't matter that we've got "too  much" tariff data here, as we'll sort it out when we get it.
    async with pool.acquire() as conn:
        async with conn.transaction():
            metadata = TariffMetadata(
                dataset_id=dataset_id,
                site_id=params.site_id,
                created_at=datetime.datetime.now(datetime.UTC),
                provider=provider,
                product_name=params.tariff_name,
                tariff_name=underlying_tariff,
                valid_from=None,
                valid_to=None,
            )
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
                records=zip(price_df["dataset_id"], price_df["start_ts"], price_df["end_ts"], price_df["cost"], strict=True),
                columns=["dataset_id", "start_ts", "end_ts", "unit_cost"],
            )

    return metadata


@router.post("/get-import-tariffs", tags=["get", "tariff"])
async def get_import_tariffs(params: MultipleDatasetIDWithTime, conn: DatabasePoolDep) -> EpochTariffEntry:
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
    EpochTariffEntry
        Tariff entries in an EPOCH friendly format.
    """
    dfs: list[pd.DataFrame] = []
    for dataset_id in params.dataset_id:
        res = await conn.fetch(
            """
            SELECT
                start_ts,
                end_ts,
                unit_cost
            FROM tariffs.electricity
            WHERE dataset_id = $1
            AND $2 <= start_ts
            AND end_ts <= $3
            ORDER BY start_ts ASC""",
            dataset_id,
            params.start_ts,
            params.end_ts,
        )
        if not res:
            raise ValueError(f"Could not get a dataset for {dataset_id}.")
        df = pd.DataFrame.from_records(res, index="start_ts", columns=["start_ts", "end_ts", "unit_cost"])
        df.index = pd.to_datetime(df.index, utc=True)
        df = df.resample(pd.Timedelta(minutes=30)).max().ffill()
        dfs.append(df)

        # If we get 1970-01-01, that means someone didn't specify the timestamps.
        # In that case, we don't resample. But if they did, then pad out to the period of interest.
        if params.start_ts > datetime.datetime(year=1970, month=1, day=1, tzinfo=datetime.UTC):
            df = df.reindex(
                index=pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="left"),
                method="nearest",
            )

    return EpochTariffEntry(timestamps=dfs[0].index.to_list(), data=[(df["unit_cost"] / 100).to_list() for df in dfs])
