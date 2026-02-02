"""
Endpoints for import tariffs, calculating electrical cost in p / kWh.

Currently just uses Octopus data, but will likely use RE24 data in future.
"""

import datetime
import itertools
import logging
from typing import cast

import numpy as np
import pandas as pd
from app.internal.epl_typing import RecordMapping
from fastapi import APIRouter, HTTPException

from ..dependencies import DatabasePoolDep, HttpClientDep
from ..internal.client_data import get_postcode
from ..internal.import_tariffs import (
    create_custom_tariff,
    create_day_and_night_tariff,
    create_fixed_tariff,
    create_peak_tariff,
    create_shapeshifter_tariff,
    get_day_and_night_rates,
    get_elexon_wholesale_tariff,
    get_fixed_rates,
    get_octopus_tariff,
    get_re24_wholesale_tariff,
    get_shapeshifters_rates,
    resample_to_range,
    tariff_to_new_timestamps,
)
from ..internal.import_tariffs.re24 import get_re24_approximate_ppa
from ..internal.site_manager.bundles import file_self_with_bundle
from ..internal.utils.uuid import uuid7
from ..models.core import DatasetID, MultipleDatasetIDWithTime, SiteID, SiteIDWithTime
from ..models.import_tariffs import (
    BaselineTariffRequest,
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

# Store the postcodes that we've already looked up to reduce 3rd party requests
POSTCODE_CACHE: dict[str, GSPCodeResponse] = {}


async def get_gsp_code_from_postcode(inbound_postcode: str, http_client: HttpClientDep) -> GSPCodeResponse:
    """
    Get a Grid Supply Point code, including regional information.

    This uses the National Grid ESO API to look up Grid Supply points
    and Distribution Network Operators for a given site.
    The site is looked up via its postcode and should exist in the database.

    Parameters
    ----------
    inbound_postcode
        Postcode of the site you want to look up. Ideally provide the inbound section e.g. "W1A" or an inbound outbound
        pair separated by a space
    http_client
        HTTP client used to look this up in the carbon intensity geocoding API

    Returns
    -------
    GSPCodeResponse
        Details about the grid supply and DNO for this site.
    """
    # We've received a combined postcode, so split it.
    if " " in inbound_postcode:
        inbound_postcode, _ = inbound_postcode.split(" ")
    if inbound_postcode in POSTCODE_CACHE:
        return POSTCODE_CACHE[inbound_postcode]
    ci_result = await http_client.get(f"https://api.carbonintensity.org.uk/regional/postcode/{inbound_postcode}")
    if not ci_result.is_success or "data" not in ci_result.json():
        if ci_result.status_code == 400 and ci_result.json()["error"]["message"] == "No postcode match can be found.":
            raise ValueError(f"Got a bad postcode: {inbound_postcode}")
        raise HTTPException(400, f"Got error from CarbonIntensity API: {ci_result.status_code}: {ci_result.json()}.")

    region_id = ci_result.json()["data"][0]["regionid"]
    dno_region_id = CARBON_INTENSITY_ID_TO_AREA_ID[region_id]
    if dno_region_id is None:
        raise HTTPException(400, f"A region ID without corresponding area id: {region_id}.")

    POSTCODE_CACHE[inbound_postcode] = GSPCodeResponse(
        ci_region_id=region_id,
        dno_region_id=dno_region_id,
        region_code=AREA_ID_TO_GSP[dno_region_id],
        dno_region=ci_result.json()["data"][0]["dnoregion"],
    )
    return POSTCODE_CACHE[inbound_postcode]


@router.post("/add-baseline-tariff", tags=["baseline", "tariff"])
async def add_baseline_tariff(
    baseline_id: DatasetID, tariff_req: BaselineTariffRequest, pool: DatabasePoolDep, http_client: HttpClientDep
) -> TariffMetadata:
    """
    Generate a tariff and mark it as being the baseline tariff.

    The baseline tariff is the one that we compare costs to, and is always at index 0 when provided to EPOCH.
    This can be any sort of tariff, but is mostly commonly fixed.
    Use the `tariff_req` parameter to set the details of the tariff following the instructions in `generate-import-tariffs`,
    which this internally delegates to.

    Run this before `generate-all` for your site as the baseline tariff will be carried forward from there and
    the correct metadata set.

    Do not specify any `bundle_metadata` (it is specifically nulled out here!)
    as that will be handled in `generate-all` and when fetching tariffs.


    Parameters
    ----------
    baseline_id
        ID of the baseline that you have created through `add-site-baseline`.

    site_id: site_id_t
        The ID of the site you want to generate the tariff for (we'll look up grid supply location with this).

    tariff_name: SyntheticTariffEnum | str
        If a string like `E-1R-AGILE-24-04-03-A` then we'll look up the specific Octopus tariff.
        Or could be a synthetic tariff type like `custom`, `fixed`, `overnight`, `peak`.

    day_cost: float | None
        For a synthetic tariff, the fixed cost for 'day' periods in p/kWh. If None, will look up an Octopus tariff.
        Not needed for a `custom` tariff or an Octopus tariff, so leave as None in that case.

    night_cost: float | None
        For a synthetic tariff, the fixed cost for 'night' periods in p/kWh. Will most commonly be lower than 'day'.
        Not needed for a `custom` tariff or an Octopus tariff, so leave as None in that case.

    peak_cost: float | None
        For a synthetic tariff, the fixed cost for 'peak' periods in p/kWh. Will most commonly be higher than 'day'.
        Not needed for a `custom` or `overnight` tariff or an Octopus tariff, so leave as None in that case.

    cost_bands: list[TariffCostBand] | None
        Cost bands in form [{'end_time':..., 'cost':...}] for a custom tariff. Ignore if not using a custom tariff.
        These override the day, night and peak costs so leave them as None.
        These apply every 24 hours and should cover the whole time period, so make sure you have an entry that ends at 00:00.

    bundle_metadata
        Set automatically! Leave this empty.

    Returns
    -------
    TariffMetadata
        Some useful metadata about the tariff entry in the database, including what we used to generate it.
    """
    new_tariff = await generate_import_tariffs(params=tariff_req, pool=pool, http_client=http_client)
    new_tariff_id = new_tariff.dataset_id
    await pool.execute(
        """UPDATE client_info.site_baselines SET tariff_id = $1 WHERE baseline_id = $2""", new_tariff_id, baseline_id.dataset_id
    )
    return new_tariff


@router.post("/get-gsp-code", tags=["list", "tariff"])
async def get_gsp_code(site_id: SiteID, http_client: HttpClientDep, pool: DatabasePoolDep) -> GSPCodeResponse:
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
    postcode = await get_postcode(site_id.site_id, pool=pool)
    inbound_postcode, _ = postcode.split(" ")
    return await get_gsp_code_from_postcode(inbound_postcode, http_client)


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
            is_tracker=item.get("is_tracker") == "true",
            is_prepay=item.get("is_prepay") == "true",
            is_variable=item.get("is_variable") == "true",
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
    Generate a specific import tariff, either according to a specific synthetic pattern or from Octopus.

    This should most commonly be called as part of a `generate-all` run as that will fill in the bundle metadata.
    If you want to use this to create a custom tariff, then first call `generate-all`, record the bundle ID
    and get ready to fill in the associated metadata here with your specified tariff parameters.

    Parameters
    ----------
    site_id: site_id_t
        The ID of the site you want to generate the tariff for (we'll look up grid supply location with this).

    tariff_name: SyntheticTariffEnum | str
        If a string like `E-1R-AGILE-24-04-03-A` then we'll look up the specific Octopus tariff.
        Or could be a synthetic tariff type like `custom`, `fixed`, `overnight`, `peak`.

    day_cost: float | None
        For a synthetic tariff, the fixed cost for 'day' periods in p/kWh. If None, will look up an Octopus tariff.
        Not needed for a `custom` tariff or an Octopus tariff, so leave as None in that case.

    night_cost: float | None
        For a synthetic tariff, the fixed cost for 'night' periods in p/kWh. Will most commonly be lower than 'day'.
        Not needed for a `custom` tariff or an Octopus tariff, so leave as None in that case.

    peak_cost: float | None
        For a synthetic tariff, the fixed cost for 'peak' periods in p/kWh. Will most commonly be higher than 'day'.
        Not needed for a `custom` or `overnight` tariff or an Octopus tariff, so leave as None in that case.

    cost_bands: list[TariffCostBand] | None
        Cost bands in form [{'end_time':..., 'cost':...}] for a custom tariff. Ignore if not using a custom tariff.
        These override the day, night and peak costs so leave them as None.
        These apply every 24 hours and should cover the whole time period, so make sure you have an entry that ends at 00:00.

    bundle_metadata
        Information about the existing data bundle you want to associate this new tariff with, including the "tariff index"
        which should be an integer greater than any of the tariffs you have generated as part of this bundle so far.

    Returns
    -------
    tariff_metadata
        Some useful metadata about the tariff entry in the database, including what we used to generate it.
    """
    region_code = (await get_gsp_code(SiteID(site_id=params.site_id), http_client=http_client, pool=pool)).region_code

    # Use these for tracking and returning metadata; they're frequently overwrittten by the
    # lookups to Octopus.
    day_cost, night_cost, peak_cost = None, None, None
    if isinstance(params.tariff_name, SyntheticTariffEnum):
        provider = TariffProviderEnum.Synthetic
        match params.tariff_name:
            case SyntheticTariffEnum.Fixed:
                logger.info(f"Generating a Fixed tariff in {region_code} between {params.start_ts} and {params.end_ts}")
                underlying_tariff = "LOYAL-FIX-12M-23-12-30"
                timestamps = pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="both")
                if params.day_cost is None:
                    day_cost = await get_fixed_rates(tariff_name=underlying_tariff, region_code=region_code, client=http_client)
                else:
                    day_cost = params.day_cost
                price_df = create_fixed_tariff(timestamps, fixed_cost=day_cost)
            case SyntheticTariffEnum.Agile:
                # Note that this ignore the parameter costs you've provided.
                logger.info(f"Generating an Agile-like tariff in {region_code} between {params.start_ts} and {params.end_ts}")
                # Use these rounded dates to make sure everything resamples nicely and that we get the most recent data.
                underlying_tariff = "RE24-NORDPOOL"
                end_ts = datetime.datetime.now(datetime.UTC).replace(hour=0, minute=0, second=0, microsecond=0)
                start_ts = end_ts - datetime.timedelta(days=365)
                price_df = await get_re24_wholesale_tariff(
                    start_ts=start_ts, end_ts=end_ts, http_client=http_client, region_code=region_code
                )
                price_df = tariff_to_new_timestamps(
                    price_df, pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30))
                )
            case SyntheticTariffEnum.Peak:
                # use the FIX prices and the Octopus Cosy pricing structure
                # https://octopus.energy/smart/cosy-octopus/
                logger.info(f"Generating a Peak tariff in {region_code} between {params.start_ts} and {params.end_ts}")
                underlying_tariff = "LOYAL-FIX-12M-23-12-30"
                timestamps = pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="both")

                if params.day_cost is None:
                    # For the peak-y tariff, ignore the 'night' rates from Octopus as they're for Economy 7
                    _, day_cost = await get_day_and_night_rates(
                        tariff_name=underlying_tariff, region_code=region_code, client=http_client
                    )
                else:
                    day_cost = params.day_cost

                # For cosy Octopus, the nights are always 49% of the price of the day periods
                night_cost = day_cost * 0.49 if params.night_cost is None else params.night_cost

                # For Cosy Octopus, the 4-7pm peak is always 150% of the price of the day periods
                peak_cost = day_cost * 1.5 if params.peak_cost is None else params.peak_cost

                price_df = create_peak_tariff(timestamps, day_cost=day_cost, night_cost=night_cost, peak_cost=peak_cost)
            case SyntheticTariffEnum.Overnight:
                logger.info(f"Generating an Overnight tariff in {region_code} between {params.start_ts} and {params.end_ts}")
                underlying_tariff = "LOYAL-FIX-12M-23-12-30"
                timestamps = pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="both")

                if params.day_cost is None or params.night_cost is None:
                    # If either of these costs is None, then get both of them and fill in whichever ones are missing
                    # (this nested logic is to avoid an expensive 3rd party API call in get_day_and_night_rates)
                    night_cost, day_cost = await get_day_and_night_rates(
                        tariff_name=underlying_tariff, region_code=region_code, client=http_client
                    )
                    if params.night_cost is not None:
                        night_cost = params.night_cost
                    if params.day_cost is not None:
                        day_cost = params.day_cost
                else:
                    night_cost, day_cost = params.night_cost, params.day_cost

                price_df = create_day_and_night_tariff(timestamps, day_cost=day_cost, night_cost=night_cost)
            case SyntheticTariffEnum.ShapeShifter:
                logger.info(f"Generating a ShapeShifter tariff in {region_code} between {params.start_ts} and {params.end_ts}")
                underlying_tariff = "BUS-12M-FIXED-SHAPE-SHIFTER-25-05-23"
                timestamps = pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="both")

                postcode = await get_postcode(params.site_id, pool=pool)
                if params.day_cost is None or params.night_cost is None or params.peak_cost is None:
                    shapeshifter_costs = await get_shapeshifters_rates(
                        postcode=postcode, client=http_client, underlying_tariff=underlying_tariff
                    )
                    day_cost, night_cost, peak_cost = (
                        shapeshifter_costs["day"],
                        shapeshifter_costs["night"],
                        shapeshifter_costs["peak"],
                    )
                    if params.day_cost is not None:
                        day_cost = params.day_cost
                    if params.night_cost is not None:
                        night_cost = params.night_cost
                    if params.peak_cost is not None:
                        peak_cost = params.peak_cost
                else:
                    day_cost, night_cost, peak_cost = params.day_cost, params.night_cost, params.peak_cost

                price_df = create_shapeshifter_tariff(
                    timestamps,
                    day_cost=day_cost,
                    night_cost=night_cost,
                    peak_cost=peak_cost,
                )
            case SyntheticTariffEnum.PowerPurchaseAgreement:
                logger.info("Generating a PPA")

                # First we need a grid tariff to act as a backup for any excess energy
                # that we can't purchase via a PPA
                underlying_tariff = "LOYAL-FIX-12M-23-12-30"
                timestamps = pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="both")
                fixed_cost = await get_fixed_rates(tariff_name=underlying_tariff, region_code=region_code, client=http_client)
                fixed_df = create_fixed_tariff(timestamps, fixed_cost=fixed_cost)

                price_df = await get_re24_approximate_ppa(
                    params=SiteIDWithTime(site_id=params.site_id, start_ts=params.start_ts, end_ts=params.end_ts),
                    grid_tariff=fixed_df,
                )
            case SyntheticTariffEnum.Wholesale:
                logger.info("Generating a Wholesale tariff")

                # First we need a grid tariff to act as a backup for any excess energy
                # that we can't purchase via a PPA
                underlying_tariff = "APXMIDP"

                price_df = await get_elexon_wholesale_tariff(
                    start_ts=params.start_ts, end_ts=params.end_ts, http_client=http_client
                )
            case SyntheticTariffEnum.Custom:
                assert params.cost_bands, "Cost bands not provided"
                logger.info("Generating a custom tariff")
                underlying_tariff = "Custom"
                timestamps = pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="both")

                price_df = create_custom_tariff(
                    timestamps,
                    end_times=[item.end_time for item in params.cost_bands],
                    costs=[item.cost for item in params.cost_bands],
                )
                if price_df.cost.isna().any():
                    raise HTTPException(400, "Bad time bands provided, didn't cover all 24 hours. Should end at midnight!")
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

    if price_df.empty:
        raise HTTPException(400, f"Got an empty dataframe for {params.tariff_name}")

    # Note that we don't write the day, night or peak costs to the database currently.
    # They're mostly just there for you to check the responses when you get them, if needed.
    # (the costs themselves are obvious in the time series)
    metadata = TariffMetadata(
        dataset_id=params.bundle_metadata.dataset_id if params.bundle_metadata is not None else uuid7(),
        site_id=params.site_id,
        created_at=datetime.datetime.now(datetime.UTC),
        provider=provider,
        product_name=params.tariff_name,
        tariff_name=underlying_tariff,
        day_cost=day_cost,
        night_cost=night_cost,
        peak_cost=peak_cost,
        valid_from=None,
        valid_to=None,
    )

    mask = np.logical_and(price_df.index >= params.start_ts, price_df.index < params.end_ts)
    price_df = price_df[mask]
    price_df["start_ts"] = price_df.index
    price_df["end_ts"] = price_df.index + pd.Timedelta(minutes=30)
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
                itertools.repeat(metadata.dataset_id, len(price_df)),
                price_df["start_ts"],
                price_df["end_ts"],
                price_df["cost"],
                strict=True,
            ),
            columns=["dataset_id", "start_ts", "end_ts", "unit_cost"],
        )

        if params.bundle_metadata is not None:
            await file_self_with_bundle(conn, bundle_metadata=params.bundle_metadata)
    logger.info(f"Import tariff generation {metadata.dataset_id} of type {params.tariff_name} completed.")
    return metadata


@router.post("/get-import-tariffs", tags=["get", "tariff"])
async def get_import_tariffs(params: MultipleDatasetIDWithTime, conn: DatabasePoolDep) -> EpochTariffEntry:
    """
    Get the electricity import tariffs in £ / kWh for this dataset.

    You can create tariffs with the `generate-import-tariffs` endpoint.
    These are currently just Octopus time-of-use tariffs.

    It always returns 30 minute tariff intervals, regardless of the original source data.
    Tariffs will be forward-filled if they were originally sparser.
    Watch out, as the unit costs in the database are in p / kWh but this returns £ / kWh.

    Parameters
    ----------
    *request*
        Internal FastAPI request object
    *params*
        The ID of the dataset you want, and the timestamps (usually the year) you want it for.

    Returns
    -------
    EpochTariffEntry
        Tariff entries with entrties in £ / kWh.
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
            raise ValueError(
                f"Could not get an ImportTariff dataset for {dataset_id} between {params.start_ts} and {params.end_ts}."
            )
        df = pd.DataFrame.from_records(cast(RecordMapping, res), index="start_ts", columns=["start_ts", "end_ts", "unit_cost"])
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

    # Note that the unit costs in the database are in p / kWh, but we return £ / kWh for EPOCH to use.
    # Yes, this is very confusing.
    return EpochTariffEntry(timestamps=dfs[0].index.to_list(), data=[(df["unit_cost"] / 100).to_list() for df in dfs])
