"""Models associated with meter data endpoints, including gas and electricity."""
# ruff: noqa: D101

import datetime
import enum
import uuid

import pydantic

from .core import FuelEnum, epoch_date_field, epoch_hour_of_year_field, epoch_start_time_field, site_id_field, site_id_t


class ReadingTypeEnum(str, enum.Enum):
    Customer = "manual"
    Automatic = "automatic"
    HalfHourly = "halfhourly"


class MeterMetadata(pydantic.BaseModel):
    dataset_id: pydantic.UUID4 = pydantic.Field(default_factory=uuid.uuid4)
    created_at: pydantic.AwareDatetime = pydantic.Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    site_id: site_id_t = site_id_field
    fuel_type: FuelEnum
    reading_type: ReadingTypeEnum
    filename: str | None = pydantic.Field(default=None)


class MeterEntry(pydantic.BaseModel):
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime
    consumption: float
    unit_cost: float | None = None
    total_cost: float | None = None


class MeterEntries(pydantic.BaseModel):
    metadata: MeterMetadata
    data: list[MeterEntry]


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
