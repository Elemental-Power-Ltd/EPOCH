"""
Shared models and descriptive fields for multiple endpoints.

If a pydantic model is used in multiple places or has similar descriptions,
centralise it in here.
"""

# ruff: noqa: D101
import datetime
from enum import Enum
from typing import Annotated, Self

import pydantic
from pydantic import BaseModel, Field

dataset_id_t = Annotated[pydantic.UUID4, "String serialised UUID"]
client_id_t = str
site_id_t = str
location_t = Annotated[str, "Name of the nearest city, e.g. Glasgow"]

example_start_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
example_end_ts = datetime.datetime(year=2021, month=1, day=1, tzinfo=datetime.UTC)
site_id_field = Field(
    examples=["demo_matts_house"],
    pattern=r"^[0-9a-z_]+$",
    description="The database ID for a site, all lower case, joined by underscores.",
)

client_id_field = Field(
    examples=["demo", "demo"],
    pattern=r"^[0-9a-z_]+$",
    description="The database ID for a client, all lower case, joined by underscores.",
)

dataset_id_field = Field(
    examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv4) of a dataset."
)

epoch_start_time_field = Field(
    examples=["00:00", "11:30"],
    description="Starting time for this data, often 30 mins or 1 hour long from now.",
    pattern=r"[0-2][0-9]:[0-6][0-9]",
)

epoch_hour_of_year_field = Field(
    examples=[1, 365 * 24 - 1],
    description="Hour of the year, 1-indexed for EPOCH. Counts up even over timezone changes."
    + "For example, Jan 1st 00:00 is 1.",
)

epoch_date_field = Field(
    examples=["01-Jan", "31-Dec"],
    description="Date string for EPOCH to consume, zero padded day first"
    + "and 3 letter month abbreviation second."
    + "No year information is provided (be careful!). This is originally Excel-like.",
    pattern=r"[0-9][0-9]-[A-Za-z]*",
)


class FuelEnum(str, Enum):
    gas = "gas"
    elec = "elec"
    oil = "oil"


class ReadingTypeEnum(str, Enum):
    manual = "manual"
    automatic = "automatic"
    halfhourly = "halfhourly"
    oil = "oil"
    solar_pv = "solar_pv"
    tariff = "tariff"
    heating_load = "heating_load"


class DatasetID(BaseModel):
    dataset_id: dataset_id_t = dataset_id_field


class ClientID(BaseModel):
    client_id: client_id_t = client_id_field


class SiteID(BaseModel):
    site_id: site_id_t = site_id_field


class SiteIDWithTime(BaseModel):
    site_id: site_id_t = Field(examples=["demo_london"])
    start_ts: pydantic.AwareDatetime = Field(
        examples=["2024-01-01T00:00:00Z"], description="The earliest time (inclusive) to retrieve data for."
    )
    end_ts: pydantic.AwareDatetime = Field(
        examples=["2024-05-31T00:00:00Z"], description="The latest time (exclusive) to retrieve data for."
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


class ClientIdNamePair(pydantic.BaseModel):
    """A client_id, name pair."""

    client_id: client_id_t = client_id_field
    name: str = Field(examples=["Demonstration", "Demonstration"], description="Human readable client name")


class DatasetEntry(pydantic.BaseModel):
    dataset_id: dataset_id_t = dataset_id_field
    reading_type: ReadingTypeEnum
    fuel_type: FuelEnum


class SiteIdNamePair(pydantic.BaseModel):
    site_id: site_id_t = site_id_field
    name: str = Field(examples=["Demonstration - Matt's House"], description="Human-readable name of this site.")


class ClientData(pydantic.BaseModel):
    client_id: client_id_t = client_id_field
    name: str = pydantic.Field(examples=["Demonstration", "Demonstration"])


class SiteData(pydantic.BaseModel):
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
        examples=["27 Mill Close, London, SW1A 0AA", "Queens Buildings, Potter Street, Worksop, S80 2AH"]
    )
