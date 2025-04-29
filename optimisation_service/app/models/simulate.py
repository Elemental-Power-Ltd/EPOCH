from pydantic import UUID4, BaseModel

from app.models.epoch_types import ReportData, TaskDataPydantic
from app.models.metrics import MetricValues
from app.models.site_data import EpochSiteData, RemoteMetaData, SiteMetaData

site_id_t = str


class ReproduceSimulationRequest(BaseModel):
    portfolio_id: UUID4
    site_id: str


class RunSimulationRequest(BaseModel):
    task_data: TaskDataPydantic
    site_data: SiteMetaData


class ResultReproConfig(BaseModel):
    portfolio_id: UUID4
    task_data: dict[site_id_t, TaskDataPydantic]
    site_data: dict[site_id_t, RemoteMetaData]


class GetSavedSiteDataRequest(BaseModel):
    portfolio_id: UUID4
    site_id: str


class EpochInputData(BaseModel):
    task_data: TaskDataPydantic
    site_data: EpochSiteData


class FullResult(BaseModel):
    metrics: MetricValues
    report_data: ReportData

    # we also return the TaskData,SiteData pair used to produce this result
    # (in some contexts, the gui may not be aware of what those are)
    task_data: TaskDataPydantic
    site_data: EpochSiteData
