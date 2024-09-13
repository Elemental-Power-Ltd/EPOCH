import datetime
import logging
from enum import StrEnum
from typing import Annotated

from pydantic import UUID4, AwareDatetime, BaseModel, Field, PositiveInt
import uuid
from .optimisers import GAOptimiser, GridSearchOptimiser, NSGA2Optmiser
from .problem import EndpointParameterDict
from .site_data import SiteMetaData

logger = logging.getLogger("default")


class Objectives(StrEnum):
    carbon_balance = "carbon_balance"
    cost_balance = "cost_balance"
    capex = "capex"
    payback_horizon = "payback_horizon"
    annualised_cost = "annualised_cost"


class EndpointTask(BaseModel):
    task_name: str | None = Field(default=None, description="Human readable name for a job, e.g. 'Mount Hotel v3'.")
    optimiser: NSGA2Optmiser | GAOptimiser | GridSearchOptimiser = Field(description="Optimiser name and hyperparameters.")
    search_parameters: EndpointParameterDict = Field(
        description="Search space parameter ranges to optimise over and parameter default values."
    )
    objectives: list[Objectives] = Field(
        examples=[["capex", "carbon_balance"]], description="List of objectives to optimise for."
    )
    site_data: SiteMetaData = Field(
        examples=[{"loc": "local", "site_id": "amcott_house", "path": "./data/InputData"}],
        description="Location to fetch input data from for EPOCH to ingest.",
    )
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        description="The time this Task was created and added to the queue.",
    )


class TaskWithUUID(EndpointTask):
    task_id: Annotated[UUID4, "String serialised UUID"] = Field(default_factory=uuid.uuid4,
        examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv4) of an optimisation task."
    )


class TaskResponse(BaseModel):
    task_id: UUID4


class OptimisationSolution(BaseModel):
    ASHP_HPower: float | int
    ASHP_HSource: float | int
    ASHP_HotTemp: float | int
    ASHP_RadTemp: float | int
    CAPEX_limit: float | int
    ESS_capacity: float | int
    ESS_charge_mode: float | int
    ESS_charge_power: float | int
    ESS_discharge_mode: float | int
    ESS_discharge_power: float | int
    ESS_start_SoC: float | int
    EV_flex: float | int
    Export_headroom: float | int
    Export_kWh_price: float | int
    Fixed_load1_scalar: float | int
    Fixed_load2_scalar: float | int
    Flex_load_max: float | int
    GridExport: float | int
    GridImport: float | int
    Import_headroom: float | int
    Min_power_factor: float | int
    Mop_load_max: float | int
    OPEX_limit: float | int
    ScalarHL1: float | int
    ScalarHYield: float | int
    ScalarRG1: float | int
    ScalarRG2: float | int
    ScalarRG3: float | int
    ScalarRG4: float | int
    f22_EV_CP_number: float | int
    r50_EV_CP_number: float | int
    s7_EV_CP_number: float | int
    target_max_concurrency: float | int
    time_budget_min: float | int
    u150_EV_CP_number: float | int
    timestep_hours: float | int


class ObjectiveValues(BaseModel):
    carbon_balance: float | int
    capex: float | int
    cost_balance: float | int
    payback_horizon: float | int
    annualised_cost: float | int


class EndpointResult(BaseModel):
    task_id: str = Field(
        examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv4) of an optimisation task."
    )
    result_id: str
    solution: OptimisationSolution = Field(description="Parameter values which defines a solution to the optimisation task.")
    objective_values: ObjectiveValues = Field(
        examples=[{"carbon_balance": 9999, "capex": 99999, "cost_balance": 999, "payback_horizon": 9, "annualised_cost": 99}],
        description="Objective values of the solution.",
    )
    n_evals: PositiveInt = Field(examples=["99"], description="Number of unique simulations performed by the optimiser.")
    exec_time: datetime.timedelta = Field(description="Time spent by the optimiser to complete the task.")
    completed_at: str = Field(description="Time at which the optimisation task was completed.")
