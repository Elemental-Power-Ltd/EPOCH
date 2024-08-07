from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Annotated

from pydantic import UUID4, BaseModel, Field, PositiveInt

from ...internal.genetic_algorithm import NSGA2, GeneticAlgorithm
from ...internal.grid_search import GridSearch
from ...internal.opt_algorithm import Algorithm
from ...internal.problem import Problem
from .problem import ParameterDict
from .site_data import SiteData


class JSONTask(BaseModel):
    task_id: Annotated[UUID4, "String serialised UUID"] = Field(
        examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv4) of an optimisation task."
    )
    optimiser: str = Field(
        examples=["NSGA2", "GeneticAlgorithm", "GridSearch"], description="Name of algorithm to use in optimisation."
    )
    optimiserConfig: dict[str, str | int | float] = Field(
        examples=[{"pop_size": 512}], description="Optimiser hyperparameter config."
    )
    searchParameters: ParameterDict = Field(
        description="Search space parameter ranges to optimise over and parameter default values."
    )
    objectives: list = Field(examples=[["capex", "carbon_balance"]], description="List of objectives to optimise for.")
    siteData: SiteData = Field(
        examples=[
            {"loc": "database", "key": "805fb659-1cac-44f3-a1f9-85dc82178f53"},
            {"loc": "local", "path": "./data/InputData"},
        ],
        description="Location to fetch input data from for EPOCH to ingest.",
    )


class Optimiser(Enum):
    NSGA2 = NSGA2
    GeneticAlgorithm = GeneticAlgorithm
    GridSearch = GridSearch


@dataclass
class PyTask:
    task_id: UUID4 = Field(
        examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv4) of an optimisation task."
    )
    optimiser: Algorithm = Field(description="Optimiser initialised with hyperparameters ready to run optimisation.")
    problem: Problem = Field(description="Problem instance ready to be ingested by optimiser.")
    siteData: SiteData = Field(
        examples=[
            {"loc": "database", "key": "805fb659-1cac-44f3-a1f9-85dc82178f53"},
            {"loc": "local", "path": "./data/InputData"},
        ],
        description="Location to fetch input data from for EPOCH to ingest.",
    )


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


class OptimisationResult(BaseModel):
    task_id: str = Field(
        examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv4) of an optimisation task."
    )
    solution: OptimisationSolution = Field(description="Parameter values which defines a solution to the optimisation task.")
    objective_values: ObjectiveValues = Field(
        examples=[{"carbon_balance": 9999, "capex": 99999, "cost_balance": 999, "payback_horizon": 9, "annualised_cost": 99}],
        description="Objective values of the solution.",
    )
    n_evals: PositiveInt = Field(examples=["99"], description="Number of unique simulations performed by the optimiser.")
    exec_time: timedelta = Field(description="Time spent by the optimiser to complete the task.")
    completed_at: str = Field(description="Time at which the optimisation task was completed.")
