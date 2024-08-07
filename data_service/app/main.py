"""Main app entrypoint.

This function should import all the APIRouters you want to use, and handle all of the app-level
lifespan and request objects.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Awaitable, Callable, Never

import asyncpg
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    air_source_heat_pump,
    carbon_intensity,
    client_data,
    heating_load,
    meter_data,
    optimisation,
    renewables,
    weather,
)


class Database:
    """Shared database object that we'll re-use throughout the lifetime of this API."""

    async def create_pool(self) -> None:
        """Create the PostgreSQL connection pool.

        For a given endpoint, use `pool.acquire()` to get an entry from this pool
        and speed things up.

        You can specify the database via the DATABASE_URL environment variable, or it falls back
        to a locally hosted version of Elemental DB if not.
        """
        self.pool = await asyncpg.create_pool(
            dsn=os.environ.get("DATABASE_URL", "postgresql://python:elemental@localhost/elementaldb")
        )


db = Database()

http_client = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[Never]:
    """Set up a long clients: a database pool and an HTTP client."""
    # Startup events
    await db.create_pool()
    global http_client
    http_client = httpx.AsyncClient()
    yield  # type: ignore
    await http_client.aclose()


app = FastAPI(lifespan=lifespan)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """
    Set up the database connection pool as part of the request object.

    This will populate the `request.state` object, and if you want to access it
    then pass a `request: Request` parameter into each of your endpoints.
    Then the connection pool is available as the `request.state.pgpool` parameter.
    """
    request.state.pgpool = db.pool
    request.state.http_client = http_client
    response = await call_next(request)
    return response


app.include_router(client_data.router)
app.include_router(meter_data.router)
app.include_router(weather.router)
app.include_router(heating_load.router)
app.include_router(renewables.router)
app.include_router(carbon_intensity.router)
app.include_router(optimisation.router)
app.include_router(air_source_heat_pump.router)


@app.get("/")
async def root() -> dict[str, str]:  # noqa: RUF029
    """Endpoint for basic access to the API, to test that it's working."""
    return {"message": "Welcome to the Data Elemental backend API!"}
