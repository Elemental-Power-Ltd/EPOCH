"""Models for endpoints in weather.py, mostly for VisualCrossing data."""

# ruff: noqa: D101
import datetime
from enum import StrEnum, auto
from typing import Self

import pydantic

from .core import location_t


class BaitAndModelCoefs(pydantic.BaseModel):
    solar_gain: float
    wind_chill: float
    humidity_discomfort: float
    smoothing: float
    threshold: float
    heating_kwh: float
    dhw_kwh: float
    r2_score: float


class WeatherDataProvider(StrEnum):
    """
    Which third party we want to get weather data from.

    If Auto, we'll prefer VisualCrossing if there's an API key and OpenMeteo if not.
    """

    Auto = auto()
    VisualCrossing = auto()
    OpenMeteo = auto()


class WeatherDatasetEntry(pydantic.BaseModel):
    timestamp: pydantic.AwareDatetime
    temp: float = pydantic.Field(examples=[16.7], description="Air temperature at this time in °C.")
    humidity: float = pydantic.Field(examples=[80.0], description="Relative humidity at this time in %.")
    solarradiation: float | None = pydantic.Field(
        examples=[80.0, None], description="Horizontal solar radiation at this time in W / m2."
    )
    windspeed: float = pydantic.Field(examples=[5.0], description="Windspeed at 2m in ms^-1")
    pressure: float | None = pydantic.Field(examples=[998.0], description="Air pressure in mbar")
    dniradiation: float | None = None
    difradiation: float | None = None
    cloudcover: float | None = None


class WeatherRequest(pydantic.BaseModel):
    provider: WeatherDataProvider = pydantic.Field(
        default=WeatherDataProvider.Auto,
        description="3rd party API to query for weather data. If auto, prefer VisualCrossing, but need an API keyy.",
    )
    location: location_t = pydantic.Field(
        examples=["London", "Cardiff"], description="The name of the nearest town or city that we'll use for weather data."
    )
    latitude: float | None = pydantic.Field(default=None, description="Used for OpenMeteo.")
    longitude: float | None = pydantic.Field(default=None, description="Used for OpenMeteo.")
    start_ts: pydantic.AwareDatetime = pydantic.Field(
        examples=["2024-01-01T23:59:59Z"], description="The earliest time (inclusive) to retrieve weather data for."
    )
    end_ts: pydantic.AwareDatetime = pydantic.Field(
        examples=["2024-05-31T00:00:00Z"], description="The latest time (exclusive) to retrieve weather data for."
    )

    @pydantic.model_validator(mode="after")
    def check_timestamps_valid(self) -> Self:
        """Check that the start timestamp is before the end timestamp, and that neither of them is in the future."""
        assert self.start_ts < self.end_ts, f"Start timestamp {self.start_ts} must be before end timestamp {self.end_ts}"
        assert self.start_ts <= datetime.datetime.now(datetime.UTC), f"Start timestamp {self.start_ts} must be in the past."
        assert self.end_ts <= datetime.datetime.now(datetime.UTC), f"End timestamp {self.end_ts} must be in the past."
        return self
