"""Models for EPOCH/GA optimisation tasks, both queuing and completing."""

# ruff: noqa: D101
import datetime
import uuid
from enum import StrEnum
from typing import Any

import pydantic

from .core import client_id_t, dataset_id_t, site_id_field, site_id_t
from .site_manager import SiteDataEntry
from .site_range import SiteRange

type SiteScenario = dict[str, Any]


class SiteOptimisationResult(pydantic.BaseModel):
    """Result for a single site within a portfolio result."""

    site_id: site_id_t = site_id_field
    portfolio_id: pydantic.UUID4 = pydantic.Field(
        description="The portfolio pareto front entry this site is linked to."
        + " A single site result is uniquely identified by a (portfolio_id, site_id) pair."
    )
    scenario: SiteScenario = pydantic.Field(
        description="The mix of assets used in this scenario, e.g. solar PV and grid connects."
    )
    metric_carbon_balance_scope_1: float | None = pydantic.Field(
        description="Direct carbon emissions saved by this scenario on this site.", default=None, examples=[None, 3.14]
    )
    metric_carbon_balance_scope_2: float | None = pydantic.Field(
        description="Net kg CO2e over the lifetime of these interventions for scope 2 on this site.", default=None
    )
    metric_carbon_cost: float | None = pydantic.Field(
        description="Net £ per t CO2e over the lifetime of these interventions on this site.", default=None
    )
    metric_cost_balance: float | None = pydantic.Field(
        description="Net monetary cost (opex - returns) over the lifetime of these interventions on this site.", default=None
    )
    metric_capex: float | None = pydantic.Field(description="Cost to install this scenario on this site.", default=None)
    metric_payback_horizon: float | None = pydantic.Field(
        description="Years for this scenario to pay back on this site (if very large, represents no payback ever.)",
        default=None,
    )
    metric_annualised_cost: float | None = pydantic.Field(
        description="Cost of running this scenario (including amortised deprecation) on this site.", default=None
    )


class PortfolioOptimisationResult(pydantic.BaseModel):
    """Result for a whole portfolio optimisation task, often one entry in the Pareto front."""

    task_id: pydantic.UUID4
    portfolio_id: pydantic.UUID4 = pydantic.Field(
        description="Individual ID representing this entry in the portfolio pareto front,"
        + " used to link to SiteOptimisationResults."
    )
    metric_carbon_balance_scope_1: float | None = pydantic.Field(
        description="Direct carbon emissions saved by this entire portfolio of scenarios.", default=None, examples=[None, 3.14]
    )
    metric_carbon_balance_scope_2: float | None = pydantic.Field(
        description="Indirect scope 2 carbon emissions saved by this entire portfolio of scenarios.", default=None
    )
    metric_carbon_cost: float | None = pydantic.Field(
        description="Net £ per t CO2e over the lifetime of these interventions on this site.", default=None
    )
    metric_cost_balance: float | None = pydantic.Field(
        description="Net change in annual running cost due to this entire portfolio of scenarios.", default=None
    )
    metric_capex: float | None = pydantic.Field(
        description="Cost to install this scenario on entire portfolio of scenarios.", default=None
    )
    metric_payback_horizon: float | None = pydantic.Field(
        description="Years for these scenarios to pay back across this portfolio.", default=None
    )
    metric_annualised_cost: float | None = pydantic.Field(
        description="Cost of running these scenario (including amortised deprecation) across this portfolio", default=None
    )
    site_results: list[SiteOptimisationResult] | None = pydantic.Field(
        default=None,
        description="Individual site results for this Portfolio."
        + " Not provided when requesting a specific portfolio from the DB.",
    )


class TaskResult(pydantic.BaseModel):
    """Result for metadata about an optimisation task."""

    task_id: pydantic.UUID4
    n_evals: pydantic.PositiveInt = pydantic.Field(
        description="Number of site scenarios evaluated during this task.", examples=[1, 9999]
    )
    exec_time: datetime.timedelta = pydantic.Field(description="Wall-clock time this optimisation run took.")
    completed_at: pydantic.AwareDatetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        description="The wall-clock time this optimisation run concluded at.",
    )


class OptimisationResultEntry(pydantic.BaseModel):
    portfolio: list[PortfolioOptimisationResult] | None = pydantic.Field(
        default=None, description="List of total portfolio result data, with associated site results."
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


class Optimiser(pydantic.BaseModel):
    name: OptimiserEnum = pydantic.Field(default=OptimiserEnum.NSGA2, description="Name of optimiser.")
    hyperparameters: dict[str, float | int | str] | None = pydantic.Field(
        default=None, description="Hyperparameters provided to the optimiser, especially interesting for Genetic algorithms."
    )


class TaskConfig(pydantic.BaseModel):
    task_id: pydantic.UUID4 = pydantic.Field(description="Unique ID for this specific task.")
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
    portfolio_range: dict[site_id_t, SiteRange] = pydantic.Field(
        examples=[
            {
                "demo_london": {
                    "Export_headroom": {"min": 0, "max": 0, "step": 0},
                    "Export_kWh_price": 5,
                    "Fixed_load1_scalar": {"min": 1, "max": 1, "step": 0},
                }
            }
        ],
        description="EPOCH search space parameters, either as single entries or as a"
        + " min/max/step arrangement for searchables. Keyed by site ID.",
    )
    objectives: list[str] = pydantic.Field(
        default=[
            "capex",
            "carbon_cost",
            "carbon_balance_scope_1",
            "carbon_balance_scope_2",
            "annualised_cost",
            "payback_horizon",
        ],
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
    task_data: dict[site_id_t, SiteScenario]
    site_data: dict[site_id_t, SiteDataEntry]


class OptimisationTaskListEntry(pydantic.BaseModel):
    task_id: dataset_id_t
    task_name: str | None
    n_evals: pydantic.PositiveInt | None = pydantic.Field(
        examples=[8832],
        description="Number of EPOCH evaluations we ran to calculate this task." + " None if the task didn't complete.",
    )
    n_saved: pydantic.NonNegativeInt = pydantic.Field(
        examples=[12, 0], description="The number of portfolio results saved to the database for this task."
    )
    exec_time: datetime.timedelta | None = pydantic.Field(
        examples=["PT4.297311S"],
        description="Time it took to calculate this set of results." + " None if the task didn't complete.",
    )
