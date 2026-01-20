"""
Shared models and descriptive fields for multiple endpoints.

If a pydantic model is used in multiple places or has similar descriptions,
centralise it in here.
"""

# ruff: noqa: D101
import datetime
import re
from enum import StrEnum
from typing import Annotated, Any, Self

import pydantic
from pydantic import BaseModel, Field

from app.internal.utils.uuid import uuid7

# We have to support either UUID4 for historic datasets or UUID7 for more recent dataset
type uuid_t = pydantic.UUID4 | pydantic.UUID7
type dataset_id_t = Annotated[uuid_t, "String serialised UUID"]
type client_id_t = str
type site_id_t = str
type location_t = Annotated[str, "Name of the nearest city, e.g. Glasgow"]

POSTCODE_REGEX = re.compile(r".*, [A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$")

example_start_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
example_end_ts = datetime.datetime(year=2021, month=1, day=1, tzinfo=datetime.UTC)
site_id_field = Field(
    examples=["demo_london"],
    pattern=r"^[0-9a-z_]+$",
    description="The database ID for a site, all lower case, joined by underscores.",
)

client_id_field = Field(
    examples=["demo", "demo"],
    pattern=r"^[0-9a-z_]+$",
    description="The database ID for a client, all lower case, joined by underscores.",
)

dataset_id_field = Field(
    examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"],
    description="Unique ID (generally a UUIDv4) of a dataset.",
    default_factory=uuid7,
)


class FuelEnum(StrEnum):
    gas = "gas"
    elec = "elec"
    oil = "oil"


class ResultID(BaseModel):
    result_id: dataset_id_t


class TaskID(BaseModel):
    task_id: dataset_id_t


class DatasetID(BaseModel):
    dataset_id: dataset_id_t = dataset_id_field


class ClientID(BaseModel):
    client_id: client_id_t = client_id_field


class SiteID(BaseModel):
    site_id: site_id_t = site_id_field


class EpochEntry(pydantic.BaseModel):
    timestamps: list[pydantic.AwareDatetime]


class SiteIDWithTime(SiteID):
    """A model for getting data for a site between two timestamps."""

    start_ts: pydantic.AwareDatetime = Field(
        examples=["2024-01-01T00:00:00Z"],
        description="The earliest time (inclusive) to retrieve data for.",
    )
    end_ts: pydantic.AwareDatetime = Field(
        examples=["2024-05-31T00:00:00Z"],
        description="The latest time (exclusive) to retrieve data for.",
    )

    @pydantic.model_validator(mode="after")
    def check_timestamps_valid(self) -> Self:
        """Check that the start timestamp is before the end timestamp, and that neither of them is in the future."""
        assert self.start_ts < self.end_ts, f"Start timestamp {self.start_ts} must be before end timestamp {self.end_ts}"
        assert self.start_ts <= datetime.datetime.now(datetime.UTC), f"Start timestamp {self.start_ts} must be in the past."
        assert self.end_ts <= datetime.datetime.now(datetime.UTC), f"End timestamp {self.end_ts} must be in the past."
        return self


class DatasetIDWithTime(BaseModel):
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

    @pydantic.model_validator(mode="after")
    def check_timestamps_valid(self) -> Self:
        """Check that the start timestamp is before the end timestamp, and that neither of them is in the future."""
        assert self.start_ts < self.end_ts, f"Start timestamp {self.start_ts} must be before end timestamp {self.end_ts}"
        assert self.start_ts <= datetime.datetime.now(datetime.UTC), f"Start timestamp {self.start_ts} must be in the past."
        assert self.end_ts <= datetime.datetime.now(datetime.UTC), f"End timestamp {self.end_ts} must be in the past."
        return self


class MultipleDatasetIDWithTime(BaseModel):
    dataset_id: list[dataset_id_t] = pydantic.Field(examples=[uuid7(), [uuid7() for _ in range(4)]])
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

    @pydantic.field_validator("dataset_id", mode="before")
    @classmethod
    def check_dataset_list(cls, v: dataset_id_t | list[dataset_id_t]) -> list[dataset_id_t]:
        """Check if we've got a list of datasets, and if we got just one, make it a list."""
        if not isinstance(v, list):
            v = [v]
        return v

    @pydantic.model_validator(mode="after")
    def check_timestamps_valid(self) -> Self:
        """Check that the start timestamp is before the end timestamp, and that neither of them is in the future."""
        assert self.start_ts < self.end_ts, f"Start timestamp {self.start_ts} must be before end timestamp {self.end_ts}"
        assert self.start_ts <= datetime.datetime.now(datetime.UTC), f"Start timestamp {self.start_ts} must be in the past."
        assert self.end_ts <= datetime.datetime.now(datetime.UTC), f"End timestamp {self.end_ts} must be in the past."
        return self


