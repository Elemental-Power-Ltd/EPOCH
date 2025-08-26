import operator
import os
from datetime import datetime
from typing import cast

from pydantic import UUID7, AwareDatetime

from app.dependencies import CachedAsyncClient

_DB_URL = os.environ.get("EP_DATA_SERVICE_URL", "http://localhost:8762")


async def get_latest_bundle_id(
    site_id: str, start_ts: AwareDatetime, end_ts: AwareDatetime, http_client: CachedAsyncClient
) -> UUID7:
    """
    Get the bundle_id of the last created bundle with matching start timestamp.

    Parameters
    ----------
    site_id
        ID of the site.
    start_ts
        Start timestamp.
    end_ts
        End timestamp.
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
        Bundle ID.
    """
    data = {"site_id": site_id}
    bundles = await http_client.post(url=_DB_URL + "/list-dataset-bundles", data=data)
    matching_bundles = [
        bundle
        for bundle in bundles
        if datetime.fromisoformat(bundle["start_ts"]) == start_ts and datetime.fromisoformat(bundle["end_ts"]) == end_ts
    ]

    if not matching_bundles:
        raise ValueError(f"Unable to find a bundle with matching start and end timestamps: {start_ts}, {end_ts}")

    return cast(UUID7, max(matching_bundles, key=operator.itemgetter("created_at"))["bundle_id"])
