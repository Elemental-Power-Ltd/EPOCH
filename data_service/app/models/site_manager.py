"""Models for site manager, handling requesting datasets."""

# ruff: noqa: D101

import datetime
from enum import StrEnum
from typing import Literal

import pydantic

from .core import DatasetEntry, dataset_id_t, site_id_field, site_id_t


class FileLocationEnum(StrEnum):
    local = "local"
    remote = "remote"


class DataDuration(StrEnum):
    year = "year"


class LocalMetaData(pydantic.BaseModel):
    loc: Literal[FileLocationEnum.local] = pydantic.Field(
        default=FileLocationEnum.local,
        examples=["local"],
        description="Where we are getting the data from, either a local file or remote DB.",
    )
    site_id: site_id_t = site_id_field
    path: pydantic.FilePath | str = pydantic.Field(
        examples=["./tests/data/benchmarks/var-3/InputData"], description="If a local file, the path to it."
    )


class DatasetList(pydantic.BaseModel):
    """
    Collection of available datasets in the database.

    These come as a list of DatasetEntries or single dataset entries, or None if there's nothing available.
    For list-latest-datasets, these will tend to be single entries except for the specific cases like tariffs where
    you want multiple.
    Each individual dataset entry comes with some useful metadata.
    """

    site_id: site_id_t
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime
    HeatingLoad: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    ASHPData: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    CarbonIntensity: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    ElectricityMeterData: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    ElectricityMeterDataSynthesised: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    ImportTariff: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    Weather: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    GasMeterData: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    RenewablesGeneration: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)


class RemoteMetaData(pydantic.BaseModel):
    """
    Requested remote metadata for datasets you want from the database.

    You can request individual dataset IDs for most types, but ImportTariffs take multiple dataset ids.
    If you provide a start and end timestamp, we'll try to only get datasets that cover those specific times.
    Generally you want to create one of these from a `DatasetList`.
    """

    loc: Literal[FileLocationEnum.remote] = pydantic.Field(
        default=FileLocationEnum.remote,
        examples=["remote"],
        description="Where we are getting the data from, either a local file or remote DB.",
    )
    site_id: site_id_t
    start_ts: pydantic.AwareDatetime = pydantic.Field(default=datetime.datetime(year=1970, month=1, day=1, tzinfo=datetime.UTC))
    end_ts: pydantic.AwareDatetime = pydantic.Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    HeatingLoad: dataset_id_t | list[dataset_id_t] | None = pydantic.Field(default=None)
    ASHPData: dataset_id_t | None = pydantic.Field(default=None)
    CarbonIntensity: dataset_id_t | None = pydantic.Field(default=None)
    ElectricityMeterData: dataset_id_t | None = pydantic.Field(default=None)
    ElectricityMeterDataSynthesised: dataset_id_t | None = pydantic.Field(default=None)
    ImportTariff: dataset_id_t | list[dataset_id_t] | None = pydantic.Field(default=None)
    Weather: dataset_id_t | None = pydantic.Field(default=None)
    GasMeterData: dataset_id_t | None = pydantic.Field(default=None)
    RenewablesGeneration: dataset_id_t | list[dataset_id_t] | None = pydantic.Field(default=None)


SiteDataEntry = RemoteMetaData | LocalMetaData
