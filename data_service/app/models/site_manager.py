"""Models for site manager, handling requesting datasets."""

# ruff: noqa: D101

import datetime
from enum import StrEnum
from typing import Any

import pydantic

from .client_data import SolarLocation
from .core import DatasetEntry, DatasetTypeEnum, dataset_id_t, site_id_field, site_id_t
from .epoch_types import TaskDataPydantic
from .heating_load import HeatingLoadMetadata
from .import_tariffs import TariffMetadata


class BundleHints(pydantic.BaseModel):
    """GUI suitable hints and metadata for bundled datasets."""

    site_id: site_id_t = site_id_field
    bundle_id: dataset_id_t = pydantic.Field(description="The ID of this bundle of datasets")
    renewables: list[SolarLocation] | None = pydantic.Field(
        default=None, description="Solar locations associated with each renewables generation."
    )
    tariffs: list[TariffMetadata] | None = pydantic.Field(default=None, description="Metadata about each tariff.")
    baseline: TaskDataPydantic | None = pydantic.Field(default=None, description="Contents of the baseline for this bundle.")
    heating: list[HeatingLoadMetadata] | None = pydantic.Field(
        default=None, description="Metadata about each heating load, including interventions.."
    )


class WorkerStatus(pydantic.BaseModel):
    """Status of a given worker job."""

    name: str = pydantic.Field(description="Human-readable name of this worker process")
    exception: str | None = pydantic.Field(default=None, description="The exception that caused this job to fail, if any")
    is_running: bool = pydantic.Field(
        default=False, description="Whether this job is running (either awaiting a job or working)."
    )
    current_job: str | None = pydantic.Field(
        default=None, description="The type of the current job that this worker is running."
    )
    current_job_id: int | None = pydantic.Field(
        default=None, description="The ID of the current job that this worker is running."
    )
    started_at: datetime.datetime | None = pydantic.Field(
        default=None, description="The time this worker picked up the current job."
    )
    coro: str | None = pydantic.Field(description="Name of the coroutine this worker is working on.")
    ctx: dict[str, Any] | None = pydantic.Field(description="Full context dictionary this worker is acting within.")


class DataDuration(StrEnum):
    year = "year"


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
    is_complete: bool = pydantic.Field(default=False, description="True if this bundle is finished generating.")
    is_error: bool = pydantic.Field(default=False, description="True if any generation task for this dataset errored.")
    bundle_id: dataset_id_t | None = pydantic.Field(default=None, description="The bundle these datasets came from")
    SiteBaseline: DatasetEntry | None = pydantic.Field(default=None)
    HeatingLoad: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    ASHPData: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    CarbonIntensity: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    ElectricityMeterData: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    ElectricityMeterDataSynthesised: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    ImportTariff: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    Weather: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    GasMeterData: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    RenewablesGeneration: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    ThermalModel: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)
    PHPP: list[DatasetEntry] | DatasetEntry | None = pydantic.Field(default=None)


class SiteDataEntry(pydantic.BaseModel):
    """
    Requested remote metadata for datasets you want from the database.

    You can request individual dataset IDs for most types, but ImportTariffs take multiple dataset ids.
    If you provide a start and end timestamp, we'll try to only get datasets that cover those specific times.
    Generally you want to create one of these from a `DatasetList`.
    """

    site_id: site_id_t
    start_ts: pydantic.AwareDatetime = pydantic.Field(default=datetime.datetime(year=1970, month=1, day=1, tzinfo=datetime.UTC))
    end_ts: pydantic.AwareDatetime = pydantic.Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    SiteBaseline: dataset_id_t | None = pydantic.Field(default=None)
    HeatingLoad: dataset_id_t | list[dataset_id_t] | None = pydantic.Field(default=None)
    ASHPData: dataset_id_t | None = pydantic.Field(default=None)
    CarbonIntensity: dataset_id_t | None = pydantic.Field(default=None)
    ElectricityMeterData: dataset_id_t | None = pydantic.Field(default=None)
    ElectricityMeterDataSynthesised: dataset_id_t | None = pydantic.Field(default=None)
    ImportTariff: dataset_id_t | list[dataset_id_t] | None = pydantic.Field(default=None)
    Weather: dataset_id_t | None = pydantic.Field(default=None)
    GasMeterData: dataset_id_t | None = pydantic.Field(default=None)
    RenewablesGeneration: dataset_id_t | list[dataset_id_t] | None = pydantic.Field(default=None)
    ThermalModel: dataset_id_t | list[dataset_id_t] | None = pydantic.Field(default=None)
    PHPP: dataset_id_t | None = pydantic.Field(default=None)


class DatasetBundleMetadata(pydantic.BaseModel):
    """Metadata about a specific bundle of datasets, including a unique ID and when it was created."""

    bundle_id: dataset_id_t = pydantic.Field(description="The ID of this bundle of datasets")
    name: str | None = pydantic.Field(default=None, description="Human readable name of this dataset bundle.")
    is_complete: bool = pydantic.Field(default=True, description="True if this bundle has finished generating.")
    is_error: bool = pydantic.Field(
        default=False, description="True if this bundle has suffered an error during the generating process."
    )
    site_id: site_id_t = site_id_field
    start_ts: pydantic.AwareDatetime | None = pydantic.Field(
        default=None, description="The earliest timestamp for each of the datasets in this bundle, if applicable."
    )
    end_ts: pydantic.AwareDatetime | None = pydantic.Field(
        default=None, description="The latest timestamp for each of the datasets in this bundle, if applicable."
    )
    created_at: pydantic.AwareDatetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC), description="When this bundle of datasets was created."
    )
    available_datasets: list[DatasetTypeEnum] = pydantic.Field(
        default=[],
        description=(
            "Unsorted list of the types of datasets available in this bundle."
            " May contain duplicates if there are multiple of a single type. "
        ),
    )
