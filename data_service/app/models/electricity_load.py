"""Models for electrical loads requests."""

# ruff: noqa: D101

import pydantic

from .core import DatasetIDWithTime, EpochEntry
from .meter_data import MeterMetadata


class ElectricalLoadRequest(DatasetIDWithTime):
    pass


class ElectricalLoadMetadata(MeterMetadata):
    pass


class EpochElectricityEntry(EpochEntry):
    data: list[float] = pydantic.Field(
        examples=[[0.123, 4.56]], description="List of fixed electrical loads for this building in kWh."
    )
