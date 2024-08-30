"""Functions and utils for getting public holiday information in the UK."""

import datetime
import enum

import httpx
from fastapi import HTTPException


class UKCountryEnum(str, enum.Enum):
    """List of countries making up the UK (not Crown Dependencies!)."""

    England = "England"
    Wales = "Wales"
    Scotland = "Scotland"
    NorthernIreland = "NorthernIreland"


async def get_bank_holidays(
    http_client: httpx.AsyncClient, country: UKCountryEnum | str = UKCountryEnum.England
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

    response = await http_client.get("https://www.gov.uk/bank-holidays.json")
    if response.status_code != 200:
        raise HTTPException(response.status_code, "Could not get bank holiday information from gov.uk")

    data = response.json()[key]["events"]
    return [datetime.datetime.strptime(item["date"], "%Y-%m-%d").replace(tzinfo=datetime.UTC).date() for item in data]
