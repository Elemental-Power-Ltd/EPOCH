"""
Provide type hints for epoch_simulator that mypy can use.

This works a bit like a C header file; mypy can't see into the pybind library
to identify the types involve, so we write them out manually here.
You can't import this file, but it's useful for static analysis.
"""
import typing

class SimulationResult:
    carbon_balance: float
    cost_balance: float
    capex: float
    payback_horizon: float
    annualised_cost: float
    report_data: typing.Any

class TaskData:
    ASHP_HPower: float
    ASHP_HSource: float
    ASHP_HotTemp: float
    ASHP_RadTemp: float
    CAPEX_limit: float
    ESS_capacity: float
    ESS_charge_mode: int
    ESS_charge_power: float
    ESS_discharge_mode: int
    ESS_discharge_power: float
    ESS_start_SoC: float
    EV_flex: float
    Export_headroom: float
    Export_kWh_price: float
    Fixed_load1_scalar: float
    Fixed_load2_scalar: float
    Flex_load_max: float
    GridExport: float
    GridImport: float
    Import_headroom: float
    Min_power_factor: float
    Mop_load_max: float
    OPEX_limit: float
    ScalarHL1: float
    ScalarHYield: float
    ScalarRG1: float
    ScalarRG2: float
    ScalarRG3: float
    ScalarRG4: float
    f22_EV_CP_number: float
    r50_EV_CP_number: float
    s7_EV_CP_number: float
    target_max_concurrency: int
    time_budget_min: float
    u150_EV_CP_number: float

class Simulator:
    def __init__(self, inputDir: str = ..., outputDir: str = ..., configDir: str = ...): ...
    def simulate_scenario(self, taskData: TaskData, fullReporting: bool = False) -> SimulationResult: ...
