"""Main app entrypoint.

This function should import all the APIRouters you want to use, and handle all of the app-level
lifespan and request objects.
"""

import asyncio
import datetime
import sys
from collections.abc import Coroutine
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.site_manager import WorkerStatus

from .job_queue import current_job_id_ctx, current_job_type_ctx, started_at_ctx
from .lifespan import WORKERS, lifespan
from .routers import (
    air_source_heat_pump,
    carbon_intensity,
    client_data,
    electricity_load,
    heating_load,
    import_tariffs,
    meter_data,
    optimisation,
    renewables,
    site_manager,
    weather,
)

assert sys.version_info >= (3, 13, 0), f"Must be using Python 3.13.0 or above, but you're on {sys.version}"

start_time = datetime.datetime.now(tz=datetime.UTC)
app = FastAPI(lifespan=lifespan, title="Data Service", root_path="/api/data")
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(client_data.router)
app.include_router(meter_data.router)
app.include_router(weather.router)
app.include_router(heating_load.api_router)
app.include_router(renewables.router)
app.include_router(carbon_intensity.router)
app.include_router(optimisation.router)
app.include_router(air_source_heat_pump.router)
app.include_router(import_tariffs.router)
app.include_router(site_manager.router)
app.include_router(electricity_load.router)


@app.get("/list-queue-workers")
async def list_queue_workers(full: bool = True) -> list[WorkerStatus]:
    """
    Get the status of the workers in the queue.

    This will tell you if they're running, or their failing exception otherwise.
    This includes their internal task, if there is one

    Parameters
    ----------
    full
        If True, provide more debug info including the name of the task (probably `process_jobs`)
        and their context

    Returns
    -------
    list[WorkerStatus]
        Status of each worker including their current job.
    """

    def get_exception(t: asyncio.Task) -> str | None:
        """Get the current exception state of a task, or None if there isn't one."""
        try:
            return str(t.exception())
        except asyncio.InvalidStateError:
            return None

    def get_coro_name(coro: Coroutine[Any, Any, Any] | None) -> str | None:
        """Get the name of the running coroutine, or None if there isn't one."""
        if coro is None:
            return None
        return coro.__name__

    return [
        WorkerStatus(
            name=w.get_name(),
            exception=get_exception(w),
            is_running=not w.done(),
            coro=get_coro_name(w.get_coro()) if full else None,
            ctx={k.name: str(v) for k, v in w.get_context().items()} if full and w.get_context() is not None else None,
            current_job=w.get_context().get(current_job_type_ctx),
            current_job_id=w.get_context().get(current_job_id_ctx),
            started_at=w.get_context().get(started_at_ctx),
        )
        for w in WORKERS
    ]


@app.get("/")
async def root() -> dict[str, str | float]:
    """Endpoint for basic access to the API, to test that it's working."""
    return {
        "message": "Welcome to the Data Elemental backend API!",
        "system_uptime": (datetime.datetime.now(datetime.UTC) - start_time).total_seconds(),
    }
