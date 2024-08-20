"""
Endpoints for import tariffs, calculating electrical cost in p / kWh.

Currently just uses Octopus data, but will likely use RE24 data in future.
"""

import datetime
import logging
import uuid

import pandas as pd
from fastapi import APIRouter, HTTPException

from ..dependencies import DatabaseDep, HttpClientDep
from ..internal.utils import hour_of_year
from ..internal.utils.utils import get_with_fallback
from ..models.core import DatasetIDWithTime, SiteID, SiteIDWithTime
from ..models.import_tariffs import (
    EpochTariffEntry,
    GSPCodeResponse,
    GSPEnum,
    TariffListEntry,
    TariffMetadata,
    TariffProviderEnum,
    TariffRequest,
)

router = APIRouter()

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
    if not ci_result.status_code == 200:
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
        )

    tariff_list = (
        await http_client.get(
            "https://api.octopus.energy/v1/products/",
            params={"available_at": params.start_ts.isoformat(), "is_business": False},
        )
    ).json()

    all_tariffs = [extract_tariff(item) for item in tariff_list["results"] if item.get("direction") == "IMPORT"]
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
async def generate_import_tariffs(params: TariffRequest, conn: DatabaseDep, http_client: HttpClientDep) -> TariffMetadata:
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

    response = await http_client.get(url)
    products = response.json()
    if response.status_code != 200:
        raise HTTPException(response.json()["detail"])

    product_available_from = datetime.datetime.fromisoformat(products.get("available_from", "1970-01-01T00:00:00Z"))
    if product_available_from > params.end_ts:
        raise HTTPException(
            400,
            f"Tariff {params.tariff_name} only available from {product_available_from}."
            + f"This is after your end timestamp of {params.end_ts}.",
        )
    region_code = (await get_gsp_code(SiteID(site_id=params.site_id), http_client=http_client, conn=conn)).region_code.value
    region_key = (
        region_code
        if region_code in products["single_register_electricity_tariffs"]
        else next(iter(products["single_register_electricity_tariffs"].keys()))
    )
    regional_data = products["single_register_electricity_tariffs"][region_key]

    tariff_code = get_with_fallback(regional_data, ["direct_debit_monthly", "prepayment"])["code"]

    price_url = url + f"electricity-tariffs/{tariff_code}/standard-unit-rates/"

    price_response = await http_client.get(
        price_url,
        params={
            "period_from": params.start_ts.isoformat(),
            "period_to": params.end_ts.isoformat(),
        },
    )

    price_data = price_response.json()
    price_records = list(price_data["results"])
    requests_made = 0
    while price_data.get("next") is not None:
        requests_made += 1
        price_response = await http_client.get(price_data["next"])
        price_data = price_response.json()
        price_records.extend(price_data["results"])

    price_df = pd.DataFrame.from_records(price_records)
    if price_df.empty:
        raise HTTPException(400, f"Got an empty dataframe for {params.tariff_name}")
    if "payment_method" in price_df:
        price_df = price_df.drop(columns=["payment_method"])
    price_df["valid_from"] = pd.to_datetime(price_df["valid_from"], utc=True, format="ISO8601")
    price_df["valid_to"] = pd.to_datetime(price_df["valid_to"], utc=True, format="ISO8601")
    price_df = price_df.set_index("valid_from").sort_index().resample(pd.Timedelta(hours=1)).max().ffill()

    price_df = price_df[["value_exc_vat"]].rename(columns={"value_exc_vat": "price", "valid_from": "start_ts"})
    price_df["start_ts"] = price_df.index
    price_df["dataset_id"] = dataset_id

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
            pd.to_datetime(metadata["valid_to"], utc=True, format="ISO8601"),
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
async def get_import_tariffs(params: DatasetIDWithTime, conn: DatabaseDep) -> list[EpochTariffEntry]:
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
    df = df.resample(pd.Timedelta(minutes=60)).max().ffill()
    # If we get 1970-01-01, that means someone didn't specify the timestamps.
    # In that case, we don't resample. But if they did, then pad out to the period of interest.
    if params.start_ts > datetime.datetime(year=1970, month=1, day=1, tzinfo=datetime.UTC):
        df = df.reindex(
            index=pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=60), inclusive="left"),
            method="nearest",
        )
    return [
        EpochTariffEntry(Date=ts.strftime("%d-%b"), HourOfYear=hour_of_year(ts), StartTime=ts.strftime("%H:%M"), Tariff=val)
        for ts, val in zip(df.index, df["unit_cost"], strict=True)
    ]
