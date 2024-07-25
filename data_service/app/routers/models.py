import datetime
from enum import Enum
from typing import Annotated

import pydantic
from pydantic import BaseModel, Field

dataset_id_t = Annotated[pydantic.UUID4, "String serialised UUID"]
client_id_t = str
site_id_t = str
location_t = Annotated[str, "Name of the nearest city, e.g. Glasgow"]


class FuelEnum(str, Enum):
    gas = "gas"
    elec = "elec"
    oil = "oil"


class ReadingTypeEnum(str, Enum):
    manual = "manual"
    automatic = "automatic"
    halfhourly = "halfhourly"


class DatasetID(BaseModel):
    dataset_id: dataset_id_t = Field(
        examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv4) of a dataset."
    )


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


class WeatherRequest(BaseModel):
    location: location_t = Field(
        examples=["London", "Cardiff"], description="The name of the nearest town or city that we'll use for weather data."
    )
    start_ts: pydantic.AwareDatetime = Field(
        examples=["2024-01-01T23:59:59Z"], description="The earliest time (inclusive) to retrieve weather data for."
    )
    end_ts: pydantic.AwareDatetime = Field(
        examples=["2024-05-31T00:00:00Z"], description="The latest time (exclusive) to retrieve weather data for."
    )


class ClientID(BaseModel):
    client_id: client_id_t = Field(
        examples=["demo", "demo"], description="The database key for clients, all lower case, no spaces."
    )


class SiteID(BaseModel):
    site_id: site_id_t = Field(
        examples=["demo_matts_house"], description="The database ID for a site, all lower case, joined by underscores."
    )


class SiteIDWithTime(BaseModel):
    site_id: site_id_t = Field(examples=["demo_matts_house"])
    start_ts: pydantic.AwareDatetime = Field(
        examples=["2024-01-01T23:59:59Z"], description="The earliest time (inclusive) to retrieve data for."
    )
    end_ts: pydantic.AwareDatetime = Field(
        examples=["2024-05-31T00:00:00Z"], description="The latest time (exclusive) to retrieve data for."
    )


class DatasetIDWithTime(BaseModel):
    dataset_id: dataset_id_t = Field(examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"])
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


class WeatherDatasetEntry(pydantic.BaseModel):
    timestamp: pydantic.AwareDatetime
    temp: float = Field(examples=[16.7], description="Air temperature at this time in °C.")
    humidity: float = Field(examples=[80.0], description="Relative humidity at this time in %.")
    solarradiation: float | None = Field(examples=[80.0, None], description="Horizontal olar radiation at this time in W / m2.")
    windspeed: float = Field(examples=[5.0], description="Windspeed at 2m in ms^-1")
    pressure: float | None = Field(examples=[998.0], description="Air pressure in mbar")


class HeatingLoadEntry(pydantic.BaseModel):
    timestamp: pydantic.AwareDatetime
    predicted: float | None = Field(examples=[0.512], description="Total predicted heating + DHW energy usage at this time.")
    dhw: float | None = Field(examples=[0.256], description="Predicted domestic hot water energy usage at this time.")
    heating: float | None = Field(examples=[0.256], description="Predicted heating usage at this time.")
    timedelta: datetime.timedelta = Field(
        examples=[1800.0],
        description="Length of time in seconds this reading covers, such that the"
        + "reading covers [timestamp, timestamp + timedelta]",
    )
    hdd: float | None = Field(examples=[0.01], description="Heating degree days due to external weather in this period.")

class ClientIdNamePair(pydantic.BaseModel):
    """
    A client_id, name pair.
    """

    client_id: client_id_t
    name: str


class DatasetEntry(pydantic.BaseModel):
    dataset_id: dataset_id_t
    reading_type: ReadingTypeEnum
    fuel_type: FuelEnum


class SiteIdNamePair(pydantic.BaseModel):
    site_id: site_id_t
    name: str


class ClientData(pydantic.BaseModel):
    client_id: client_id_t = pydantic.Field(examples=["demo", "demo"], pattern=r"^[0-9a-z_]+$")
    name: str = pydantic.Field(examples=["Demonstration", "Demonstration"])


class SiteData(pydantic.BaseModel):
    client_id: client_id_t = pydantic.Field(
        examples=["demo", "demo"],
        pattern=r"^[0-9a-z_]+$",
        description="Unique database client ID that this site is associated with.",
    )
    site_id: str = pydantic.Field(
        examples=["demo_london", "demo_offices"],
        pattern=r"^[0-9a-z_]+$",
        description="Unique database site ID that this site is associated with.",
    )
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
