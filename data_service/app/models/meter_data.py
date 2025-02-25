"""Models associated with meter data endpoints, including gas and electricity."""
# ruff: noqa: D101

import datetime
from enum import StrEnum

import pydantic

from .core import FuelEnum, dataset_id_field, dataset_id_t, site_id_field, site_id_t


class ReadingTypeEnum(StrEnum):
    Customer = "manual"
    Automatic = "automatic"
    HalfHourly = "halfhourly"


class MeterMetadata(pydantic.BaseModel):
    dataset_id: dataset_id_t = dataset_id_field
    created_at: pydantic.AwareDatetime = pydantic.Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    site_id: site_id_t = site_id_field
    fuel_type: FuelEnum
    reading_type: ReadingTypeEnum
    filename: str | None = pydantic.Field(default=None)
    is_synthesised: bool = pydantic.Field(default=False)
    start_ts: pydantic.AwareDatetime | None = pydantic.Field(default=None)
    end_ts: pydantic.AwareDatetime | None = pydantic.Field(default=None)


class MeterEntry(pydantic.BaseModel):
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime
    consumption: float
    unit_cost: float | None = None
    total_cost: float | None = None


class MeterEntries(pydantic.BaseModel):
    metadata: MeterMetadata
    data: list[MeterEntry]


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
