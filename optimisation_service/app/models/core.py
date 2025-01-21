import datetime
import logging
import uuid
from os import PathLike
from typing import Annotated

from pydantic import UUID4, AwareDatetime, BaseModel, Field, PositiveInt, PrivateAttr

from app.models.objectives import Objectives, ObjectiveValues
from app.models.optimisers import GridSearchOptimiser, NSGA2Optmiser
from app.models.site_data import SiteMetaData
from app.models.site_range import SiteRange

logger = logging.getLogger("default")


class Site(BaseModel):
    name: str = Field(description="Human readable name for a building. Must be unique to portfolio.")
    site_range: SiteRange = Field(description="Site range to optimise over.")
    site_data: SiteMetaData = Field(
        examples=[{"loc": "local", "site_id": "amcott_house", "path": "./data/InputData"}],
        description="Location to fetch input data from for EPOCH to ingest.",
    )
    _input_dir: PathLike = PrivateAttr()


class EndpointTask(Site):
    optimiser: NSGA2Optmiser | GridSearchOptimiser = Field(description="Optimiser name and hyperparameters.")
    objectives: list[Objectives] = Field(examples=[["carbon_cost"]], description="List of objectives to optimise for.")
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        description="The time this Task was created and added to the queue.",
    )
    client_id: str = Field(
        examples=["demo"],
        description="The database ID for a client, all lower case, joined by underscores.",
    )


class Task(BaseModel):
    name: str = Field(description="Human readable name for a portfolio task, e.g. 'Demonstration v1'.")
    optimiser: NSGA2Optmiser | GridSearchOptimiser = Field(description="Optimiser name and hyperparameters.")
    objectives: list[Objectives] = Field(
        examples=[["capex", "carbon_balance"]], description="List of objectives to optimise for."
    )
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        description="The time this Task was created and added to the queue.",
    )
    portfolio: list[Site] = Field(description="List of buildings in portfolio.")
    client_id: str = Field(
        examples=["demo"],
        description="The database ID for a client, all lower case, joined by underscores.",
    )
    task_id: Annotated[UUID4, "String serialised UUID"] = Field(
        default_factory=uuid.uuid4,
        description="Unique ID (generally a UUIDv4) of an optimisation task.",
    )
    _input_dir: PathLike = PrivateAttr()


class TaskResponse(BaseModel):
    task_id: UUID4


class EndpointResult(BaseModel):
    task_id: UUID4 = Field(
        examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv4) of an optimisation task."
    )
    site_id: str | None
    result_id: UUID4
    portfolio_id: UUID4
    solution: dict | None = Field(description="Site scenario / Dictionary representation of a TaskData.")
    objective_values: ObjectiveValues = Field(
        examples=[
            {
                "carbon_cost": 9999,
                "carbon_balance_scope_1": 99,
                "carbon_balance_scope_2": 99,
                "capex": 99999,
                "cost_balance": 999,
                "payback_horizon": 9,
                "annualised_cost": 99,
            }
        ],
        description="Objective values of the solution.",
    )
    n_evals: PositiveInt = Field(examples=["99"], description="Number of unique simulations performed by the optimiser.")
    exec_time: datetime.timedelta = Field(description="Time spent by the optimiser to complete the task.")
    completed_at: AwareDatetime = Field(description="Time at which the optimisation task was completed.")
