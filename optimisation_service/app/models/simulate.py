from typing import Any

from pydantic import UUID4, BaseModel

from app.models.objectives import ObjectiveValues
from app.models.site_data import RemoteMetaData, SiteMetaData


class ReproduceSimulationRequest(BaseModel):
    portfolio_id: UUID4
    site_id: str


class RunSimulationRequest(BaseModel):
    # FIXME: generically typed as a json dict for now
    task_data: dict[str, Any]
    site_data: SiteMetaData


class ResultReproConfig(BaseModel):
    portfolio_id: UUID4
    task_data: dict[str, dict[str, Any]]
    site_data: dict[str, RemoteMetaData]


class FullResult(BaseModel):
    objectives: ObjectiveValues
    report_data: dict[str, list[float]]

    # TODO - this needs other info like the start_date and timestep_hours
