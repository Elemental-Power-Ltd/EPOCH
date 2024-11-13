import datetime
import logging
import uuid
from typing import Annotated

from pydantic import UUID4, AwareDatetime, BaseModel, Field, PositiveInt

from app.models.objectives import Objectives
from app.models.optimisers import GAOptimiser, GridSearchOptimiser, NSGA2Optmiser
from app.models.parameters import EndpointParameterDict
from app.models.site_data import SiteMetaData

logger = logging.getLogger("default")


class EndpointBuilding(BaseModel):
    name: str = Field(description="Human readable name for a building. Must be unique to portfolio.")
    search_parameters: EndpointParameterDict = Field(
        description="Search space parameter ranges to optimise over and parameter default values."
    )
    site_data: SiteMetaData = Field(
        examples=[{"loc": "local", "site_id": "amcott_house", "path": "./data/InputData"}],
        description="Location to fetch input data from for EPOCH to ingest.",
    )


class EndpointTask(EndpointBuilding):
    optimiser: NSGA2Optmiser | GAOptimiser | GridSearchOptimiser = Field(description="Optimiser name and hyperparameters.")
    objectives: list[Objectives] = Field(
        examples=[["capex", "carbon_balance"]], description="List of objectives to optimise for."
    )
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        description="The time this Task was created and added to the queue.",
    )


class EndpointPortfolioTask(BaseModel):
    name: str = Field(description="Human readable name for a portfolio task, e.g. 'Demonstration v1'.")
    optimiser: NSGA2Optmiser | GridSearchOptimiser = Field(description="Optimiser name and hyperparameters.")
    objectives: list[Objectives] = Field(
        examples=[["capex", "carbon_balance"]], description="List of objectives to optimise for."
    )
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        description="The time this Task was created and added to the queue.",
    )
    buildings: list[EndpointBuilding] = Field(description="List of buildings in portfolio.")


class TaskWithUUID(EndpointPortfolioTask):
    task_id: Annotated[UUID4, "String serialised UUID"] = Field(
        default_factory=uuid.uuid4,
        examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"],
        description="Unique ID (generally a UUIDv4) of an optimisation task.",
    )


class TaskResponse(BaseModel):
    task_id: UUID4


class OptimisationSolution(BaseModel):
    Fixed_load1_scalar: float | int
    Fixed_load2_scalar: float | int
    Flex_load_max: float | int
    Mop_load_max: float | int
    ScalarRG1: float | int
    ScalarRG2: float | int
    ScalarRG3: float | int
    ScalarRG4: float | int
    ScalarHYield: float | int
    s7_EV_CP_number: float | int
    f22_EV_CP_number: float | int
    r50_EV_CP_number: float | int
    u150_EV_CP_number: float | int
    EV_flex: float | int
    ASHP_HPower: float | int
    ASHP_HSource: int
    ASHP_RadTemp: float | int
    ASHP_HotTemp: float | int
    ScalarHL1: float | int
    GridImport: float | int
    GridExport: float | int
    Import_headroom: float | int
    Export_headroom: float | int
    Min_power_factor: float | int
    ESS_charge_power: float | int
    ESS_discharge_power: float | int
    ESS_capacity: float | int
    ESS_start_SoC: float | int
    ESS_charge_mode: int
    ESS_discharge_mode: int
    DHW_cylinder_volume: float | int
    Export_kWh_price: float | int
    time_budget_min: float | int
    target_max_concurrency: float | int
    timestep_hours: float | int
    CAPEX_limit: float | int
    OPEX_limit: float | int
    timewindow: float | int


class ObjectiveValues(BaseModel):
    carbon_balance: float | int
    capex: float | int
    cost_balance: float | int
    payback_horizon: float | int
    annualised_cost: float | int


class EndpointResult(BaseModel):
    task_id: UUID4 = Field(
        examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv4) of an optimisation task."
    )
    site_id: str | None
    result_id: UUID4
    solution: OptimisationSolution | None = Field(
        description="Parameter values which defines a solution to the optimisation task."
    )
    objective_values: ObjectiveValues = Field(
        examples=[{"carbon_balance": 9999, "capex": 99999, "cost_balance": 999, "payback_horizon": 9, "annualised_cost": 99}],
        description="Objective values of the solution.",
    )
    n_evals: PositiveInt = Field(examples=["99"], description="Number of unique simulations performed by the optimiser.")
    exec_time: datetime.timedelta = Field(description="Time spent by the optimiser to complete the task.")
    completed_at: AwareDatetime = Field(description="Time at which the optimisation task was completed.")
