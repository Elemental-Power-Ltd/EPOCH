"""
Provide type hints for epoch_simulator that mypy can use.

This works a bit like a C header file; mypy can't see into the pybind library
to identify the types involve, so we write them out manually here.
You can't import this file, but it's useful for static analysis.
"""

import typing
from enum import Enum

__version__: str

class RatingGrade(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"

class SimulationMetrics:
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

class ScenarioComparison:
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

class SimulationResult:
    comparison: ScenarioComparison
    metrics: SimulationMetrics
    baseline_metrics: SimulationMetrics
    scenario_capex_breakdown: CapexBreakdown
    report_data: typing.Any

class Config:
    capex_limit: float
    use_boiler_upgrade_scheme: bool
    general_grant_funding: float
    npv_time_horizon: int
    npv_discount_factor: float

class Building:
    scalar_heat_load: float
    scalar_electrical_load: float
    fabric_intervention_index: int
    floor_area: float | None
    incumbent: bool
    age: float
    lifetime: float

class DataCentre:
    maximum_load: float
    hotroom_temp: float
    incumbent: bool
    age: float
    lifetime: float

class DomesticHotWater:
    cylinder_volume: float
    incumbent: bool
    age: float
    lifetime: float

class ElectricVehicles:
    flexible_load_ratio: float
    small_chargers: int
    fast_chargers: int
    rapid_chargers: int
    ultra_chargers: int
    scalar_electrical_load: float
    incumbent: bool
    age: float
    lifetime: float

class BatteryMode(Enum):
    CONSUME = "CONSUME"
    CONSUME_PLUS = "CONSUME_PLUS"

class EnergyStorageSystem:
    capacity: float
    charge_power: float
    discharge_power: float
    battery_mode: BatteryMode
    initial_charge: float
    incumbent: bool
    age: float
    lifetime: float

class GasType(Enum):
    NATURAL_GAS = "NATURAL_GAS"
    LIQUID_PETROLEUM_GAS = "LIQUID_PETROLEUM_GAS"

class GasHeater:
    maximum_output: float
    gas_type: GasType
    boiler_efficiency: float
    fixed_gas_price: float
    incumbent: bool
    age: float
    lifetime: float

class Grid:
    grid_export: float
    grid_import: float
    import_headroom: float
    tariff_index: int
    incumbent: bool
    age: float
    lifetime: float

class HeatSource(Enum):
    AMBIENT_AIR = "AMBIENT_AIR"
    HOTROOM = "HOTROOM"

class HeatPump:
    heat_power: float
    heat_source: HeatSource
    send_temp: float
    incumbent: bool
    age: float
    lifetime: float

class Mop:
    maximum_load: float
    incumbent: bool
    age: float
    lifetime: float

class SolarPanel:
    yield_scalar: float
    yield_index: int
    incumbent: bool
    age: float
    lifetime: float

class TaskData:
    config: Config
    building: Building
    data_centre: DataCentre
    domestic_hot_water: DomesticHotWater
    electric_vehicles: ElectricVehicles
    energy_storage_system: EnergyStorageSystem
    gas_heater: GasHeater
    grid: Grid
    heat_pump: HeatPump
    mop: Mop
    solar_panels: list[SolarPanel]

    @staticmethod
    def from_json(json_str: str) -> TaskData: ...
    def to_json(self) -> str: ...

class CapexBreakdown:
    building_fabric_capex: float
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

class Simulator:
    @staticmethod
    def from_json(site_data_json_str: str, config_json_str: str) -> Simulator: ...
    @staticmethod
    def from_file(site_data_filepath: str, config_filepath: str) -> Simulator: ...
    def simulate_scenario(self, taskData: TaskData, fullReporting: bool = False) -> SimulationResult: ...
    def is_valid(self, taskData: TaskData) -> bool: ...
    def calculate_capex(self, taskData: TaskData) -> CapexBreakdown: ...

def aggregate_site_results(site_results: list[SimulationResult]) -> SimulationResult: ...
