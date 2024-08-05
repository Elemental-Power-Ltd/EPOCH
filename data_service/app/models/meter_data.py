"""Models associated with meter data endpoints, including gas and electricity."""
# ruff: noqa: D101

import pydantic

from .core import epoch_date_field, epoch_hour_of_year_field, epoch_start_time_field


class EpochElectricityEntry(pydantic.BaseModel):
    Date: str = epoch_date_field
    StartTime: str = epoch_start_time_field
    HourOfYear: float = epoch_hour_of_year_field
    FixLoad1: float = pydantic.Field(examples=[0.123, 4.56], description="Fixed electrical load for this building in kWh.")


class GasDatasetEntry(pydantic.BaseModel):
    start_ts: pydantic.AwareDatetime = pydantic.Field(
        examples=["2024-01-01T23:59:59Z"],
        description="The start time this period of consumption covers (inclusive)," + "often when this reading was taken.",
    )
    end_ts: pydantic.AwareDatetime = pydantic.Field(
        examples=["2024-05-31T00:00:00Z"],
        description="The end time this period of consumption covers (exclusive)," + "often when the next reading was taken.",
    )
    consumption: float = pydantic.Field(examples=[0.24567], description="Gas consumption measured in kWh. Can be null.")
