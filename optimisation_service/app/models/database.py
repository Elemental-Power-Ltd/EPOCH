from enum import StrEnum
from typing import Annotated

from pydantic import UUID4, AwareDatetime, BaseModel, Field

dataset_id_field = Field(
    examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv4) of a dataset."
)
dataset_id_t = Annotated[UUID4, "String serialised UUID"]
site_id_t = str


class DatasetIDWithTime(BaseModel):
    dataset_id: dataset_id_t = dataset_id_field
    start_ts: AwareDatetime = Field(
        examples=["2024-01-01T00:00:00Z"],
        description="The earliest time (inclusive) to retrieve data for.",
    )
    end_ts: AwareDatetime = Field(
        examples=["2024-05-31T00:00:00Z"],
        description="The latest time (exclusive) to retrieve data for.",
    )


class DatasetTypeEnum(StrEnum):
    GasMeterData = "GasMeterData"
    ElectricityMeterData = "ElectricityMeterData"
    ElectricityMeterDataSynthesised = "ElectricityMeterDataSynthesised"
    RenewablesGeneration = "RenewablesGeneration"
    Weather = "Weather"
    CarbonIntensity = "CarbonIntensity"
    HeatingLoad = "HeatingLoad"
    ASHPData = "ASHPData"
    ImportTariff = "ImportTariff"
