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
    FixLoad1: float = pydantic.Field(examples=[0.123, 4.56], description="Fixed electrical load for this building in kWh.")
