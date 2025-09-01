import datetime
import typing
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from fastapi import Depends

type Jsonable = dict[str, Jsonable] | list[Jsonable] | str | int | float | bool | None

type HTTPClient = httpx.AsyncClient


class CachedAsyncClient(httpx.AsyncClient):
    """Async HTTPX client with bundle caching."""

    async def post(self, url: str | httpx._urls.URL, **kwargs: Any) -> httpx._models.Response:
        """Post request with bundle caching."""
        return await super().post(url=url, **kwargs)


async def get_http_client() -> AsyncGenerator[CachedAsyncClient]:
    """
    Get a shared HTTP client.

    This is passed as a dependency to make the most use of connection and async
    pooling (i.e. everything goes through this client, so it has the most opportunity to schedule intelligently).
    """
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
    yield http_client


HttpClientDep = typing.Annotated[HTTPClient, Depends(get_http_client)]
