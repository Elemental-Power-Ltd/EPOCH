"""Models for EPOCH/GA optimisation tasks, both queuing and completing."""

from __future__ import annotations

# ruff: noqa: D101
import datetime
import math
from enum import StrEnum

import pydantic
from pydantic import BaseModel, Field

from .core import client_id_t, dataset_id_t, site_id_field, site_id_t
from .epoch_types import TaskDataPydantic
from .site_manager import BundleHints, SiteDataEntry
from .site_range import SiteRange


class MinMaxParam[T: float | int](pydantic.BaseModel):
    min: T
    max: T
    count: int


type ValuesParam = list[int] | list[float] | list[str]

type FixedParam = int | float | str


class Param(pydantic.BaseModel):
    name: str
    units: str | None
    considered: ValuesParam | MinMaxParam[float] | MinMaxParam[int] | FixedParam


type component_t = str
type gui_param_dict = dict[str, Param]


class Grade(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class CostInfo(BaseModel):
    name: str = Field(examples=["Solar Panel"], description="Display name for this cost item.")
    component: str | None = Field(
        examples=["solar_panel"], description="Key of the EPOCH component type this cost belongs to.", default=None
    )
    cost: float = Field(
        examples=[1200.0], description="The net cost of the item in pounds, including all sub_components minus any funding."
    )
    sub_components: list[CostInfo] = Field(
        description="The sub-components that make up this cost item, or the empty list if there are none.", default_factory=list
    )


class SimulationMetrics(BaseModel):
    """Metrics for a site or portfolio of sites."""

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
        description="The change in Net Present Value between the baseline and the scenario.", default=None
    )
    payback_horizon: float | None = Field(
        description="Years for this scenario to pay back (if very large, represents no payback ever.)",
        default=None,
    )
    return_on_investment: float | None = Field(
        description="Yearly return on investment (operating balance / capex) as a decimal percentage. "
        + "None when no money was spent.",
        default=None,
    )
    carbon_balance_scope_1: float | None = Field(
        description="Direct carbon emissions saved by this scenario.", default=None, examples=[None, math.pi]
    )
    carbon_balance_scope_2: float | None = Field(
        description="Net kg CO2e over the lifetime of these interventions for scope 2.", default=None
    )
    carbon_balance_total: float | None = Field(
        description="Net kg CO2e saved from both scope 1 and scope 2 emissions",
        default=None,
    )
    carbon_cost: float | None = Field(description="Net £ per t CO2e over the lifetime of these interventions.", default=None)
    total_gas_used: float | None = Field(description="Total gas imported (kWh).", default=None)
    total_electricity_imported: float | None = Field(
        description="Total electricity imported from the grid (kWh).", default=None
    )
    total_electricity_generated: float | None = Field(description="Total electricity generated on-site (kWh).", default=None)
    total_electricity_exported: float | None = Field(description="Total electricity exported to the grid (kWh).", default=None)
    total_electricity_curtailed: float | None = Field(
        description="Total electricity surplus that could not be exported (kWh).", default=None
    )
    total_electricity_used: float | None = Field(description="Total electricity used (kWh).", default=None)
    total_electrical_shortfall: float | None = Field(
        description="Total electrical shortfall (kWh) when compared to the demand.", default=None
    )
    total_heat_load: float | None = Field(description="Total heat used (kWh).", default=None)
    total_dhw_load: float | None = Field(description="Total heat used for domestic hot water (kWh).", default=None)
    total_ch_load: float | None = Field(description="Total heat used for central heating (kWh).", default=None)
    total_heat_shortfall: float | None = Field(
        description="Total heat shortfall (kWh) when compared to the demand.", default=None
    )
    total_ch_shortfall: float | None = Field(
        description="Total central heating (CH) shortfall (kWh) when compared to the demand.", default=None
    )
    total_dhw_shortfall: float | None = Field(
        description="Total domestic hot water (DHW) shortfall (kWh) when compared to the demand.", default=None
    )
    peak_hload_shortfall: float | None = Field(
        description="Shortfall in meeting the peak heating demand calculated by an external source (such as PHPP)", default=None
    )
    capex: float | None = Field(description="Cost to install this scenario.", default=None)
    total_gas_import_cost: float | None = Field(description="Total spend (£) importing gas.", default=None)
    total_electricity_import_cost: float | None = Field(
        description="Total spend (£) importing electricity from the grid.", default=None
    )
    total_electricity_export_gain: float | None = Field(
        description="Total income (£) exporting electricity to this grid.", default=None
    )

    total_meter_cost: float | None = Field(
        description="Total cost of importing fuel/electricity minus revenue from exporting.", default=None
    )
    total_operating_cost: float | None = Field(
        description="Total meter cost minus operating costs for components.", default=None
    )
    annualised_cost: float | None = Field(
        description="Cost of running this scenario (including amortised deprecation).", default=None
    )
    total_net_present_value: float | None = Field(
        description="Net Present Value after repeating the simulation for the configured number of years.",
        default=None,
    )
    total_scope_1_emissions: float | None = Field(description="Total Scope 1 emissions (kg CO2e).", default=None)
    total_scope_2_emissions: float | None = Field(description="Total Scope 2 emissions (kg CO2e).", default=None)
    total_combined_carbon_emissions: float | None = Field(description="Scope 1 and Scope 2 emissions (kg CO2e).", default=None)

    scenario_environmental_impact_score: int | None = Field(description="environmental impact score based on SAP", default=None)
    scenario_environmental_impact_grade: Grade | None = Field(description="environmental impact grade (A-G)", default=None)

    scenario_capex_breakdown: list[CostInfo] | None = Field(description="Breakdown of scenario expenditure.", default=None)

    baseline_gas_used: float | None = Field(description="Baseline gas imported (kWh).", default=None)
    baseline_electricity_imported: float | None = Field(
        description="Baseline electricity imported from the grid (kWh).", default=None
    )
    baseline_electricity_generated: float | None = Field(
        description="Baseline electricity generated on-site (kWh).", default=None
    )
    baseline_electricity_exported: float | None = Field(
        description="Baseline electricity exported to the grid (kWh).", default=None
    )
    baseline_electricity_curtailed: float | None = Field(
        description="Baseline electricity surplus that could not be exported (kWh).", default=None
    )
    baseline_electricity_used: float | None = Field(description="Baseline electricity used (kWh).", default=None)

    baseline_electrical_shortfall: float | None = Field(
        description="Baseline electrical shortfall (kWh) when compared to the demand.", default=None
    )
    baseline_heat_load: float | None = Field(description="Baseline heat used (kWh).", default=None)
    baseline_dhw_load: float | None = Field(description="Baseline heat used for domestic hot water (kWh).", default=None)
    baseline_ch_load: float | None = Field(description="Baseline heat used for central heating (kWh).", default=None)
    baseline_heat_shortfall: float | None = Field(
        description="Baseline heat shortfall (kWh) when compared to the demand.", default=None
    )
    baseline_ch_shortfall: float | None = Field(
        description="Baseline central heating (CH) shortfall (kWh) when compared to the demand.", default=None
    )
    baseline_dhw_shortfall: float | None = Field(
        description="Baseline domestic hot water (DHW) shortfall (kWh) when compared to the demand.", default=None
    )
    baseline_peak_hload_shortfall: float | None = Field(
        description="Baseline shortfall in meeting the peak heating demand calculated by an external source (such as PHPP)",
        default=None,
    )
    baseline_gas_import_cost: float | None = Field(description="Total spend (£) importing gas.", default=None)
    baseline_electricity_import_cost: float | None = Field(
        description="Baseline spend (£) importing electricity from the grid.", default=None
    )
    baseline_electricity_export_gain: float | None = Field(
        description="Baseline income (£) exporting electricity to this grid.", default=None
    )
    baseline_meter_cost: float | None = Field(
        description="Baseline cost of importing fuel/electricity minus revenue from exporting.", default=None
    )
    baseline_operating_cost: float | None = Field(
        description="Baseline meter cost minus operating costs for components.", default=None
    )
    baseline_net_present_value: float | None = Field(
        description="Baseline Net Present Value after repeating the simulation for the configured number of years.",
        default=None,
    )
    baseline_scope_1_emissions: float | None = Field(description="Baseline Scope 1 emissions (kg CO2e).", default=None)
    baseline_scope_2_emissions: float | None = Field(description="Baseline Scope 2 emissions (kg CO2e).", default=None)
    baseline_combined_carbon_emissions: float | None = Field(
        description="Baseline Scope 1 and Scope 2 emissions (kg CO2e).", default=None
    )
    baseline_environmental_impact_score: int | None = Field(
        description="baseline environmental impact score based on SAP", default=None
    )
    baseline_environmental_impact_grade: Grade | None = Field(
        description="baseline environmental impact grade (A-G)", default=None
    )


