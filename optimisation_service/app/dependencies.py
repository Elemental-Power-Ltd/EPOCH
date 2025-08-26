import datetime
from collections.abc import AsyncGenerator
from typing import Any

import httpx

type Jsonable = dict[str, Jsonable] | list[Jsonable] | str | int | float | bool | None

type HTTPClient = httpx.AsyncClient


class CachedAsyncClient(httpx.AsyncClient):
    """Async HTTPX client with bundle caching."""

    async def post(self, url: str, **kwargs: Any) -> Jsonable:
        """Post request with bundle cachine."""
        await super().post(url=url)


# These limits are enormous to make sure that we don't saturate the AsyncConnnections
# https://github.com/encode/httpx/discussions/3084
http_limits = httpx.Limits(max_keepalive_connections=10000, keepalive_expiry=datetime.timedelta(seconds=30).total_seconds())
http_client = CachedAsyncClient(
    timeout=httpx.Timeout(
        pool=None,
        connect=datetime.timedelta(minutes=10).total_seconds(),
        read=datetime.timedelta(minutes=10).total_seconds(),
        write=None,
    ),
    limits=http_limits,
)


async def get_http_client() -> AsyncGenerator[HTTPClient]:
    """
    Get a shared HTTP client.

    This is passed as a dependency to make the most use of connection and async
    pooling (i.e. everything goes through this client, so it has the most opportunity to schedule intelligently).
    """
    yield http_client
