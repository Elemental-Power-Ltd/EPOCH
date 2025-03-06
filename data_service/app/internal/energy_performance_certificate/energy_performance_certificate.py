"""
Get energy performance and display energy data from the OpenDataCommunities API.

Relevant third party documentation at
https://epc.opendatacommunities.org/docs/api/non-domestic
and
https://epc.opendatacommunities.org/docs/api/display
"""

import base64
from json import JSONDecodeError

from fastapi import HTTPException
from httpx import AsyncClient

from app.epl_secrets import get_secrets_environment
from app.models.energy_performance_certificate import NonDomesticDEC, NonDomesticEPC, NonDomesticRecommendation


def create_opendata_token(username: str, api_key: str) -> str:
    """
    Create a token to use for accessing the OpenDataCommunities API.

    See the documentation at
    https://epc.opendatacommunities.org/docs/api/non-domestic#using_this_api
    for details.

    Parameters
    ----------
    username
        Email address associated with the OpenDataCommunities account
    api_key
        Pre-generated API key from the OpenDataCommunities site

    Returns
    -------
    str
        Base64 encoded '{username}:{api_key}' string
    """
    # we have to do this horrible type transformation as the API expects a string,
    # but base64 only works on bytes -- argh!
    return base64.b64encode(f"{username}:{api_key}".encode()).decode("utf-8")


def create_search_params(postcode: str | None = None, address: str | None = None, uprn: str | None = None) -> dict[str, str]:
    """
    Create search parameters from a given combination of postcode, address and UPRN.

    We can only use one of these at a time to search, and users might have passed one or many of them.
    Returns a single element dict of the right type for the EPC API if only one is provided, and errors otherwise.

    Parameters
    ----------
    postcode
        Postcode, either outbound or outbound + inbound (with a space, ideally)
    address
        Free text searchable address string
    uprn
        Unique property reference number

    Returns
    -------
    dict[str, str]
        Dict keyed by the not-none type with the value being the passed argument.

    Raises
    ------
    ValueError
        If you didn't provide exactly one argument
    """
    count_not_none = sum(bool(item is not None) for item in (postcode, address, uprn))
    if count_not_none != 1:
        raise ValueError(f"Must only specify one of the arguments to this function, got {count_not_none}")

    if postcode is not None:
        return {"postcode": postcode}

    if address is not None:
        return {"address": address}

    if uprn is not None:
        return {"uprn": uprn}

    raise ValueError("Must only specify one of the arguments to this function, got 0")


async def get_cepc_by_lmk(lmk_key: str, http_client: AsyncClient) -> NonDomesticEPC:
    """
    Get a commercial EPC identified by its unique LMK key.

    This also gets the relevant recommendations, if any of them are attached.

    Parameters
    ----------
    lmk_key
        Unique ID for a commercial EPC
    http_client

    Returns
    -------
    NonDomesticEPC
        Non-domestic EPC retrieved from the API, with recommendations filled in (if possible!)
    """
    secrets = get_secrets_environment()
    token = create_opendata_token(secrets["OPENDATACOMMUNITIES_EMAIL"], secrets["OPENDATACOMMUNITIES_API_KEY"])
    headers = {"Accept": "application/json", "Authorization": f"Basic {token}"}

    response = await http_client.get(
        f"https://epc.opendatacommunities.org/api/v1/non-domestic/certificate/{lmk_key}", headers=headers
    )
    if response.status_code != 200 or not response.text:
        raise HTTPException(400, f"Could not get an EPC result for {lmk_key}, due to {response.text}")

    try:
        certificate = NonDomesticEPC.model_validate(response.json()["rows"][0])
    except JSONDecodeError as ex:
        raise HTTPException(400, f"Could not decode model for {lmk_key}: {ex}") from ex
    resp = await http_client.get(
        f"https://epc.opendatacommunities.org/api/v1/non-domestic/recommendations/{lmk_key}", headers=headers
    )
    if resp.status_code == 200 and resp.json()["rows"]:
        # Get all the recommendations, and attach them to this certificate (if there are any!)
        recommendations = [NonDomesticRecommendation.model_validate(row) for row in resp.json()["rows"]]
        certificate.recommendations = recommendations
    return certificate


