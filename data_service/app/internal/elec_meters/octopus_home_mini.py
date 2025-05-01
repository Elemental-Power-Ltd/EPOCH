"""Get high resolution data from an Octopus Home Mini from their GraphQL api."""

import datetime
import itertools

import httpx
import pandas as pd

from ...epl_secrets import get_secrets_environment


async def get_octopus_jwt(http_client: httpx.AsyncClient) -> str:
    """
    Get a short lived JWT for usage in other Octopus GraphQL queries.

    Environment
    -----------
    EP_OCTOPUS_API_KEY
        Octopus API key from the secrets environment, starts with `sk_live...`

    Returns
    -------
        Stringified JWT
    """
    query = """mutation ObtainKrakenToken($input: ObtainJSONWebTokenInput!) {
    obtainKrakenToken(input: $input) {
        token
        payload
        refreshToken
        refreshExpiresIn
    }
    }"""
    response = await http_client.post(
        "https://api.octopus.energy/v1/graphql/",
        json={"query": query, "variables": {"input": {"APIKey": get_secrets_environment()["EP_OCTOPUS_API_KEY"]}}},
        headers={"Content-Type": "application/json"},
    )
    return str(response.json()["data"]["obtainKrakenToken"]["token"])


async def get_home_mini_id(account_id: str, http_client: httpx.AsyncClient) -> str | None:
    """
    Get the device ID of the Home Mini associated with this account.

    Parameters
    ----------
    account_id
        The ID of the Octopus account, starts `A-...`
    http_client

    Returns
    -------
    Device ID of the home mini, or None if there isn't one.
    """
    # TODO (2025-04-11 MHJB): this looks pretty graphql-injection risky
    # but passing the argument requires a mystery incantation that I don't
    # actually know, and this is only for internal use, so it's probably fine?
    query = (
        """
    query MyQuery
    {account(accountNumber: """
        + f'"{account_id}"'
        + """)
        {
            electricityAgreements(active: true)
            {
                meterPoint{
                    meters(includeInactive: false) {
                        smartDevices
                        {
                            deviceId
                        }
                    }
                }
            }
        }
    }
    """
    )
    token = await get_octopus_jwt(http_client)
    response = await http_client.post(
        "https://api.octopus.energy/v1/graphql/",
        json={"query": query},
        headers={"Content-Type": "application/json", "Authorization": token},
    )
    try:
        home_mini_id = response.json()["data"]["account"]["electricityAgreements"][0]["meterPoint"]["meters"][0][
            "smartDevices"
        ][0]["deviceId"]
        return str(home_mini_id)
    except KeyError:
        return None
    except IndexError:
        return None


async def get_home_mini_readings(
    home_mini_id: str, start_ts: datetime.datetime, end_ts: datetime.datetime, http_client: httpx.AsyncClient
) -> pd.DataFrame:
    """
    Get a set of 10s resolution readings from an Octopus Home Mini.

    This is very many readings, so make sure your start and end are close together!

    Parameters
    ----------
    home_mini_id
        Device ID of the home mini, retrieved from the API
    start_ts
        Earliest time to get data for
    end_ts
        Latest time to get data for

    Returns
    -------
    Pandas dataframe of consumption, export, demand, consumptionDelta readings.
    """
    query = """
    query SmartMeterTelemetry(
      $deviceId: String!,
      $start: DateTime,
      $end: DateTime,
      $grouping: TelemetryGrouping
    ) {
      smartMeterTelemetry(
        deviceId: $deviceId,
        start: $start,
        end: $end,
        grouping: $grouping
      ) {
        readAt
        consumption
        export
        demand
        consumptionDelta
      }
    }
    """
    all_data = []

    token = get_octopus_jwt(http_client)
    for start, end in itertools.pairwise(
        list(
            pd.date_range(
                start_ts,
                end_ts,
                freq=pd.Timedelta(hours=1),
            )
        )
    ):
        # Each batch is enormous, so iterate over hours of data to avoid thrashing the API.
        response = await http_client.post(
            "https://api.octopus.energy/v1/graphql/",
            json={
                "query": query,
                "variables": {
                    "deviceId": home_mini_id,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "grouping": "TEN_SECONDS",
                },
            },
            headers={"Content-Type": "application/json", "Authorization": str(token)},
        )
        data = response.json()["data"]["smartMeterTelemetry"]
        all_data.extend(data)

    # Turn this into a dataframe, with all the type conversions that entails.
    df = pd.DataFrame.from_records(all_data).rename(columns={"readAt": "start_ts"})
    df.start_ts = pd.to_datetime(df.start_ts)
    df.consumption = df.consumption.astype(float)
    df.export = df.export.astype(float)
    df.demand = df.demand.astype(float)
    df.consumptionDelta = df.consumptionDelta.astype(float)
    df = df.set_index(df.start_ts).sort_index()
    return df
