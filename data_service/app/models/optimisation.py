"""Models for EPOCH/GA optimisation tasks, both queuing and completing."""

# ruff: noqa: D101
import datetime
import math
from enum import StrEnum

import pydantic
from pydantic import BaseModel, Field

from ..internal.utils.uuid import uuid7
from .core import client_id_t, dataset_id_t, site_id_field, site_id_t
from .epoch_types import TaskDataPydantic
from .site_manager import SiteDataEntry
from .site_range import SiteRange


class SiteMetrics(BaseModel):
    """Metrics for a single site within a portfolio."""

    carbon_balance_scope_1: float | None = Field(
        description="Direct carbon emissions saved by this scenario on this site.", default=None, examples=[None, math.pi]
    )
    carbon_balance_scope_2: float | None = Field(
        description="Net kg CO2e over the lifetime of these interventions for scope 2 on this site.", default=None
    )
    carbon_balance_total: float | None = Field(
        description="Scope 1 + 2 emissions across this portfolio in kg CO2e; None if either is unset",
        default_factory=lambda data: (data["carbon_balance_scope_1"] + data["carbon_balance_scope_2"])
        if data.get("carbon_balance_scope_1") is not None and data.get("carbon_balance_scope_2") is not None
        else None,
    )
    carbon_cost: float | None = Field(
        description="Net £ per t CO2e over the lifetime of these interventions on this site.", default=None
    )
    meter_balance: float | None = Field(
        description="Monetary savings from importing and exporting fuel/electricity when compared against the baseline.",
        default=None,
    )
    operating_balance: float | None = Field(
        description="Monetary savings from fuel, electricity and opex when compared against the baseline.", default=None
    )
    cost_balance: float | None = Field(
        description="Monetary savings from fuel, electricity, opex and annualised cost when compared against the baseline.",
        default=None,
    )
    npv_balance: float | None = Field(
        description="The change in Net Present Value between the baseline and the scenario for this site.", default=None
    )
    capex: float | None = Field(description="Cost to install this scenario on this site.", default=None)
    payback_horizon: float | None = Field(
        description="Years for this scenario to pay back on this site (if very large, represents no payback ever.)",
        default=None,
    )
    annualised_cost: float | None = Field(
        description="Cost of running this scenario (including amortised deprecation) on this site.", default=None
    )
    total_gas_used: float | None = Field(description="Total gas imported (kWh) for this site", default=None)
    total_electricity_imported: float | None = Field(
        description="Total electricity imported from the grid (kWh) for this site", default=None
    )
    total_electricity_generated: float | None = Field(
        description="Total electricity generated on-site (kWh) for this site", default=None
    )
    total_electricity_exported: float | None = Field(
        description="Total electricity exported to the grid (kWh) for this site", default=None
    )
    total_electrical_shortfall: float | None = Field(
        description="Total electrical shortfall (kWh) when compared to the demand for this site", default=None
    )
    total_heat_shortfall: float | None = Field(
        description="Total heat shortfall (kWh) when compared to the demand for this site", default=None
    )
    total_ch_shortfall: float | None = Field(
        description="Total central heating (CH) shortfall (kWh) when compared to the demand for this site", default=None
    )
    total_dhw_shortfall: float | None = Field(
        description="Total domestic hot water (DHW) shortfall (kWh) when compared to the demand for this site", default=None
    )
    total_gas_import_cost: float | None = Field(description="Total spend (£) importing gas for the site", default=None)
    total_electricity_import_cost: float | None = Field(
        description="Total spend (£) importing electricity from the grid for this site", default=None
    )
    total_electricity_export_gain: float | None = Field(
        description="Total income (£) exporting electricity to this grid for this site", default=None
    )
    total_meter_cost: float | None = Field(
        description="Total cost of importing fuel/electricity minus revenue from exporting.", default=None
    )
    total_operating_cost: float | None = Field(
        description="Total meter cost minus operating costs for components for this site.", default=None
    )
    total_net_present_value: float | None = Field(
        description="Net Present Value after repeating the simulation for the configured number of years for this site.",
        default=None,
    )

    baseline_gas_used: float | None = Field(description="Baseline gas imported (kWh) for this site", default=None)
    baseline_electricity_imported: float | None = Field(
        description="Baseline electricity imported from the grid (kWh) for this site", default=None
    )
    baseline_electricity_generated: float | None = Field(
        description="Baseline electricity generated on-site (kWh) for this site", default=None
    )
    baseline_electricity_exported: float | None = Field(
        description="Baseline electricity exported to the grid (kWh) for this site", default=None
    )
    baseline_electrical_shortfall: float | None = Field(
        description="Baseline electrical shortfall (kWh) when compared to the demand for this site", default=None
    )
    baseline_heat_shortfall: float | None = Field(
        description="Baseline heat shortfall (kWh) when compared to the demand for this site", default=None
    )
    baseline_ch_shortfall: float | None = Field(
        description="Baseline central heating (CH) shortfall (kWh) when compared to the demand for this site", default=None
    )
    baseline_dhw_shortfall: float | None = Field(
        description="Baseline domestic hot water (DHW) shortfall (kWh) when compared to the demand for this site", default=None
    )
    baseline_gas_import_cost: float | None = Field(description="Total spend (£) importing gas for the site", default=None)
    baseline_electricity_import_cost: float | None = Field(
        description="Baseline spend (£) importing electricity from the grid for this site", default=None
    )
    baseline_electricity_export_gain: float | None = Field(
        description="Baseline income (£) exporting electricity to this grid for this site", default=None
    )
    baseline_meter_cost: float | None = Field(
        description="Baseline cost of importing fuel/electricity minus revenue from exporting.", default=None
    )
    baseline_operating_cost: float | None = Field(
        description="Baseline meter cost minus operating costs for components for this site.", default=None
    )
    baseline_net_present_value: float | None = Field(
        description="Baseline Net Present Value after repeating the simulation for the configured number of years "
        "for this site.",
        default=None,
    )


