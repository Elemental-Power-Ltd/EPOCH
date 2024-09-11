"""Models for electrical loads requests."""

# ruff: noqa: D101
from typing import Literal

import pydantic

from .core import (
    FuelEnum,
    dataset_id_field,
    dataset_id_t,
    epoch_date_field,
    epoch_hour_of_year_field,
    epoch_start_time_field,
    site_id_field,
    site_id_t,
)


class ElectricalLoadRequest(pydantic.BaseModel):
    dataset_id: dataset_id_t = dataset_id_field
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime


class ElectricalLoadMetadata(pydantic.BaseModel):
    dataset_id: dataset_id_t = dataset_id_field
    created_at: pydantic.AwareDatetime
    site_id: site_id_t = site_id_field
    fuel_type: Literal[FuelEnum.elec]
    reading_type: str
    filename: str
    is_synthesised: bool


class EpochElectricityEntry(pydantic.BaseModel):
    Date: str = epoch_date_field
    StartTime: str = epoch_start_time_field
    HourOfYear: float = epoch_hour_of_year_field
    FixLoad1: float = pydantic.Field(examples=[0.123, 4.56], description="Fixed electrical load for this building in kWh.")
