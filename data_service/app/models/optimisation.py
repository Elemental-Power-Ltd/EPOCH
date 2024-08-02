import datetime
from enum import Enum

import pydantic


class Objective(pydantic.BaseModel):
    carbon_balance: float = pydantic.Field(default=1.0)
    cost_balance: float = pydantic.Field(default=1.0)
    capex: float = pydantic.Field(default=1.0)
    payback_horizon: float = pydantic.Field(default=1.0)
    annualised_cost: float = pydantic.Field(default=1.0)


class OptimisationResult(pydantic.BaseModel):
    TaskID: pydantic.UUID4 | pydantic.UUID1
    solutions: dict[str, float | int]
    objective_values: Objective
    n_evals: pydantic.PositiveInt
    exec_time: datetime.timedelta
    completed_at: pydantic.AwareDatetime


class OptimiserEnum(Enum):
    GridSearch = "GridSearch"
    NSGA2 = "NSGA2"


class FileLocationEnum(Enum):
    local = "local"
    remote = "remote"


class SearchSpaceEntry(pydantic.BaseModel):
    min: float | int
    max: float | int
    step: float | int


class TaskConfig(pydantic.BaseModel):
    task_id: pydantic.UUID4 | pydantic.UUID1 = pydantic.Field(description="Unique ID for this specific task.")
    task_name: str | None = pydantic.Field(default=None, description="Human readable name for a job, e.g. 'Mount Hotel v3'.")
    objective_directions: Objective = pydantic.Field(
        default=Objective(carbon_balance=-1, cost_balance=1, capex=-1, payback_horizon=-1, annualised_cost=-1),
        description="Whether we are maximising (+1) or minimising (-1) a given objective.",
    )
    constraints_min: Objective | None = None
    constraints_max: Objective | None = None
    searchParameters: dict[str, float | int | SearchSpaceEntry]
    objectives: list[str] = pydantic.Field(default=list(Objective().model_dump().keys()))
    siteData: dict[str, FileLocationEnum | pydantic.UUID4 | pydantic.UUID1 | pydantic.FilePath | str]
    optimiser: OptimiserEnum
    optimiser_hyperparameters: dict[str, float | int | str] | None = None
    created_at: pydantic.AwareDatetime = pydantic.Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
