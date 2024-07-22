from enum import Enum
from typing import Annotated

import pydantic
from pydantic import BaseModel, Field

type dataset_id_t = Annotated[str, "String serialised UUID"]
type client_id_t = str
type site_id_t = str
type location_t = Annotated[str, "Name of the nearest city, e.g. Glasgow"]


class FuelEnum(str, Enum):
    gas = "gas"
    elec = "elec"
    oil = "oil"


class DatasetID(BaseModel):
    dataset_id: dataset_id_t

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "dataset_id": "805fb659-1cac-44f3-a1f9-85dc82178f53",
                }
            ]
        }
    }


class GasDatasetEntry(BaseModel):
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime
    consumption: float


class WeatherRequest(BaseModel):
    location: location_t = Field(example="London")
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime


class ClientID(BaseModel):
    client_id: client_id_t


class SiteID(BaseModel):
    site_id: site_id_t = Field(example="demo_matts_house")


class SiteIDWithTime(BaseModel):
    site_id: site_id_t = Field(example="demo_matts_house")
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime


class DatasetIDWithTime(BaseModel):
    dataset_id: dataset_id_t = Field(example="805fb659-1cac-44f3-a1f9-85dc82178f53")
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime
