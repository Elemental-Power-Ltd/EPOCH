import datetime

import pydantic
from pydantic import Field

from .core import dataset_id_t, site_id_field, site_id_t


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


class EpochHeatingEntry(pydantic.BaseModel):
    Date: str = pydantic.Field(examples=["Jan-01", "Dec-31"], pattern=r"[0-9][0-9]-[A-Za-z]*")
    StartTime: datetime.time = pydantic.Field(examples=["00:00", "13:30"])
    HourOfYear: float = pydantic.Field(examples=[1, 24 * 365 - 1])
    HLoad1: float = pydantic.Field(examples=[0.123, 4.56])
    DHWLoad1: float = pydantic.Field(examples=[0.123, 4.56])
