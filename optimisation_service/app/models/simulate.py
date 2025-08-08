from pydantic import BaseModel

from app.models.database import dataset_id_t, site_id_t
from app.models.epoch_types import ReportData
from app.models.epoch_types.task_data_type import TaskData as TaskDataPydantic
from app.models.metrics import MetricValues
from app.models.site_data import EpochSiteData, RemoteMetaData, SiteMetaData


class ReproduceSimulationRequest(BaseModel):
    portfolio_id: dataset_id_t
    site_id: str


class RunSimulationRequest(BaseModel):
    task_data: TaskDataPydantic
    site_data: SiteMetaData


class ResultReproConfig(BaseModel):
    portfolio_id: dataset_id_t
    task_data: dict[site_id_t, TaskDataPydantic]
    site_data: dict[site_id_t, RemoteMetaData]


class GetSavedSiteDataRequest(BaseModel):
    portfolio_id: dataset_id_t
    site_id: str


class EpochInputData(BaseModel):
    task_data: TaskDataPydantic
    site_data: EpochSiteData


class FullResult(BaseModel):
    metrics: MetricValues
    report_data: ReportData | None

    # we also return the TaskData,SiteData pair used to produce this result
    # (in some contexts, the gui may not be aware of what those are)
    task_data: TaskDataPydantic
    site_data: EpochSiteData
