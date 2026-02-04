from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class PanelInfo(BaseModel):
    solar_peak: float = Field(ge=0.0)
    direction: Literal["North", "East", "South", "West"]  # Chose one of the four solar data arrays


class HeatInfo(BaseModel):
    heat_power: float = Field(gt=0.0)
    heat_source: Literal["Boiler", "HeatPump"]


class InsulationInfo(BaseModel):
    double_glazing: bool
    cladding: bool
    loft: bool


class BatteryInfo(BaseModel):
    capacity: float = Field(gt=0.0)
    power: float = Field(gt=0.0)


Location = Literal["Cardiff", "London", "Edinburgh"]
BuildingType = Literal["Domestic", "TownHall", "LeisureCentre"]


class SimulationRequest(BaseModel):
    # SiteData configuration
    location: Location
    building: BuildingType

    # TaskData configuration
    panels: list[PanelInfo]
    heat: HeatInfo
    insulation: InsulationInfo
    battery: BatteryInfo | None

    # Result configuration
    full_reporting: bool = False


class RatingGrade(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class ScenarioComparison(BaseModel):
    meter_balance: float
    operating_balance: float
    cost_balance: float
    npv_balance: float
    payback_horizon_years: float
    return_on_investment: float | None
    carbon_balance_scope_1: float
    carbon_balance_scope_2: float
    combined_carbon_balance: float
    carbon_cost: float


class SimulationMetrics(BaseModel):
    total_gas_used: float
    total_electricity_imported: float
    total_electricity_generated: float
    total_electricity_exported: float
    total_electricity_curtailed: float
    total_electricity_used: float

    total_heat_load: float
    total_dhw_load: float
    total_ch_load: float

    total_electrical_shortfall: float
    total_heat_shortfall: float
    total_ch_shortfall: float
    total_dhw_shortfall: float
    peak_hload_shortfall: float

    total_capex: float
    total_gas_import_cost: float
    total_electricity_import_cost: float
    total_electricity_export_gain: float

    total_meter_cost: float
    total_operating_cost: float
    total_annualised_cost: float
    total_net_present_value: float

    total_scope_1_emissions: float
    total_scope_2_emissions: float
    total_combined_carbon_emissions: float

    environmental_impact_score: int | None
    environmental_impact_grade: RatingGrade | None


class FabricCostBreakdown(BaseModel):
    name: str
    area: float | None
    cost: float


class CapexBreakdown(BaseModel):
    building_fabric_capex: float
    fabric_cost_breakdown: list[FabricCostBreakdown]
    dhw_capex: float
    ev_charger_cost: float
    ev_charger_install: float
    gas_heater_capex: float
    grid_capex: float
    heatpump_capex: float
    ess_pcs_capex: float
    ess_enclosure_capex: float
    ess_enclosure_disposal: float
    pv_panel_capex: float
    pv_roof_capex: float
    pv_ground_capex: float
    pv_BoP_capex: float
    boiler_upgrade_scheme_funding: float
    general_grant_funding: float
    total_capex: float


class SimulationResult(BaseModel):
    comparison: ScenarioComparison
    metrics: SimulationMetrics
    baseline_metrics: SimulationMetrics
    scenario_capex_breakdown: CapexBreakdown
    report_data: Any
