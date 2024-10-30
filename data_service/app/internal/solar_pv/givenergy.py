"""Functions for interfacing with the GivEnergy API."""

import datetime
import os
import re
from collections import defaultdict

import httpx
import pandas as pd

from ..utils.jwt_utils import validate_jwt
from .givenergy_types import FullGivEnergyResponse, GivEnergyDict


def is_serial_number_valid(serial_number: str) -> bool:
    """
    Check if the GivEnergy serial number is valid.

    GivEnergy serials are in the form AB1234C567.
    Doesn't check if the serial really exists.

    Parameters
    ----------
    serial_number
        Potential GivEnergy string to match

    Returns
    -------
    True if serial number is a valid form.
    """
    match = re.match("[A-Z]{2}[0-9]{4}[A-Z][0-9]{3}", serial_number)
    return bool(match)


def givenergy_records_to_dataframe(raw_data: list[GivEnergyDict]) -> pd.DataFrame:
    """
    Turn a set of GivEnergy Inverter records into a pandas dataframe.

    This will have NaN entries for missing rows and report everything as floats.
    It should cope well with different numbers of solar arrays, but watch out for the final dataframe.

    The API is documented here:
    https://givenergy.cloud/docs/api/v1#inverter-data-GETinverter--inverter_serial_number--data-points--date-

    Parameters
    ----------
    raw_data: GivEnergyDict
        The 'data' entry of a response from the GivEnergy API, ideally with 'solar', 'grid', 'battery' and 'inverter'

    Returns
    -------
    Unnested pandas dataframe, with the solar arrays in array_{i}_... and other components in the form "{component}_{attribute}
    """
    unpacked_records = []
    for row in raw_data:
        default_nan: dict[str, float] = defaultdict(lambda: float("NaN"))
        solar = row.get("power", {}).get("solar", {}).get("arrays", [default_nan, default_nan])  # type: ignore

        grid = row.get("power", {}).get("grid", default_nan)
        battery = row.get("power", {}).get("battery", default_nan)
        inverter = row.get("power", {}).get("inverter", default_nan)
        unpacked_entry = {
            "time": datetime.datetime.fromisoformat(row["time"]),
            "grid_current": grid["current"],
            "grid_voltage": grid["voltage"],
            "grid_power": grid["power"],
            "grid_frequency": grid["frequency"],
            "battery_charge": battery["percent"] / 100.0,
            "battery_power": battery["power"],
            "battery_temperature": battery["temperature"],
            "consumption_power": row["power"]["consumption"]["power"],
            "inverter_power": inverter["power"],
            "inverter_temperature": inverter["temperature"],
            "inverter_voltage": inverter["output_voltage"],
            "inverter_frequency": inverter["output_frequency"],
            "inverter_eps_power": inverter["eps_power"],
        }
        for name_idx, array in enumerate(solar, 1):
            unpacked_entry[f"array_{name_idx}_voltage"] = array["voltage"]
            unpacked_entry[f"array_{name_idx}_current"] = array["current"]
            unpacked_entry[f"array_{name_idx}_power"] = array["power"]
        unpacked_records.append(unpacked_entry)
    return pd.DataFrame.from_records(unpacked_records, index="time")


def get_givenergy_day(
    timestamp: datetime.datetime, serial_number: str, client: httpx.Client | None = None
) -> list[GivEnergyDict]:
    """
    Get a single day from the GivEnergy API.

    Their API only allows us to get single days at a time, so you'll almost certainly want to call this in a loop.

    Parameters
    ----------
    timestamp
        Datetime you want to get data for; note that we only use the day of this entry.
    serial_number
        GivEnergy serial number of the component in the form AB1234B567
    client
        httpx client to use for sending requests

    Returns
    -------
        List of dict-like GivEnergy responses
    """
    if client is None:
        client = httpx.Client()

    if not is_serial_number_valid(serial_number):
        raise ValueError(f"Got invalid serial number {serial_number}.")

    jwt_token = os.environ.get("GIVENERGY_JWT_TOKEN")
    if jwt_token is None:
        raise ValueError("Environment variable GIVENERGY_JWT_TOKEN must provided.")

    validate_jwt(jwt_token, scope="api:inverter:data")

    unpacked: FullGivEnergyResponse = {
        "data": [GivEnergyDict({})],
        "links": {
            "next": f"https://api.givenergy.cloud/v1/inverter/{serial_number}/data-points/{timestamp.date().isoformat()}"
        },
    }

    all_data: list[GivEnergyDict] = []
    while unpacked.get("links", {}).get("next") is not None:
        url = unpacked["links"]["next"]
        resp = client.get(
            url,
            headers={"Authorization": f"Bearer {jwt_token}", "Content-Type": "application/json", "Accept": "application/json"},
            params={"pageSize": 100},
        )
        if resp.status_code != 200:
            if resp.json()["message"] == "Not Found":
                raise ValueError(
                    f"Couldn't find GivEnergy data for serial number {serial_number}." + " Is it the correct component?"
                )
            elif resp.json()["message"] == "This action is unauthorized.":
                raise ValueError(
                    f"Unauthorized for serial number {serial_number}." + " Is it the correct component?"
                )                
            raise ValueError(resp.text)

        unpacked = resp.json()

        all_data.extend(unpacked["data"])
    return all_data


def get_givenergy_data(
    serial_number: str, start_ts: datetime.datetime, end_ts: datetime.datetime, client: httpx.Client | None = None
) -> pd.DataFrame:
    """
    Get all the GivEnergy inverter data for a given inverter between two timestamps.

    Parameters
    ----------
    serial_number
        GivEnergy serial number of the inverter in the form AB1234C567
    start_ts
        Earliest timestamp to get data for (clips to day)
    end_ts
        Latest timestamp to get data for (clips to day)
    client
        HTTPX client to re-use if provided

    Returns
    -------
        Dataframe with GivEnergy data unpacked
    """
    if client is None:
        client = httpx.Client()

    entries = []
    for day in pd.date_range(start_ts, end_ts, freq=pd.Timedelta(days=1), normalize=True, tz=datetime.UTC, inclusive="both"):
        entries.extend(get_givenergy_day(day, serial_number=serial_number, client=client))

    return givenergy_records_to_dataframe(entries).sort_index().drop_duplicates()