class SiteOptimisationResult(pydantic.BaseModel):
    """Result for a single site within a portfolio result."""

    site_id: site_id_t = site_id_field
    portfolio_id: dataset_id_t = pydantic.Field(
        description="The portfolio pareto front entry this site is linked to."
        + " A single site result is uniquely identified by a (portfolio_id, site_id) pair."
    )
    scenario: TaskDataPydantic = pydantic.Field(
        description="The mix of assets used in this scenario, e.g. solar PV and grid connects."
    )
    metrics: SimulationMetrics = pydantic.Field(description="The metrics calculated for this site.")
    is_feasible: bool | None = pydantic.Field(
        description="Indicates whether the result is feasible or not given the task's constraints."
    )


class PortfolioOptimisationResult(pydantic.BaseModel):
    """Result for a whole portfolio optimisation task, often one entry in the Pareto front."""

    task_id: dataset_id_t
    portfolio_id: dataset_id_t = pydantic.Field(
        description="Individual ID representing this entry in the portfolio pareto front,"
        + " used to link to SiteOptimisationResults."
    )
    metrics: SimulationMetrics = pydantic.Field(description="The metrics calculated across the whole portfolio.")
    site_results: list[SiteOptimisationResult] | None = pydantic.Field(
        default=None,
        description="Individual site results for this Portfolio."
        + " Not provided when requesting a specific portfolio from the DB.",
    )
    is_feasible: bool | None = pydantic.Field(
        description="Indicates whether the result is feasible or not given the task's constraints."
    )


