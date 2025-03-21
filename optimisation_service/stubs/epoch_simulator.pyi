"""
Provide type hints for epoch_simulator that mypy can use.

This works a bit like a C header file; mypy can't see into the pybind library
to identify the types involve, so we write them out manually here.
You can't import this file, but it's useful for static analysis.
"""

import typing
from enum import Enum

class SimulationMetrics:
    total_gas_used: float
    total_electricity_imported: float
    total_electricity_generated: float
    total_electricity_exported: float

    total_electrical_shortfall: float
    total_heat_shortfall: float

    total_gas_import_cost: float
    total_electricity_import_cost: float
    total_electricity_export_gain: float

class SimulationResult:
    carbon_balance_scope_1: float
    carbon_balance_scope_2: float
    cost_balance: float
    capex: float
    payback_horizon: float
    annualised_cost: float
    metrics: SimulationMetrics
    report_data: typing.Any

class Config:
    capex_limit: float

class Building:
    scalar_heat_load: float
    scalar_electrical_load: float
    fabric_intervention_index: int

class DataCentre:
    maximum_load: float
    hotroom_temp: float

class DomesticHotWater:
    cylinder_volume: float

class ElectricVehicles:
    flexible_load_ratio: float
    small_chargers: int
    fast_chargers: int
    rapid_chargers: int
    ultra_chargers: int
    scalar_electrical_load: float

class BatteryMode(Enum):
    CONSUME = "CONSUME"
    CONSUME_PLUS = "CONSUME_PLUS"

class EnergyStorageSystem:
    capacity: float
    charge_power: float
    discharge_power: float
    battery_mode: BatteryMode
    initial_charge: float

class GasType(Enum):
    NATURAL_GAS = "NATURAL_GAS"
    LIQUID_PETROLEUM_GAS = "LIQUID_PETROLEUM_GAS"

class GasHeater:
    maximum_output: float
    gas_type: GasType
    boiler_efficiency: float

class Grid:
    grid_export: float
    grid_import: float
    import_headroom: float
    tariff_index: int

class HeatSource(Enum):
    AMBIENT_AIR = "AMBIENT_AIR"
    HOTROOM = "HOTROOM"

class HeatPump:
    heat_power: float
    heat_source: HeatSource
    send_temp: float

class Mop:
    maximum_load: float

class Renewables:
    yield_scalars: list[float]

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
    renewables: Renewables

    @staticmethod
    def from_json(json_str: str) -> TaskData: ...

class CapexBreakdown:
    dhw_capex: float
    ev_charger_cost: float
    ev_charger_install: float
    grid_capex: float
    heatpump_capex: float
    ess_pcs_capex: float
    ess_enclosure_capex: float
    ess_enclosure_disposal: float
    pv_panel_capex: float
    pv_roof_capex: float
    pv_ground_capex: float
    pv_BoP_capex: float
    total_capex: float

class Simulator:
    @staticmethod
    def from_json(json_str: str) -> Simulator: ...
    @staticmethod
    def from_file(filepath: str) -> Simulator: ...
    def simulate_scenario(self, taskData: TaskData, fullReporting: bool = False) -> SimulationResult: ...
    def is_valid(self, taskData: TaskData) -> bool: ...
    def calculate_capex(self, taskData: TaskData) -> CapexBreakdown: ...
