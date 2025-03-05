from typing import Any

from pydantic import UUID4, BaseModel

from app.models.metrics import MetricValues
from app.models.site_data import EpochSiteData, RemoteMetaData, SiteMetaData

site_id_t = str
TaskDataType = dict[str, Any]


class ReproduceSimulationRequest(BaseModel):
    portfolio_id: UUID4
    site_id: str


class RunSimulationRequest(BaseModel):
    task_data: TaskDataType
    site_data: SiteMetaData


class ResultReproConfig(BaseModel):
    portfolio_id: UUID4
    task_data: dict[site_id_t, TaskDataType]
    site_data: dict[site_id_t, RemoteMetaData]


class GetSavedSiteDataRequest(BaseModel):
    portfolio_id: UUID4
    site_id: str


class EpochInputData(BaseModel):
    task_data: TaskDataType
    site_data: EpochSiteData


class FullResult(BaseModel):
    objectives: MetricValues
    report_data: dict[str, list[float]]

    # we also return the TaskData,SiteData pair used to produce this result
    # (in some contexts, the gui may not be aware of what those are)
    task_data: TaskDataType
    site_data: EpochSiteData