class HighlightReason(StrEnum):
    BestCostBalance = "best_cost_balance"
    BestCarbonBalance = "best_carbon_balance"
    BestPaybackHorizon = "best_payback_horizon"
    BestReturnOnInvestment = "best_return_on_investment"
    UserCurated = "user_curated"


class HighlightedResult(pydantic.BaseModel):
    """A portfolio result we want to draw attention to and a reason why."""

    portfolio_id: dataset_id_t = pydantic.Field(
        description="Individual ID representing this entry in the portfolio pareto front."
    )
    reason: HighlightReason = pydantic.Field(description="The reason the portfolio result is highlighted.")
    display_name: str = pydantic.Field(description="A human readable version of the highlight reason.")
    suggested_metric: str | None = pydantic.Field(
        description="A key to the most appropriate metric to display/sort by when considering this result."
    )


class SearchInfo(pydantic.BaseModel):
    total_options_considered: int = pydantic.Field(description="The total number of permutations for this portfolio.")
    site_options_considered: dict[site_id_t, int] = pydantic.Field(description="The number of permutations for each site.")


class OptimisationResultsResponse(pydantic.BaseModel):
    """Response containing all saved results for a given task_id and some highlighted results."""

    portfolio_results: list[PortfolioOptimisationResult] = pydantic.Field(
        description="Result for a whole portfolio optimisation task, often one entry in the Pareto front."
    )
    highlighted_results: list[HighlightedResult] = pydantic.Field(
        description="A list of highlighted results, containing a portfolio_id and the reason the result is highlighted."
    )
    hints: dict[site_id_t, BundleHints] = pydantic.Field(
        default={},
        description="Descriptive information about the data we've used to generate this result."
        " This contains names and metadata about tariffs and renewables installations.",
    )
    search_spaces: dict[site_id_t, dict[component_t, gui_param_dict | list[gui_param_dict]]] = pydantic.Field(
        default={},
        description="Information about the components we've searched over to give you this result."
        " For each site, shows you the components and the parameters for each component we checked.",
    )
    search_info: SearchInfo = pydantic.Field(description="Supporting information about the optimisation.")


