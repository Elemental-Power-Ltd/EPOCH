"""Functions and utils for getting public holiday information in the UK."""

import datetime
from enum import StrEnum

import httpx
from fastapi import HTTPException


class UKCountryEnum(StrEnum):
    """List of countries making up the UK (not Crown Dependencies!)."""

    England = "England"
    Wales = "Wales"
    Scotland = "Scotland"
    NorthernIreland = "NorthernIreland"


async def get_bank_holidays(
    country: UKCountryEnum | str = UKCountryEnum.England, http_client: httpx.AsyncClient | None = None
) -> list[datetime.date]:
    """
    Get a list of bank holidays for different countries in the UK.

    Bank holidays are published on gov.uk, but vary by country.
    Fun fact: the Government API also tells you if it's appropriate to put bunting on your website on each day.

    Parameters
    ----------
    http_client
        HTTP client capable of sending a get request
    country
        Which country you're interested in from the UK (may extend in future)

    Returns
    -------
    list[datetime.date]
        List of public holiday dates for that country.
    """
    if country == UKCountryEnum.England or country == UKCountryEnum.Wales:
        key = "england-and-wales"
    elif country == UKCountryEnum.Scotland:
        key = "scotland"
    elif country == UKCountryEnum.NorthernIreland:
        key = "northern-ireland"
    else:
        raise ValueError("Got unknown country for public holidays: " + str(country))
    if http_client is not None:
        response = await http_client.get("https://www.gov.uk/bank-holidays.json")
    else:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get("https://www.gov.uk/bank-holidays.json")
    if response.status_code != 200:
        raise HTTPException(response.status_code, "Could not get bank holiday information from gov.uk")

    data = response.json()[key]["events"]
    return [datetime.datetime.strptime(item["date"], "%Y-%m-%d").replace(tzinfo=datetime.UTC).date() for item in data]


def get_bank_holidays_sync(
    country: UKCountryEnum | str = UKCountryEnum.England, http_client: httpx.Client | None = None
) -> list[datetime.date]:
    """
    Get a list of bank holidays for different countries in the UK.

    Bank holidays are published on gov.uk, but vary by country.
    Fun fact: the Government API also tells you if it's appropriate to put bunting on your website on each day.

    Parameters
    ----------
    http_client
        HTTP client capable of sending a get request
    country
        Which country you're interested in from the UK (may extend in future)

    Returns
    -------
    list[datetime.date]
        List of public holiday dates for that country.
    """
    if country == UKCountryEnum.England or country == UKCountryEnum.Wales:
        key = "england-and-wales"
    elif country == UKCountryEnum.Scotland:
        key = "scotland"
    elif country == UKCountryEnum.NorthernIreland:
        key = "northern-ireland"
    else:
        raise ValueError("Got unknown country for public holidays: " + str(country))
    if http_client is not None:
        response = http_client.get("https://www.gov.uk/bank-holidays.json")
    else:
        with httpx.Client() as http_client:
            response = http_client.get("https://www.gov.uk/bank-holidays.json")
    if response.status_code != 200:
        raise HTTPException(response.status_code, "Could not get bank holiday information from gov.uk")

    data = response.json()[key]["events"]
    return [datetime.datetime.strptime(item["date"], "%Y-%m-%d").replace(tzinfo=datetime.UTC).date() for item in data]