class ClientIdNamePair(pydantic.BaseModel):
    """A client_id, name pair."""

    client_id: client_id_t = client_id_field
    name: str = Field(examples=["Demonstration", "Demonstration"], description="Human readable client name")


class DatasetTypeEnum(StrEnum):
    SiteBaseline = "SiteBaseline"
    GasMeterData = "GasMeterData"
    ElectricityMeterData = "ElectricityMeterData"
    ElectricityMeterDataSynthesised = "ElectricityMeterDataSynthesised"
    RenewablesGeneration = "RenewablesGeneration"
    Weather = "Weather"
    CarbonIntensity = "CarbonIntensity"
    HeatingLoad = "HeatingLoad"
    ASHPData = "ASHPData"
    ImportTariff = "ImportTariff"
    ThermalModel = "ThermalModel"
    PHPP = "PHPP"


class DatasetEntry(pydantic.BaseModel):
    dataset_id: dataset_id_t = dataset_id_field
    dataset_type: DatasetTypeEnum
    created_at: pydantic.AwareDatetime
    start_ts: pydantic.AwareDatetime | None = None
    end_ts: pydantic.AwareDatetime | None = None
    num_entries: int | None = None
    resolution: datetime.timedelta | None = Field(
        examples=[datetime.timedelta(minutes=30), datetime.timedelta(days=28)],
        default=None,
        description="Average time span between entries in this dataset.",
    )
    dataset_subtype: Any | None = Field(
        description="Subtype of this dataset, e.g. SyntheticTariff types, if available.", default=None
    )


class SiteIdNamePair(pydantic.BaseModel):
    site_id: site_id_t = site_id_field
    name: str = Field(examples=["Demonstration - Matt's House"], description="Human-readable name of this site.")


class ClientData(pydantic.BaseModel):
    client_id: client_id_t = client_id_field
    name: str = pydantic.Field(examples=["Demonstration", "Demonstration"])


class SiteData(pydantic.BaseModel):
    """Metadata about a specific site from the database."""

    client_id: client_id_t = client_id_field
    site_id: str = site_id_field
    name: str = pydantic.Field(
        examples=["Demo - London", "Demonstration Offices"], description="Human readable name of this site"
    )
    location: str = pydantic.Field(
        examples=["London", "Worksop"], description="Nearest town or weather station to this site."
    )
    coordinates: tuple[float, float] = pydantic.Field(
        examples=[(51.499669471331015, -0.1248477037277857884), (51.46347923229967686, -3.162713781953953301)]
    )
    address: str = pydantic.Field(
        description="Street address, must end with a comma followed by the postcode.",
        examples=["27 Mill Close, London, SW1A 0AA", "Queens Buildings, Potter Street, Worksop, S80 2AH"],
    )
    epc_lmk: str | None = pydantic.Field(
        description="LMK for the latest Commercial Energy Performance Certificate for this building", default=None
    )
    dec_lmk: str | None = pydantic.Field(
        description="LMK for the latest Commercial Display Energy Certificate for this building", default=None
    )

    @pydantic.field_validator("address", mode="after")
    @classmethod
    def check_ends_with_postcode(cls, addr: str) -> str:
        """Check if we got an address that ends with a postcode."""
        if not POSTCODE_REGEX.match(addr):
            raise ValueError("Didn't find a postcode after a comma at the end of your address, does it end ',AB1, 2CD'?")
        return addr


class BundleEntryMetadata(pydantic.BaseModel):
    bundle_id: dataset_id_t = pydantic.Field(description="ID of the linked bundle that this is part of.")
    dataset_id: dataset_id_t = pydantic.Field(description="ID for this individual dataset within the bundle.")
    dataset_type: DatasetTypeEnum = pydantic.Field(description="Type of dataset this is, such as ElectricityMeterData")
    dataset_subtype: Any | None = pydantic.Field(
        default=None,
        description="JSON serialisable subtype for this dataset, maybe a solar location or tariff type. Defaults to None.",
    )
    dataset_order: int | None = pydantic.Field(
        description="Order of these datasets within the bundle; especially useful for sorting subtypes such as import tariffs.",
        default=None,
    )


class RequestBase(pydantic.BaseModel):
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime

    bundle_metadata: BundleEntryMetadata | None = None

    @pydantic.model_validator(mode="after")
    def check_timestamps_valid(self) -> Self:
        """Check that the start timestamp is before the end timestamp, and that neither of them is in the future."""
        assert self.start_ts < self.end_ts, f"Start timestamp {self.start_ts} must be before end timestamp {self.end_ts}"
        assert self.start_ts <= datetime.datetime.now(datetime.UTC), f"Start timestamp {self.start_ts} must be in the past."
        assert self.end_ts <= datetime.datetime.now(datetime.UTC), f"End timestamp {self.end_ts} must be in the past."
        return self
