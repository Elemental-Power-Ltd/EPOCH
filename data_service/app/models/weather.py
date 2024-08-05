"""Models for endpoints in weather.py, mostly for VisualCrossing data."""

# ruff: noqa: D101
import pydantic

from .core import location_t


class WeatherDatasetEntry(pydantic.BaseModel):
    timestamp: pydantic.AwareDatetime
    temp: float = pydantic.Field(examples=[16.7], description="Air temperature at this time in °C.")
    humidity: float = pydantic.Field(examples=[80.0], description="Relative humidity at this time in %.")
    solarradiation: float | None = pydantic.Field(
        examples=[80.0, None], description="Horizontal solar radiation at this time in W / m2."
    )
    windspeed: float = pydantic.Field(examples=[5.0], description="Windspeed at 2m in ms^-1")
    pressure: float | None = pydantic.Field(examples=[998.0], description="Air pressure in mbar")


class WeatherRequest(pydantic.BaseModel):
    location: location_t = pydantic.Field(
        examples=["London", "Cardiff"], description="The name of the nearest town or city that we'll use for weather data."
    )
    start_ts: pydantic.AwareDatetime = pydantic.Field(
        examples=["2024-01-01T23:59:59Z"], description="The earliest time (inclusive) to retrieve weather data for."
    )
    end_ts: pydantic.AwareDatetime = pydantic.Field(
        examples=["2024-05-31T00:00:00Z"], description="The latest time (exclusive) to retrieve weather data for."
    )
