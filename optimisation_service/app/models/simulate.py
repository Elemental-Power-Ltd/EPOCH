from typing import Any

from pydantic import UUID4, BaseModel

from app.models.site_data import SiteMetaData


class ReproduceSimulationRequest(BaseModel):
    result_id: UUID4


class RunSimulationRequest(BaseModel):
    # FIXME: generically typed as a json dict for now
    task_data: dict[str, Any]
    site_data: SiteMetaData


class ResultReproConfig(BaseModel):
    task_id: UUID4
    task_data: dict[str, Any]
    site_data: SiteMetaData


class FullResult(BaseModel):
    objectives: dict[str, float]
    report_data: dict[str, list[float]]

    # TODO - this needs other info like the start_date and timestep_hours
