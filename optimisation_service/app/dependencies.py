import datetime
import typing
import urllib
from collections import OrderedDict
from collections.abc import Generator
from hashlib import sha256
from typing import Any

import httpx
from fastapi import Depends

from app.internal.database.utils import _DB_URL
from app.internal.queue import IQueue

type Jsonable = dict[str, Jsonable] | list[Jsonable] | str | int | float | bool | None

type HTTPClient = httpx.AsyncClient


def url_to_hash(url: str, params: dict[str, Any] | None = None, max_len: int | None = None) -> str:
    """
    Take a given URL and set of query params, and translate into a string SHA-256 hash.

    This is used in the test suite to store a specific query to a file, avoiding collisions and
    windows filename encoding problems.

    Parameters
    ----------
    url
        The URL you are sending a request to, ideally without query parameters
    params
        Any query parameters you're sending, as a dictionary with types friendly for `urllib.parse.urlencode`.
        These are ordered alphabetically by key for consistency.
    max_len
        The maximum number of characters in the string you want. If None, return all of them.

    Returns
    -------
        SHA-256 of the url and query parameters.
    """
    hasher = sha256()
    hasher.update(url.encode("utf-8"))
    if params:
        # We try to encode this as close to the actal URL encoding we'd send out over the wire as possible,
        # and sort them for consistency
        encoded_params = urllib.parse.urlencode({key: params[key] for key in sorted(params.keys())})
        hasher.update(encoded_params.encode("utf-8"))
    str_hash = str(hasher.hexdigest())
    if max_len is None:
        return str_hash

    return str_hash[:max_len]


class LRUCache:
    """
    Least Recently Used cache implementation.

    When the cache exceeds the maximum size, the least recently used item is automatically evicted.
    """

    def __init__(self, max_size=50):
        """
        Initialize the LRUCache.

        Parameters
        ----------
        max_size
            Maximum number of items the cache can hold.
        """
        self.max_size = max_size
        self.cache = OrderedDict()

    def get(self, key):
        """
        Retrieve an item from the cache.

        If the key exists, the item is marked as recently used (moved to the end).
        If the key does not exist, None is returned.

        Parameters
        ----------
        key
            The cache key.

        Returns
        -------
            The cached value if present, otherwise None.
        """
        if key not in self.cache:
            return None
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key, value):
        """
        Add or update an item in the cache.

        If the key already exists, its value is updated and it is marked as
        recently used. If adding a new item causes the cache to exceed its
        maximum size, the least recently used item is evicted.

        Parameters
        ----------
        key
            The cache key.
        value
            The value to store in the cache.
        """
        if key in self.cache:
            # Update and move to end
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            # Pop least recently used (first item)
            self.cache.popitem(last=False)


class CachedAsyncClient(httpx.AsyncClient):
    """Async HTTPX client with bundle caching."""

    def __init__(self, max_cache_size=50, **kwargs: Any):
        """
        Initialize the CachedAsyncClient.

        Parameters
        ----------
        max_cache_size
            Maximum number of responses to store in the cache. Defaults to 50.
        """
        self.cache = LRUCache(max_cache_size)
        super().__init__(**kwargs)

    async def post(self, url: str | httpx._urls.URL, **kwargs: Any) -> httpx._models.Response:
        """Post request with bundle caching."""
        if str(url) == _DB_URL + "/get-dataset-bundle":
            params = kwargs.get("params")
            key = url_to_hash(url=url, params=params)
            print(f"Cache key: {key}")
            cached = self.cache.get(key)
            if cached is not None:
                print("Key in cache")
                return cached

            print(f"Key not in cache: {self.cache.cache}")

            response = await super().post(url, params=params)
            self.cache.set(key, response)

            print(f"Added key to cache: {self.cache.cache}")
            return response

        return await super().post(url=url, **kwargs)


_HTTP_CLIENT: CachedAsyncClient | None = None


async def get_http_client() -> CachedAsyncClient:
    """
    Get a shared HTTP client.

    This is passed as a dependency to make the most use of connection and async
    pooling (i.e. everything goes through this client, so it has the most opportunity to schedule intelligently).
    """
    global _HTTP_CLIENT
    if _HTTP_CLIENT is None:
        http_limits = httpx.Limits(
            max_keepalive_connections=10000, keepalive_expiry=datetime.timedelta(seconds=30).total_seconds()
        )
        _HTTP_CLIENT = CachedAsyncClient(
            timeout=httpx.Timeout(
                pool=None,
                connect=datetime.timedelta(minutes=10).total_seconds(),
                read=datetime.timedelta(minutes=10).total_seconds(),
                write=None,
            ),
            limits=http_limits,
        )
    return _HTTP_CLIENT


_QUEUE: IQueue | None = None


def get_queue() -> Generator[IQueue]:
    """
    Get the queue with tasks in it.

    Returns
    -------
    IQueue
        An initialised, but maybe empty, job queue.
    """
    global _QUEUE
    if _QUEUE is None:
        _QUEUE = IQueue(maxsize=20)
    return _QUEUE


HttpClientDep = typing.Annotated[HTTPClient, Depends(get_http_client)]
QueueDep = typing.Annotated[IQueue, Depends(get_queue)]
