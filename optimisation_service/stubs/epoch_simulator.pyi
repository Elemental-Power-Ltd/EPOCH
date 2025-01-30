"""
Provide type hints for epoch_simulator that mypy can use.

This works a bit like a C header file; mypy can't see into the pybind library
to identify the types involve, so we write them out manually here.
You can't import this file, but it's useful for static analysis.
"""

import typing
from enum import Enum

class SimulationResult:
    carbon_balance_scope_1: float
    carbon_balance_scope_2: float
    cost_balance: float
    capex: float
    payback_horizon: float
    annualised_cost: float
    report_data: typing.Any

class Config:
    capex_limit: float

class Building:
    scalar_heat_load: str
    scalar_electrical_load: str
    fabric_intervention_index: int

class DataCentre:
    maximum_load: str
    hotroom_temp: str

class DomesticHotWater:
    cylinder_volume: str

class ElectricVehicles:
    flexible_load_ratio: str
    small_chargers: int
    fast_chargers: int
    rapid_chargers: int
    ultra_chargers: int
    scalar_electrical_load: str

class BatteryMode(Enum):
    CONSUME = "CONSUME"

class EnergyStorageSystem:
    capacity: float
    charge_power: float
    discharge_power: float
    battery_mode: BatteryMode
    initial_charge: float

class Grid:
    export_headroom: float
    grid_export: float
    grid_import: float
    import_headroom: float
    min_power_factor: float
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
    grid: Grid
    heat_pump: HeatPump
    mop: Mop
    renewables: Renewables

    @staticmethod
    def from_json(json_str: str) -> TaskData: ...

class Simulator:
    def __init__(self, inputDir: str = ..., outputDir: str = ..., configDir: str = ...): ...
    def simulate_scenario(self, taskData: TaskData, fullReporting: bool = False) -> SimulationResult: ...
