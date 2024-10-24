from enum import StrEnum
from os import PathLike
from typing import Literal, TypedDict

from pydantic import UUID4, AwareDatetime, BaseModel, Field


class FileLoc(StrEnum):
    remote = "remote"
    local = "local"


class DataDuration(StrEnum):
    year = "year"


class RemoteMetaData(BaseModel):
    loc: Literal[FileLoc.remote] = Field(
        examples=["remote"], description="Location of data. Either in local directory or in remote database."
    )
    site_id: str = Field(
        examples=["demo_london"],
        description="The database ID for a site, all lower case, joined by underscores.",
    )
    start_ts: AwareDatetime = Field(description="Datetime to retrieve data from. Only relevant for remote files.")
    duration: DataDuration = Field(description="Length of time to retrieve data for. Only relevant for remote files.")
    dataset_ids: dict[str, UUID4] = Field(default={}, description="Specific dataset IDs to fetch.")


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