class TaskResult(pydantic.BaseModel):
    """Result for metadata about an optimisation task."""

    task_id: dataset_id_t
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
    MergeOperator = "MergeOperator"


type hyperparams_t = dict[str, float | int | str | hyperparams_t]


class Optimiser(pydantic.BaseModel):
    name: OptimiserEnum = pydantic.Field(default=OptimiserEnum.NSGA2, description="Name of optimiser.")
    hyperparameters: hyperparams_t | None = pydantic.Field(
        default=None, description="Hyperparameters provided to the optimiser."
    )


class TaskConfig(pydantic.BaseModel):
    task_id: dataset_id_t = pydantic.Field(description="Unique ID for this specific task.")
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
    optimiser: Optimiser = pydantic.Field(
        description="The optimisation algorithm for the backend to use in these calculations."
    )
    created_at: pydantic.AwareDatetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        description="The time this Task was created and added to the queue.",
    )
    epoch_version: str | None = pydantic.Field(
        default=None, description="The EPOCH version this task was created with; None if unknown"
    )
    bundle_ids: dict[site_id_t, dataset_id_t] = pydantic.Field(description="The data bundle id for each site.")


class ResultReproConfig(pydantic.BaseModel):
    portfolio_id: dataset_id_t
    task_data: dict[site_id_t, TaskDataPydantic]


class NewResultReproConfig(ResultReproConfig):
    bundle_ids: dict[site_id_t, dataset_id_t]


class LegacyResultReproConfig(ResultReproConfig):
    site_data: dict[site_id_t, SiteDataEntry]


type result_repro_config_t = NewResultReproConfig | LegacyResultReproConfig


class OptimisationTaskListRequest(pydantic.BaseModel):
    client_id: client_id_t
    limit: int | None = pydantic.Field(description="The maximum number of items to return.", gt=0, default=None)
    offset: int | None = pydantic.Field(description="The starting index to return.", ge=0, default=None)


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
    created_at: pydantic.AwareDatetime = pydantic.Field(
        description="The time this Task was created and added to the queue.",
    )
    epoch_version: str | None = pydantic.Field(description="The version of EPOCH used to generate these results.")
    objectives: list[str] = pydantic.Field(description="The objectives this task was optimised for.")


class OptimisationTaskListResponse(pydantic.BaseModel):
    tasks: list[OptimisationTaskListEntry] = pydantic.Field(description="The requested subset of the tasks.")
    total_results: int = pydantic.Field(description="The total number of results we have.")


class AddCuratedResultRequest(pydantic.BaseModel):
    task_id: dataset_id_t = pydantic.Field(description="The Task ID this result belongs to.")
    portfolio_id: dataset_id_t = pydantic.Field(description="The portfolio id of the result we want to highlight.")
    display_name: str = pydantic.Field(description="The display name for the reason this result has been highlighted. "
                                       + "This should not start with the word 'Best'.", default="Curated")


class CuratedResult(pydantic.BaseModel):
    highlight_id: dataset_id_t = pydantic.Field(description="The unique ID for this highlight.")
    task_id: dataset_id_t = pydantic.Field(description="The Task ID this result belongs to.")
    portfolio_id: dataset_id_t = pydantic.Field(description="The portfolio id of the result we want to highlight.")
    submitted_at: pydantic.AwareDatetime = pydantic.Field(
        description="The time when this result was marked as a curated result.",
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
    )
    display_name: str = pydantic.Field(description="The display name for the reason this result has been highlighted.")


class ListCuratedResultsResponse(pydantic.BaseModel):
    curated_results: list[CuratedResult] = pydantic.Field(description="The curated results.")
