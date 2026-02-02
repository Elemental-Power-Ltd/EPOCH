from enum import StrEnum, auto

from pydantic import AwareDatetime, BaseModel, Field

from app.models.core import SimulationMetrics
from app.models.database import dataset_id_t, site_id_t
from app.models.epoch_types import ReportData
from app.models.epoch_types.config import Config
from app.models.epoch_types.task_data_type import TaskData as TaskDataPydantic
from app.models.site_data import EpochSiteData, LegacySiteMetaData, site_metadata_t


class ReproduceSimulationRequest(BaseModel):
    portfolio_id: dataset_id_t
    site_id: str


class RunSimulationRequest(BaseModel):
    task_data: TaskDataPydantic
    site_data: site_metadata_t
    config: Config


class ResultReproConfig(BaseModel):
    portfolio_id: dataset_id_t
    task_data: dict[site_id_t, TaskDataPydantic]


class NewResultReproConfig(ResultReproConfig):
    bundle_ids: dict[site_id_t, dataset_id_t]
    site_configs: dict[site_id_t, Config]


class LegacyResultReproConfig(ResultReproConfig):
    site_data: dict[site_id_t, LegacySiteMetaData]


type result_repro_config_t = NewResultReproConfig | LegacyResultReproConfig


class GetSavedSiteDataRequest(BaseModel):
    portfolio_id: dataset_id_t
    site_id: str


class EpochInputData(BaseModel):
    task_data: TaskDataPydantic
    site_data: EpochSiteData
    site_config: Config


class DayOfInterestType(StrEnum):
    MaxGeneration = auto()
    MaxBatteryThroughput = auto()
    MaxSelfConsumption = auto()
    MaxHeating = auto()
    MaxDemand = auto()
    MaxCost = auto()
    MaxHeatShortfall = auto()
    MaxImportShortfall = auto()
    MaxDHWDemand = auto()


class DayOfInterest(BaseModel):
    day_type: DayOfInterestType = Field(description="Enum with finite list of reasons about why this day is interesting.")
    name: str | None = Field(description="Human readable name for this day, or why it's interesting.")
    start_ts: AwareDatetime = Field(description="Start time for this interesting period (usually the first midnight).")
    end_ts: AwareDatetime = Field(description="End time for this interesting period (usually the next midnight).")


class FullResult(BaseModel):
    metrics: SimulationMetrics
    report_data: ReportData | None

    # we also return the TaskData,SiteData pair used to produce this result
    # (in some contexts, the gui may not be aware of what those are)
    task_data: TaskDataPydantic
    site_data: EpochSiteData
    days_of_interest: list[DayOfInterest] = Field(default=[])