async def get_dec_by_lmk(lmk_key: str, http_client: AsyncClient) -> NonDomesticDEC:
    """
    Get a Display Energy Certificate identified by its unique LMK key.

    This also gets the relevant recommendations, if any of them are attached.

    Parameters
    ----------
    lmk_key
        Unique ID for a commercial EPC
    http_client

    Returns
    -------
    NonDomesticEPC
        Display Energy Certificate retrieved from the API, with recommendations filled in (if possible!)
    """
    secrets = get_secrets_environment()
    token = create_opendata_token(secrets["OPENDATACOMMUNITIES_EMAIL"], secrets["OPENDATACOMMUNITIES_API_KEY"])
    headers = {"Accept": "application/json", "Authorization": f"Basic {token}"}

    response = await http_client.get(
        f"https://epc.opendatacommunities.org/api/v1/display/certificate/{lmk_key}", headers=headers
    )
    if response.status_code != 200 or not response.text:
        raise HTTPException(400, f"Could not get an DEC result for {lmk_key}, due to {response.text}")
    try:
        certificate = NonDomesticDEC.model_validate(response.json()["rows"][0])
    except JSONDecodeError as ex:
        raise HTTPException(400, f"Could not decode model for {lmk_key}: {ex}") from ex
    resp = await http_client.get(
        f"https://epc.opendatacommunities.org/api/v1/display/recommendations/{lmk_key}", headers=headers
    )
    if resp.status_code == 200 and resp.json()["rows"]:
        # Get all the recommendations, and attach them to this certificate (if there are any!)
        recommendations = [NonDomesticRecommendation.model_validate(row) for row in resp.json()["rows"]]
        certificate.recommendations = recommendations
    return certificate


async def get_cepcs_lookup(
    http_client: AsyncClient, postcode: str | None = None, address: str | None = None
) -> dict[str, NonDomesticEPC]:
    """
    Get all the non-domestic EPCs associated with a specific postcode or address.

    Note that this does not include the Display Energy Certificates (required for larger buildings)
    or the Air Conditioning certificates.
    A given postcode may have many EPCs associated with it; it is your responsibility to check
    that you have provided the right postcode and select the right EPC from the list.

    We will also fetch the relevant recommendations for a given EPC.

    Parameters
    ----------
    postcode
        Postcode to search for, can be either the outbound code or the full thing.
        Note that for an outbound code you'll get many results!

    Returns
    -------
    dict[str, NonDomesticEPC]
        All EPCs we found, uniquely identified by their LMK Key
    """
    secrets = get_secrets_environment()
    token = create_opendata_token(secrets["OPENDATACOMMUNITIES_EMAIL"], secrets["OPENDATACOMMUNITIES_API_KEY"])
    headers = {"Accept": "application/json", "Authorization": f"Basic {token}"}
    search_resp = await http_client.get(
        "https://epc.opendatacommunities.org/api/v1/non-domestic/search",
        params=create_search_params(postcode=postcode, address=address),
        headers=headers,
    )
    if search_resp.status_code != 200:
        raise HTTPException(400, f"Got error code from EPC API: {search_resp.text}")

    try:
        result = search_resp.json()
    except JSONDecodeError as ex:
        raise HTTPException(400, f"Got bad JSON from EPC API: {search_resp.text}") from ex

    # They actually return the EPC here in the search results but we fetch it again to keep our code DRY
    all_results = {}
    for row in result["rows"]:
        try:
            all_results[row["lmk-key"]] = await get_cepc_by_lmk(row["lmk-key"], http_client=http_client)
        except (JSONDecodeError, HTTPException):
            continue
    return all_results


async def get_decs_lookup(
    http_client: AsyncClient, postcode: str | None = None, address: str | None = None
) -> dict[str, NonDomesticDEC]:
    """
    Get all the non-domestic DECs associated with a specific postcode or address.

    Note that this does not include the Energy Performance Certificates (required for larger buildings)
    or the Air Conditioning certificates.
    A given postcode may have many DECss associated with it; it is your responsibility to check
    that you have provided the right postcode and select the right DEC from the list.

    We will also fetch the relevant recommendations for a given DEC.

    Parameters
    ----------
    postcode
        Postcode to search for, can be either the outbound code or the full thing.
        Note that for an outbound code you'll get many results!

    Returns
    -------
    dict[str, NonDomesticDEC]
        All DECs we found, uniquely identified by their LMK Key
    """
    secrets = get_secrets_environment()
    token = create_opendata_token(secrets["OPENDATACOMMUNITIES_EMAIL"], secrets["OPENDATACOMMUNITIES_API_KEY"])
    headers = {"Accept": "application/json", "Authorization": f"Basic {token}"}

    search_resp = await http_client.get(
        "https://epc.opendatacommunities.org/api/v1/display/search",
        params=create_search_params(postcode=postcode, address=address),
        headers=headers,
    )
    if search_resp.status_code != 200:
        raise HTTPException(400, f"Got error code from DEC API: {search_resp.text}")
    try:
        result = search_resp.json()
    except JSONDecodeError as ex:
        raise HTTPException(400, f"Got bad JSON from DEC API: {search_resp.text}") from ex

    all_results = {}
    for row in result["rows"]:
        try:
            all_results[row["lmk-key"]] = await get_dec_by_lmk(row["lmk-key"], http_client=http_client)
        except (JSONDecodeError, HTTPException):
            continue
    return all_results
