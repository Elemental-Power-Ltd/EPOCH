"""Models for EPOCH/GA optimisation tasks, both queuing and completing."""

# ruff: noqa: D101
import datetime
import uuid
from enum import StrEnum
from typing import Any, Literal

import pydantic

from .core import client_id_t, dataset_id_t, site_id_field, site_id_t


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


type SolutionType = dict[str, Any]


class SiteOptimisationResult(pydantic.BaseModel):
    """Result for a single site within a portfolio result."""

    site_id: site_id_t
    portfolio_id: pydantic.UUID4
    scenario: SolutionType
    metric_carbon_balance_scope_1: float | None
    metric_carbon_balance_scope_2: float | None
    metric_cost_balance: float | None
    metric_capex: float | None
    metric_payback_horizon: float | None
    metric_annualised_cost: float | None


class PortfolioOptimisationResult(pydantic.BaseModel):
    """Result for a whole portfolio optimisation task, often one entry in the Pareto front."""

    task_id: pydantic.UUID4
    portfolio_id: pydantic.UUID4
    metric_carbon_balance_scope_1: float | None
    metric_carbon_balance_scope_2: float | None
    metric_cost_balance: float | None
    metric_capex: float | None
    metric_payback_horizon: float | None
    metric_annualised_cost: float | None
    site_results: list[SiteOptimisationResult] | None = pydantic.Field(default=None)


class TaskResult(pydantic.BaseModel):
    """Result for metadata about an optimisation task."""

    task_id: pydantic.UUID4
    n_evals: pydantic.PositiveInt
    exec_time: datetime.timedelta
    completed_at: pydantic.AwareDatetime = pydantic.Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))


class OptimisationResultEntry(pydantic.BaseModel):
    portfolio: list[PortfolioOptimisationResult] | None = pydantic.Field(
        default=None, description="List of total portfolio result data"
    )
    sites: list[SiteOptimisationResult] | None = pydantic.Field(
        default=None, description="List of results within a portfolio for the individual sites."
    )
    tasks: list[TaskResult] | None = pydantic.Field(default=None, description="List of task result metadata, e.g. run time")

    @pydantic.field_validator("portfolio", mode="before")
    @classmethod
    def check_portfolio_list(
        cls, v: PortfolioOptimisationResult | list[PortfolioOptimisationResult] | None
    ) -> list[PortfolioOptimisationResult] | None:
        """Check if we've got a list of portfolio results, and if we got just one, make it a list."""
        if v is None:
            return None
        if not isinstance(v, list):
            v = [v]
        return v

    @pydantic.field_validator("sites", mode="before")
    @classmethod
    def check_sites_list(
        cls, v: SiteOptimisationResult | list[SiteOptimisationResult] | None
    ) -> list[SiteOptimisationResult] | None:
        """Check if we've got a list of site results, and if we got just one, make it a list."""
        if v is None:
            return None
        if not isinstance(v, list):
            v = [v]
        return v

    @pydantic.field_validator("tasks", mode="before")
    @classmethod
    def check_task_list(cls, v: TaskResult | list[TaskResult] | None) -> list[TaskResult] | None:
        """Check if we've got a list of task results, and if we got just one, make it a list."""
        if v is None:
            return None
        if not isinstance(v, list):
            v = [v]
        return v


class OptimiserEnum(StrEnum):
    GridSearch = "GridSearch"
    NSGA2 = "NSGA2"
    GeneticAlgorithm = "GeneticAlgorithm"
    BayesianOptimisation = "BayesianOptimisation"


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
    dataset_ids: dict[str, pydantic.UUID4] = pydantic.Field(default={}, description="Specific dataset IDs to fetch.")


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
    client_id: client_id_t = pydantic.Field(
        examples=["demo"],
        description="The database ID for a client, all lower case, joined by underscores.",
    )
    task_name: str | None = pydantic.Field(default=None, description="Human readable name for a job, e.g. 'Mount Hotel v3'.")
    portfolio_constraints: dict[str, dict[str, float]] | None = pydantic.Field(
        default=None,
        examples=[{"capex": {"min": 0, "max": 9999}}],
        description="Dictionary of metrics with 'max' and 'min' keys for the entire portfolio (e.g. spend no more than £1m).",
    )
    site_constraints: dict[site_id_t, dict[str, dict[str, float]]] | None = pydantic.Field(
        default=None,
        examples=[{"demo_london": {"capex": {"min": 0, "max": 9999}}}],
        description="Dict of site ids with sub-dicts of metrics with 'max' and 'min' keys for that site "
        + "(e.g. spend no more than £100k).",
    )
    portfolio_range: dict[site_id_t, dict[str, float | int | SearchSpaceEntry]] = pydantic.Field(
        examples=[
            {
                "demo_london": {
                    "Export_headroom": {"min": 0, "max": 0, "step": 0},
                    "Export_kWh_price": 5,
                    "Fixed_load1_scalar": {"min": 1, "max": 1, "step": 0},
                }
            }
        ],
        description="EPOCH search space parameters, either as single entries or as a min/max/step arrangement for searchables.",
    )
    objectives: list[str] = pydantic.Field(
        default=list(Objective().model_dump().keys()),
        description="The objectives that we're interested in, provided as a list."
        + "Objective that aren't provided here aren't included in the opimisation.",
    )
    input_data: dict[site_id_t, SiteDataEntry] = pydantic.Field(
        examples=[
            {
                "demo_london": {
                    "loc": "remote",
                    "site_id": "demo_london",
                    "start_ts": "2025-01-01T00:00:00Z",
                    "duration": "1Y",
                    "dataset_ids": {"HeatingLoad": uuid.uuid4()},
                }
            }
        ],
        description="Where the data for this calculation are coming from, per-site",
    )
    optimiser: Optimiser = pydantic.Field(
        description="The optimisation algorithm for the backend to use in these calculations."
    )
    created_at: pydantic.AwareDatetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        description="The time this Task was created and added to the queue.",
    )


class ResultReproConfig(pydantic.BaseModel):
    portfolio_id: pydantic.UUID4
    task_data: dict[site_id_t, SolutionType]
    site_data: dict[site_id_t, SiteDataEntry]


class OptimisationTaskListEntry(pydantic.BaseModel):
    task_id: dataset_id_t
    task_name: str | None
    result_ids: list[pydantic.UUID4] | None = pydantic.Field(
        examples=[None, [uuid.uuid4()]], description="Portfolio IDs for the entries in the Pareto front for this task."
    )
    n_evals: pydantic.PositiveInt | None = pydantic.Field(
        examples=[8832],
        description="Number of EPOCH evaluations we ran to calculate this task." + " None if the task didn't complete.",
    )
    exec_time: datetime.timedelta | None = pydantic.Field(
        examples=["PT4.297311S"],
        description="Time it took to calculate this set of results." + " None if the task didn't complete.",
    )
