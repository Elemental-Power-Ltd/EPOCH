"""Optimisation service routers related to data management."""

import logging

from fastapi import APIRouter

from app.dependencies import HttpClientDep

router = APIRouter()
logger = logging.getLogger("default")


@router.post("/clear-bundle-cache")
async def clear_bundle_cache(http_client: HttpClientDep) -> str:
    """Clear the cache of bundle data, don't use unless you know what you're doing."""
    http_client.cache.clear()
    return "Cache Cleared."
