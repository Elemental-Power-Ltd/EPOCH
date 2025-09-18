from __future__ import annotations

import datetime
import logging
import math
from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import AwareDatetime, BaseModel, Field, PositiveInt, PrivateAttr, model_validator

from app.internal.epoch import get_epoch_version
from app.internal.uuid7 import uuid7
from app.models.constraints import Constraints
from app.models.database import dataset_id_t
from app.models.epoch_types import SiteRange
from app.models.epoch_types.task_data_type import TaskData as TaskDataPydantic
from app.models.metrics import Metric
from app.models.optimisers import OptimiserTypes
from app.models.site_data import EpochSiteData, site_metadata_t

logger = logging.getLogger("default")


class Site(BaseModel):
    name: str = Field(description="Human readable name for a building. Must be unique to portfolio.")
    site_range: SiteRange = Field(description="Site range to optimise over.")
    site_data: site_metadata_t = Field(
        examples=[{"site_id": "amcott_house", "start_ts": "2022-01-01T00:00:00+00:00", "end_ts": "2022-01-01T00:00:00+00:00"}],
        description="Data to fetch for EPOCH to ingest.",
    )
    constraints: Constraints = Field(
        description="Minimum or maximum bounds to apply on site metrics.", examples=[{Metric.capex: {"max": 50000}}], default={}
    )
    _epoch_data: EpochSiteData = PrivateAttr()
    _epoch_data_dir: Path = PrivateAttr()

    @model_validator(mode="after")
    def check_tariff_index(self) -> Self:
        """
        Check that all the tariff indices in the site range correspond to real tariffs.

        Returns
        -------
        self
            If we passed the check

        Raises
        ------
        ValueError
            If any tariff indices are outside the range of available tariffs
        """
        if self.site_range.grid is None:
            # If we've got no grid, then it doesn't matter what tariff we look at
            return self
        if not hasattr(self, "_epoch_data"):
            # We haven't initialised the data yet
            return self
        tariff_indices = self.site_range.grid.tariff_index
        available_tariffs = len(self._epoch_data.import_tariffs)
        if not all(item <= available_tariffs for item in tariff_indices):
            raise ValueError(f"Requested tariff_index out of feasible range: {tariff_indices} but max is {available_tariffs}")
        return self

    @model_validator(mode="after")
    def check_fabric_index(self) -> Self:
        """
        Check that all the fabric indices in the site range correspond to real heatloads.

        Returns
        -------
        self
            If we passed the check

        Raises
        ------
        ValueError
            If any fabric indices are outside the range of available heatloads
        """
        if self.site_range.building is None:
            # If we've got no building, then it doesn't matter what tariff we look at
            return self
        if not hasattr(self, "_epoch_data"):
            # We haven't initialised the data yet
            return self
        fabric_indices = self.site_range.building.fabric_intervention_index

        available_fabrics = len(self._epoch_data.fabric_interventions)
        if not all(item <= available_fabrics for item in fabric_indices):
            raise ValueError(f"Requested fabric_index out of feasible range: {fabric_indices} but max is {available_fabrics}")
        return self


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
    epoch_version: str | None = Field(
        description="EPOCH version that this task was submitted for", default_factory=get_epoch_version
    )


class TaskResponse(BaseModel):
    task_id: dataset_id_t


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
    metrics: SimulationMetrics = Field(description="The metrics calculated for this site.")


class PortfolioOptimisationResult(BaseModel):
    """Result for a whole portfolio optimisation task, often one entry in the Pareto front."""

    task_id: dataset_id_t
    portfolio_id: dataset_id_t = Field(
        description="Individual ID representing this entry in the portfolio pareto front,"
        + " used to link to SiteOptimisationResults."
    )
    metrics: SimulationMetrics = Field(description="The metrics calculated across the whole portfolio.")
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