class SiteOptimisationResult(pydantic.BaseModel):
    """Result for a single site within a portfolio result."""

    site_id: site_id_t = site_id_field
    portfolio_id: pydantic.UUID7 = pydantic.Field(
        description="The portfolio pareto front entry this site is linked to."
        + " A single site result is uniquely identified by a (portfolio_id, site_id) pair."
    )
    scenario: TaskDataPydantic = pydantic.Field(
        description="The mix of assets used in this scenario, e.g. solar PV and grid connects."
    )
    metrics: SiteMetrics = pydantic.Field(description="The metrics calculated for this site.")


class PortfolioMetrics(BaseModel):
    """Metrics for the whole portfolio."""

    carbon_balance_scope_1: float | None = Field(
        description="Direct carbon emissions saved by this entire portfolio of scenarios.",
        default=None,
        examples=[None, math.pi],
    )
    carbon_balance_scope_2: float | None = Field(
        description="Indirect scope 2 carbon emissions saved by this entire portfolio of scenarios.", default=None
    )
    carbon_balance_total: float | None = Field(
        description="Scope 1 + 2 emissions across this portfolio in kg CO2e; None if either is unset",
        default_factory=lambda data: (data["carbon_balance_scope_1"] + data["carbon_balance_scope_2"])
        if data.get("carbon_balance_scope_1") is not None and data.get("carbon_balance_scope_2") is not None
        else None,
    )
    carbon_cost: float | None = Field(
        description="Net £ per t CO2e over the lifetime of these interventions on this site.", default=None
    )
    meter_balance: float | None = Field(
        description="Monetary savings across the portfolio "
        "from importing and exporting fuel/electricity when compared against the baseline.",
        default=None,
    )
    operating_balance: float | None = Field(
        description="Monetary savings across the portfolio from fuel, electricity and opex when compared against the baseline.",
        default=None,
    )
    cost_balance: float | None = Field(
        description="Monetary savings across the portfolio "
        "from fuel, electricity, opex and annualised cost when compared against the baseline.",
        default=None,
    )
    npv_balance: float | None = Field(
        description="The change in Net Present Value between the baseline and the scenario over the portfolio.", default=None
    )
    capex: float | None = Field(description="Cost to install this scenario on entire portfolio of scenarios.", default=None)
    payback_horizon: float | None = Field(
        description="Years for these scenarios to pay back across this portfolio.", default=None
    )
    annualised_cost: float | None = Field(
        description="Cost of running these scenario (including amortised deprecation) across this portfolio", default=None
    )
    total_gas_used: float | None = Field(description="Total gas imported (kWh) across this portfolio", default=None)
    total_electricity_imported: float | None = Field(
        description="Total electricity imported from the grid (kWh) across this portfolio", default=None
    )
    total_electricity_generated: float | None = Field(
        description="Total electricity generated on-site (kWh) across this portfolio", default=None
    )
    total_electricity_exported: float | None = Field(
        description="Total electricity exported to the grid (kWh) across this portfolio", default=None
    )
    total_electrical_shortfall: float | None = Field(
        description="Total electrical shortfall (kWh) when compared to the demand across this portfolio", default=None
    )
    total_heat_shortfall: float | None = Field(
        description="Total heat shortfall (kWh) when compared to the demand across this portfolio", default=None
    )
    total_ch_shortfall: float | None = Field(
        description="Total central heating (CH) shortfall (kWh) when compared to the demand across this portfolio", default=None
    )
    total_dhw_shortfall: float | None = Field(
        description="Total domestic hot water (DHW) shortfall (kWh) when compared to the demand across this portfolio",
        default=None,
    )
    total_gas_import_cost: float | None = Field(description="Total spend (£) importing gas across this portfolio", default=None)
    total_electricity_import_cost: float | None = Field(
        description="Total spend (£) importing electricity from the grid across this portfolio", default=None
    )
    total_electricity_export_gain: float | None = Field(
        description="Total income (£) exporting electricity to this grid across this portfolio", default=None
    )
    total_meter_cost: float | None = Field(
        description="Total cost of importing fuel/electricity minus revenue from exporting across this portfolio.", default=None
    )
    total_operating_cost: float | None = Field(
        description="Total meter cost minus operating costs for components across this portfolio.", default=None
    )
    total_net_present_value: float | None = Field(
        description="Net Present Value after repeating the simulation for the configured number of years "
        "across this portfolio.",
        default=None,
    )

    baseline_gas_used: float | None = Field(description="Baseline gas imported (kWh) across this portfolio", default=None)
    baseline_electricity_imported: float | None = Field(
        description="Baseline electricity imported from the grid (kWh) across this portfolio", default=None
    )
    baseline_electricity_generated: float | None = Field(
        description="Baseline electricity generated on-site (kWh) across this portfolio", default=None
    )
    baseline_electricity_exported: float | None = Field(
        description="Baseline electricity exported to the grid (kWh) across this portfolio", default=None
    )
    baseline_electrical_shortfall: float | None = Field(
        description="Baseline electrical shortfall (kWh) when compared to the demand across this portfolio", default=None
    )
    baseline_heat_shortfall: float | None = Field(
        description="Baseline heat shortfall (kWh) when compared to the demand across this portfolio", default=None
    )
    baseline_ch_shortfall: float | None = Field(
        description="Baseline central heating (CH) shortfall (kWh) when compared to the demand across this portfolio",
        default=None,
    )
    baseline_dhw_shortfall: float | None = Field(
        description="Baseline domestic hot water (DHW) shortfall (kWh) when compared to the demand across this portfolio",
        default=None,
    )
    baseline_gas_import_cost: float | None = Field(
        description="Baseline spend (£) importing gas across this portfolio", default=None
    )
    baseline_electricity_import_cost: float | None = Field(
        description="Baseline spend (£) importing electricity from the grid across this portfolio", default=None
    )
    baseline_electricity_export_gain: float | None = Field(
        description="Baseline income (£) exporting electricity to this grid across this portfolio", default=None
    )
    baseline_meter_cost: float | None = Field(
        description="Baseline cost of importing fuel/electricity minus revenue from exporting across this portfolio.",
        default=None,
    )
    baseline_operating_cost: float | None = Field(
        description="Baseline meter cost minus operating costs for components across this portfolio.", default=None
    )
    baseline_net_present_value: float | None = Field(
        description="Baseline Net Present Value after repeating the simulation for the configured number of years "
        "across this portfolio.",
        default=None,
    )


