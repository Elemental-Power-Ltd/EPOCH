"""Models for electrical loads requests."""

# ruff: noqa: D101

import pydantic

from .core import DatasetIDWithTime, EpochEntry, dataset_id_t, final_uuid_field, RequestBase
from .meter_data import MeterMetadata


class ElectricalLoadRequest(RequestBase):
    dataset_id: dataset_id_t


class ElectricalLoadMetadata(MeterMetadata):
    pass


class EpochElectricityEntry(EpochEntry):
    data: list[float] = pydantic.Field(
        examples=[[0.123, 4.56]], description="List of fixed electrical loads for this building in kWh."
    )
