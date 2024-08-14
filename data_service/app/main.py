"""Main app entrypoint.

This function should import all the APIRouters you want to use, and handle all of the app-level
lifespan and request objects.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import lifespan
from .routers import (
    air_source_heat_pump,
    carbon_intensity,
    client_data,
    heating_load,
    import_tariffs,
    meter_data,
    optimisation,
    renewables,
    weather,
)

app = FastAPI(lifespan=lifespan)
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
app.include_router(heating_load.router)
app.include_router(renewables.router)
app.include_router(carbon_intensity.router)
app.include_router(optimisation.router)
app.include_router(air_source_heat_pump.router)
app.include_router(import_tariffs.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Endpoint for basic access to the API, to test that it's working."""
    return {"message": "Welcome to the Data Elemental backend API!"}