class PortfolioOptimisationResult(pydantic.BaseModel):
    """Result for a whole portfolio optimisation task, often one entry in the Pareto front."""

    task_id: pydantic.UUID7
    portfolio_id: pydantic.UUID7 = pydantic.Field(
        description="Individual ID representing this entry in the portfolio pareto front,"
        + " used to link to SiteOptimisationResults."
    )
    metrics: PortfolioMetrics = pydantic.Field(description="The metrics calculated across the whole portfolio.")
    site_results: list[SiteOptimisationResult] | None = pydantic.Field(
        default=None,
        description="Individual site results for this Portfolio."
        + " Not provided when requesting a specific portfolio from the DB.",
    )


class HighlightReason(StrEnum):
    BestCostBalance = "best_cost_balance"
    BestCarbonBalance = "best_carbon_balance"
    BestPaybackHorizon = "best_payback_horizon"


class HighlightedResult(pydantic.BaseModel):
    """A portfolio result we want to draw attention to and a reason why."""

    portfolio_id: pydantic.UUID7 = pydantic.Field(
        description="Individual ID representing this entry in the portfolio pareto front."
    )
    reason: HighlightReason = pydantic.Field(description="The reason the portfolio result is highlighted.")


class OptimisationResultsResponse(pydantic.BaseModel):
    """Response containing all saved results for a given task_id and some highlighted results."""

    portfolio_results: list[PortfolioOptimisationResult] = pydantic.Field(
        description="Result for a whole portfolio optimisation task, often one entry in the Pareto front."
    )
    highlighted_results: list[HighlightedResult] = pydantic.Field(
        description="A list of highlighted results, containing a portfolio_id and the reason the result is highlighted."
    )


class TaskResult(pydantic.BaseModel):
    """Result for metadata about an optimisation task."""

    task_id: pydantic.UUID7
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
    Bayesian = "Bayesian"
    SeparatedNSGA2 = "SeparatedNSGA2"
    SeparatedNSGA2xNSGA2 = "SeparatedNSGA2xNSGA2"


type hyperparams_t = dict[str, float | int | str | hyperparams_t]


class Optimiser(pydantic.BaseModel):
    name: OptimiserEnum = pydantic.Field(default=OptimiserEnum.NSGA2, description="Name of optimiser.")
    hyperparameters: hyperparams_t | None = pydantic.Field(
        default=None, description="Hyperparameters provided to the optimiser."
    )


class TaskConfig(pydantic.BaseModel):
    task_id: pydantic.UUID7 = pydantic.Field(description="Unique ID for this specific task.")
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
                    "dataset_ids": {"HeatingLoad": uuid7()},
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
    portfolio_id: dataset_id_t
    task_data: dict[site_id_t, TaskDataPydantic]
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
