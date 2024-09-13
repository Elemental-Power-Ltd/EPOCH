"""Models for EPOCH/GA optimisation tasks, both queuing and completing."""

# ruff: noqa: D101
import datetime
from enum import StrEnum
from typing import Literal

import pydantic

from .core import dataset_id_t, site_id_field, site_id_t


class Objective(pydantic.BaseModel):
    carbon_balance: float | None = pydantic.Field(
        default=1.0, description="Net kg CO2e over the lifetime of these interventions."
    )
    cost_balance: float | None = pydantic.Field(
        default=1.0, description="Net monetary cost (opex - returns) over the lifetime of these interventions."
    )
    capex: float | None = pydantic.Field(default=1.0, description="Upfront CAPEX cost for these interventions.")
    payback_horizon: float | None = pydantic.Field(
        default=1.0, description="Years before this intervention pays for itself (if very large, represents no payback ever.)"
    )
    annualised_cost: float | None = pydantic.Field(default=1.0, description="Cost to run these interventions per year")


class OptimisationResult(pydantic.BaseModel):
    task_id: pydantic.UUID4 | pydantic.UUID1 = pydantic.Field(
        examples=["bb8ce01e-4a73-11ef-9454-0242ac120001"],
        description="Unique ID for this task, often assigned by the optimiser.",
    )
    result_id: pydantic.UUID4
    solution: dict[str, float | int] = pydantic.Field(
        examples=[{"ASHP_HPower": 70.0, "ScalarHYield": 0.75, "ScalarRG1": 599.2000122070312}],
        description="EPOCH parameters e.g. ESS_Capacity=1000 for this specific solution."
        + "May not cover all parameters, only the ones we searched over.",
    )
    n_evals: pydantic.PositiveInt | None = None
    exec_time: datetime.timedelta | None = None
    objective_values: Objective = pydantic.Field(
        examples=[
            {
                "carbon_balance": 280523.3125,
                "cost_balance": 230754.328125,
                "capex": 371959.96875,
                "payback_horizon": 1.6119306087493896,
                "annualised_cost": 22880.55078125,
            }
        ],
        description="Values of the objectives at this specific point.",
    )
    completed_at: pydantic.AwareDatetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC), description="Time this result was calculated at.."
    )


class OptimiserEnum(StrEnum):
    GridSearch = "GridSearch"
    NSGA2 = "NSGA2"
    GeneticAlgorithm = "GeneticAlgorithm"


class FileLocationEnum(StrEnum):
    local = "local"
    remote = "remote"


class SearchSpaceEntry(pydantic.BaseModel):
    min: float | int = pydantic.Field(examples=[10, 100], description="The smallest value, inclusive, to search over.")
    max: float | int = pydantic.Field(examples=[200, 2000], description="The largest value, inclusive, to search over.")
    step: float | int = pydantic.Field(examples=[10, 50], description="The steps to take when searching this variable.")


class DataDuration(StrEnum):
    year = "year"


class RemoteMetaData(pydantic.BaseModel):
    loc: Literal[FileLocationEnum.remote] = pydantic.Field(
        default=FileLocationEnum.remote,
        examples=["remote"],
        description="Where we are getting the data from, either a local file or remote DB.",
    )
    site_id: site_id_t = site_id_field
    start_ts: pydantic.AwareDatetime = pydantic.Field(
        description="Datetime to retrieve data from. Only relevant for remote files."
    )
    duration: DataDuration = pydantic.Field(description="Length of time to retrieve data for. Only relevant for remote files.")


class LocalMetaData(pydantic.BaseModel):
    loc: Literal[FileLocationEnum.local] = pydantic.Field(
        default=FileLocationEnum.local,
        examples=["local"],
        description="Where we are getting the data from, either a local file or remote DB.",
    )
    site_id: site_id_t = site_id_field
    path: pydantic.FilePath | str = pydantic.Field(
        examples=["./tests/data/benchmarks/var-3/InputData"], description="If a local file, the path to it."
    )


SiteDataEntry = RemoteMetaData | LocalMetaData


class Optimiser(pydantic.BaseModel):
    name: OptimiserEnum = pydantic.Field(default=None, description="Name of optimiser.")
    hyperparameters: dict[str, float | int | str] | None = pydantic.Field(
        default=None, description="Hyperparameters provided to the optimiser, especially interesting for Genetic algorithms."
    )


class TaskConfig(pydantic.BaseModel):
    task_id: pydantic.UUID4 | pydantic.UUID1 = pydantic.Field(description="Unique ID for this specific task.")
    task_name: str | None = pydantic.Field(default=None, description="Human readable name for a job, e.g. 'Mount Hotel v3'.")
    objective_directions: Objective = pydantic.Field(
        default=Objective(carbon_balance=-1, cost_balance=1, capex=-1, payback_horizon=-1, annualised_cost=-1),
        description="Whether we are maximising (+1) or minimising (-1) a given objective.",
    )
    constraints_min: Objective | None = pydantic.Field(
        default=None,
        examples=[Objective(carbon_balance=None, cost_balance=1e6, capex=None, payback_horizon=None, annualised_cost=None)],
        description="Minimal values of the objectives to consider, e.g. reject all solutions with carbon balance < 1000.",
    )
    constraints_max: Objective | None = pydantic.Field(
        default=None,
        examples=[Objective(carbon_balance=None, cost_balance=None, capex=1e6, payback_horizon=None, annualised_cost=None)],
        description="Maximal values of the objectives to consider, e.g. reject all solutions with capex > £1,000,000.",
    )
    search_parameters: dict[str, float | int | SearchSpaceEntry] = pydantic.Field(
        examples=[
            {
                "Export_headroom": {"min": 0, "max": 0, "step": 0},
                "Export_kWh_price": 5,
                "Fixed_load1_scalar": {"min": 1, "max": 1, "step": 0},
            }
        ],
        description="EPOCH search space parameters, either as single entries or as a min/max/step arrangement for searchables.",
    )
    objectives: list[str] = pydantic.Field(
        default=list(Objective().model_dump().keys()),
        description="The objectives that we're interested in, provided as a list."
        + "Objective that aren't provided here aren't included in the opimisation.",
    )
    site_data: SiteDataEntry = pydantic.Field(description="Where the data for this calculation are coming from.")
    optimiser: Optimiser = pydantic.Field(
        description="The optimisation algorithm for the backend to use in these calculations."
    )
    optimiser_hyperparameters: dict[str, float | int | str] | None = pydantic.Field(
        default=None, description="Hyperparameters provided to the optimiser, especially interesting for Genetic algorithms."
    )
    created_at: pydantic.AwareDatetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        description="The time this Task was created and added to the queue.",
    )


class OptimisationTaskListEntry(pydantic.BaseModel):
    task_id: dataset_id_t
    site_id: site_id_t = site_id_field
    task_name: str | None
    result_ids: list[pydantic.UUID4]
    n_evals: pydantic.PositiveInt = pydantic.Field(
        examples=[8832], description="Number of EPOCH evaluations we ran to calculate this."
    )
    exec_time: datetime.timedelta = pydantic.Field(
        examples=["PT4.297311S"], description="Time it took to calculate this set of results."
    )
