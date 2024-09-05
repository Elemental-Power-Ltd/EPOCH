"""Models for endpoints in heating_load.py, including DHW and heating load."""

# ruff: noqa: D101
import datetime
from enum import Enum
from typing import Self

import pydantic
from pydantic import Field

from .core import EpochEntry, dataset_id_t, site_id_field, site_id_t, dataset_id_field

class InterventionEnum(str, Enum):
    Loft = "loft"
    DoubleGlazing = "double_glazing"
    Cladding = "cladding"

class HeatingLoadEntry(pydantic.BaseModel):
    timestamp: pydantic.AwareDatetime = pydantic.Field(
        examples=["2024-07-30T14:00:00Z"],
        description="Starting timestamp this reading covers."
        + "You can construct the usual (start_ts, end_ts) pairs by using the timedelta field.",
    )
    predicted: float | None = Field(examples=[0.512], description="Total predicted heating + DHW energy usage at this time.")
    dhw: float | None = Field(examples=[0.256], description="Predicted domestic hot water energy usage at this time.")
    heating: float | None = Field(examples=[0.256], description="Predicted heating usage at this time.")
    timedelta: datetime.timedelta = Field(
        examples=[1800.0],
        description="Length of time in seconds this reading covers, such that the"
        + "reading covers [timestamp, timestamp + timedelta]",
    )
    hdd: float | None = Field(examples=[0.01], description="Heating degree days due to external weather in this period.")


class HeatingLoadMetadata(pydantic.BaseModel):
    site_id: site_id_t = site_id_field
    dataset_id: dataset_id_t = Field(description="UUID for heating load")
    created_at: pydantic.AwareDatetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        examples=["2024-07-30T14:13:00Z"],
        description="The time this dataset was created",
    )
    params: pydantic.Json = Field(
        examples=["{'source_dataset': '...'}"],
        description="Parameters used to generate this dataset, for example the original dataset.",
    )
    interventions: list[InterventionEnum] = Field(examples=["Loft"], default=[])


class EpochHeatingEntry(EpochEntry):
    HLoad1: float = pydantic.Field(examples=[0.123, 4.56], description="Heating demand in kWh for this time period.")
    DHWLoad1: float = pydantic.Field(
        examples=[0.123, 4.56], description="Domestic hot water demand in kWh for this time period."
    )
    HLoad2: float | None = pydantic.Field(
        default=None, examples=[0.123, 4.56], description="Heating demand in kWh for this time period."
    )
    DHWLoad2: float | None = pydantic.Field(
        default=None, examples=[0.123, 4.56], description="Domestic hot water demand in kWh for this time period."
    )
    HLoad3: float | None = pydantic.Field(
        default=None, examples=[0.123, 4.56], description="Heating demand in kWh for this time period."
    )
    DHWLoad3: float | None = pydantic.Field(
        default=None, examples=[0.123, 4.56], description="Domestic hot water demand in kWh for this time period."
    )
    HLoad4: float | None = pydantic.Field(
        default=None, examples=[0.123, 4.56], description="Heating demand in kWh for this time period."
    )
    DHWLoad4: float | None = pydantic.Field(
        default=None, examples=[0.123, 4.56], description="Domestic hot water demand in kWh for this time period."
    )
    AirTemp: float = pydantic.Field(examples=[16.7], description="Air temperature at this time in °C.")


class HeatingLoadRequest(pydantic.BaseModel):
    dataset_id: dataset_id_t = dataset_id_field
    start_ts: pydantic.AwareDatetime = Field(
        examples=["2024-01-01T00:00:00Z"],
        description="The earliest time (inclusive) to retrieve data for.",
        default=datetime.datetime(year=1970, month=1, day=1, tzinfo=datetime.UTC),
    )
    end_ts: pydantic.AwareDatetime = Field(
        examples=["2024-05-31T00:00:00Z"],
        description="The latest time (exclusive) to retrieve data for.",
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
    )
    interventions: list[InterventionEnum] = Field(
        examples=[[InterventionEnum.Loft], []],
        default=[],
        description="Single energy saving intervention to make for this site.",
    )

    @pydantic.model_validator(mode="after")
    def check_timestamps_valid(self) -> Self:
        """Check that the start timestamp is before the end timestamp, and that neither of them is in the future."""
        assert self.start_ts < self.end_ts, f"Start timestamp {self.start_ts} must be before end timestamp {self.end_ts}"
        assert self.start_ts <= datetime.datetime.now(datetime.UTC), f"Start timestamp {self.start_ts} must be in the past."
        assert self.end_ts <= datetime.datetime.now(datetime.UTC), f"End timestamp {self.end_ts} must be in the past."
        return self


class InterventionCostRequest(pydantic.BaseModel):
    interventions: list[InterventionEnum] = pydantic.Field(default=[])
    site_id: site_id_t = site_id_field


class InterventionCostResult(pydantic.BaseModel):
    breakdown: dict[InterventionEnum, float]
    total: float
