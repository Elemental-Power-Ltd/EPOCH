import datetime
from enum import Enum

import pydantic


class Objective(pydantic.BaseModel):
    carbon_balance: float
    cost_balance: float
    capex: float
    payback_horizon: float
    annualised_cost: float


class OptimisationResult(pydantic.BaseModel):
    job_id: pydantic.UUID4
    solutions: dict[str, float | int]
    objective_values: Objective
    n_evals: pydantic.PositiveInt
    exec_time: datetime.timedelta
    completed_at: pydantic.AwareDatetime


class OptimiserEnum(Enum):
    GridSearch = "GridSearch"
    NSGA2 = "NSGA2"


class JobConfig(pydantic.BaseModel):
    job_id: pydantic.UUID4
    job_name: str
    objective_directions: Objective
    constraints_min: Objective
    constraints_max: Objective
    parameters: dict[str, float | int]
    input_data: dict[str, pydantic.UUID4]
    optimiser_type: OptimiserEnum
    optimiser_hyperparameters: dict[str, float | int | str]
    created_at: pydantic.AwareDatetime
