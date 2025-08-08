import datetime
import logging
from pathlib import Path

from pydantic import AwareDatetime, BaseModel, Field, PositiveInt, PrivateAttr

from app.internal.uuid7 import uuid7
from app.models.constraints import Constraints
from app.models.database import dataset_id_t
from app.models.epoch_types import SiteRange, TaskDataPydantic
from app.models.metrics import Metric
from app.models.optimisers import OptimiserTypes
from app.models.site_data import EpochSiteData, SiteMetaData

logger = logging.getLogger("default")

# We try to import the EPOCH simulator here to use it in the TaskData if it wasn't provided.
try:
    import epoch_simulator

    epoch_version_ = epoch_simulator.__version__  # type: ignore
except ImportError:
    epoch_version_ = None


class Site(BaseModel):
    name: str = Field(description="Human readable name for a building. Must be unique to portfolio.")
    site_range: SiteRange = Field(description="Site range to optimise over.")
    site_data: SiteMetaData = Field(
        examples=[{"loc": "local", "site_id": "amcott_house", "path": "./data/InputData"}],
        description="Location to fetch input data from for EPOCH to ingest.",
    )
    constraints: Constraints = Field(
        description="Minimum or maximum bounds to apply on site metrics.", examples=[{Metric.capex: {"max": 50000}}], default={}
    )
    _epoch_data: EpochSiteData = PrivateAttr()
    _epoch_data_dir: Path = PrivateAttr()


class EndpointTask(Site):
    optimiser: OptimiserTypes = Field(description="Optimiser name and hyperparameters.")
    objectives: list[Metric] = Field(examples=[["carbon_cost"]], description="List of objectives to optimise for.")
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
    optimiser: OptimiserTypes = Field(description="Optimiser name and hyperparameters.")
    objectives: list[Metric] = Field(examples=[["capex", "carbon_balance"]], description="List of objectives to optimise for.")
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        description="The time this Task was created and added to the queue.",
    )
    portfolio: list[Site] = Field(description="List of buildings in portfolio.")
    portfolio_constraints: Constraints = Field(
        description="Minimum or maximum bounds to apply on portfolio metrics.", examples=[{Metric.capex: {"max": 500000}}]
    )
    client_id: str = Field(
        examples=["demo"],
        description="The database ID for a client, all lower case, joined by underscores.",
    )
    task_id: dataset_id_t = Field(
        default_factory=uuid7,
        description="Unique ID (generally a UUIDv7) of an optimisation task.",
    )
    epoch_version: str | None = Field(description="EPOCH version that this task was submitted for", default=epoch_version_)


class TaskResponse(BaseModel):
    task_id: dataset_id_t


class SiteMetrics(BaseModel):
    """Metrics for a single site within a portfolio."""

    carbon_balance_scope_1: float | None = Field(
        description="Direct carbon emissions saved by this scenario on this site.", default=None, examples=[None, 3.14]
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


class SiteOptimisationResult(BaseModel):
    """Result for a single site within a portfolio result."""

    site_id: str = Field(
        examples=["demo_london"],
        description="The database ID for a site, all lower case, joined by underscores.",
    )
    portfolio_id: dataset_id_t = Field(
        description="The portfolio pareto front entry this site is linked to."
        + " A single site result is uniquely identified by a (portfolio_id, site_id) pair."
    )
    scenario: TaskDataPydantic = Field(description="The mix of assets used in this scenario, e.g. solar PV and grid connects.")
    metrics: SiteMetrics = Field(description="The metrics calculated for this site.")


class PortfolioMetrics(BaseModel):
    """Metrics for the whole portfolio."""

    carbon_balance_scope_1: float | None = Field(
        description="Direct carbon emissions saved by this entire portfolio of scenarios.", default=None, examples=[None, 3.14]
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


class PortfolioOptimisationResult(BaseModel):
    """Result for a whole portfolio optimisation task, often one entry in the Pareto front."""

    task_id: dataset_id_t
    portfolio_id: dataset_id_t = Field(
        description="Individual ID representing this entry in the portfolio pareto front,"
        + " used to link to SiteOptimisationResults."
    )
    metrics: PortfolioMetrics = Field(description="The metrics calculated across the whole portfolio.")
    site_results: list[SiteOptimisationResult] | None = Field(
        default=None,
        description="Individual site results for this Portfolio."
        + " Not provided when requesting a specific portfolio from the DB.",
    )


class TaskResult(BaseModel):
    """Result for metadata about an optimisation task."""

    task_id: dataset_id_t
    n_evals: PositiveInt = Field(description="Number of site scenarios evaluated during this task.", examples=[1, 9999])
    exec_time: datetime.timedelta = Field(description="Wall-clock time this optimisation run took.")
    completed_at: AwareDatetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        description="The wall-clock time this optimisation run concluded at.",
    )


class OptimisationResultEntry(BaseModel):
    portfolio: list[PortfolioOptimisationResult] = Field(description="List of total portfolio result data")
    tasks: TaskResult = Field(description="Task optimisation result metadata, e.g. run time")
