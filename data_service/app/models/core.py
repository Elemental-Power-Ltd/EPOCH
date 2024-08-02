import datetime
from enum import Enum
from typing import Annotated

import pydantic
from pydantic import BaseModel, Field

dataset_id_t = Annotated[pydantic.UUID4, "String serialised UUID"]
client_id_t = str
site_id_t = str
location_t = Annotated[str, "Name of the nearest city, e.g. Glasgow"]

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


class GasDatasetEntry(BaseModel):
    start_ts: pydantic.AwareDatetime = Field(
        examples=["2024-01-01T23:59:59Z"],
        description="The start time this period of consumption covers (inclusive)," + "often when this reading was taken.",
    )
    end_ts: pydantic.AwareDatetime = Field(
        examples=["2024-05-31T00:00:00Z"],
        description="The end time this period of consumption covers (exclusive)," + "often when the next reading was taken.",
    )
    consumption: float = Field(examples=[0.24567], description="Gas consumption measured in kWh. Can be null.")


class ClientID(BaseModel):
    client_id: client_id_t = client_id_field


class SiteID(BaseModel):
    site_id: site_id_t = site_id_field


class SiteIDWithTime(BaseModel):
    site_id: site_id_t = Field(examples=["demo_london"])
    start_ts: pydantic.AwareDatetime = Field(
        examples=["2024-01-01T23:59:59Z"], description="The earliest time (inclusive) to retrieve data for."
    )
    end_ts: pydantic.AwareDatetime = Field(
        examples=["2024-05-31T00:00:00Z"], description="The latest time (exclusive) to retrieve data for."
    )


class DatasetIDWithTime(BaseModel):
    dataset_id: dataset_id_t = dataset_id_field
    start_ts: pydantic.AwareDatetime = Field(
        examples=["2024-01-01T23:59:59Z"],
        description="The earliest time (inclusive) to retrieve data for.",
        default=datetime.datetime(year=1970, month=1, day=1, tzinfo=datetime.UTC),
    )
    end_ts: pydantic.AwareDatetime = Field(
        examples=["2024-05-31T00:00:00Z"],
        description="The latest time (exclusive) to retrieve data for.",
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
    )


class ClientIdNamePair(pydantic.BaseModel):
    """
    A client_id, name pair.
    """

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
