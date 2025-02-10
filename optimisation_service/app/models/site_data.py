from enum import StrEnum
from os import PathLike
from typing import Annotated, Literal, TypedDict

from pydantic import UUID4, AwareDatetime, BaseModel, Field


class FileLoc(StrEnum):
    remote = "remote"
    local = "local"


class DataDuration(StrEnum):
    year = "year"


dataset_id_t = Annotated[UUID4, "String serialised UUID"]


class RemoteMetaData(BaseModel):
    loc: Literal[FileLoc.remote] = Field(
        examples=["remote"], description="Location of data. Either in local directory or in remote database."
    )
    site_id: str = Field(
        examples=["demo_london"],
        description="The database ID for a site, all lower case, joined by underscores.",
    )
    start_ts: AwareDatetime = Field(
        examples=["2022-01-01T00:00:00Z"],
        description="The earliest time (inclusive) to retrieve data for.",
    )
    end_ts: AwareDatetime = Field(
        examples=["2023-01-01T00:00:00Z"],
        description="The latest time (exclusive) to retrieve data for.",
    )
    HeatingLoad: dataset_id_t | list[dataset_id_t] | None = Field(default=None)
    ASHPData: dataset_id_t | None = Field(default=None)
    CarbonIntensity: dataset_id_t | None = Field(default=None)
    ElectricityMeterData: dataset_id_t | None = Field(default=None)
    ElectricityMeterDataSynthesised: dataset_id_t | None = Field(default=None)
    ImportTariff: dataset_id_t | list[dataset_id_t] | None = Field(default=None)
    Weather: dataset_id_t | None = Field(default=None)
    GasMeterData: dataset_id_t | None = Field(default=None)
    RenewablesGeneration: dataset_id_t | list[dataset_id_t] | None = Field(default=None)


class LocalMetaData(BaseModel):
    loc: Literal[FileLoc.local] = Field(
        examples=["local"], description="Location of data. Either in local directory or in remote database."
    )
    site_id: str = Field(
        examples=["demo_london"],
        description="The database ID for a site, all lower case, joined by underscores.",
    )
    path: PathLike = Field(examples=["./tests/data/benchmarks/var-3/InputData"], description="If a local file, the path to it.")


type RecordsList = list[dict[str, str | float | int]]


class ASHPResult(BaseModel):
    index: list[float]
    columns: list[float]
    data: list[list[float]]


class SiteDataEntries(TypedDict):
    eload: RecordsList
    heat: RecordsList
    ashp_input: ASHPResult
    ashp_output: ASHPResult
    import_tariffs: RecordsList
    grid_co2: RecordsList
    rgen: RecordsList


SiteMetaData = RemoteMetaData | LocalMetaData


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


class DatasetEntry(BaseModel):
    dataset_id: UUID4
    dataset_type: DatasetTypeEnum
    created_at: AwareDatetime
