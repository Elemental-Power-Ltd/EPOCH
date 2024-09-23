from enum import StrEnum
from typing import Mapping, TypedDict

OldParameterDict = Mapping[str, list[int | float] | tuple[int | float] | int | float]


class Objectives(StrEnum):
    carbon_balance = "carbon_balance"
    cost_balance = "cost_balance"
    capex = "capex"
    payback_horizon = "payback_horizon"
    annualised_cost = "annualised_cost"


class ParamRange(TypedDict):
    min: int | float
    max: int | float
    step: int | float


ParametersWRange = [
    "ASHP_HPower",
    "ASHP_HSource",
    "ASHP_HotTemp",
    "ASHP_RadTemp",
    "ESS_capacity",
    "ESS_charge_mode",
    "ESS_charge_power",
    "ESS_discharge_mode",
    "ESS_discharge_power",
    "ESS_start_SoC",
    "EV_flex",
    "Export_headroom",
    "Fixed_load1_scalar",
    "Fixed_load2_scalar",
    "Flex_load_max",
    "GridExport",
    "GridImport",
    "Import_headroom",
    "Min_power_factor",
    "Mop_load_max",
    "ScalarHL1",
    "ScalarHYield",
    "ScalarRG1",
    "ScalarRG2",
    "ScalarRG3",
    "ScalarRG4",
    "f22_EV_CP_number",
    "r50_EV_CP_number",
    "s7_EV_CP_number",
    "u150_EV_CP_number",
]

ParametersWORange = [
    "CAPEX_limit",
    "Export_kWh_price",
    "OPEX_limit",
    "target_max_concurrency",
    "time_budget_min",
    "timestep_hours",
]


class ParameterDict(TypedDict):
    ASHP_HPower: ParamRange
    ASHP_HSource: ParamRange
    ASHP_HotTemp: ParamRange
    ASHP_RadTemp: ParamRange
    ESS_capacity: ParamRange
    ESS_charge_mode: ParamRange
    ESS_charge_power: ParamRange
    ESS_discharge_mode: ParamRange
    ESS_discharge_power: ParamRange
    ESS_start_SoC: ParamRange
    EV_flex: ParamRange
    Export_headroom: ParamRange
    Fixed_load1_scalar: ParamRange
    Fixed_load2_scalar: ParamRange
    Flex_load_max: ParamRange
    GridExport: ParamRange
    GridImport: ParamRange
    Import_headroom: ParamRange
    Min_power_factor: ParamRange
    Mop_load_max: ParamRange
    ScalarHL1: ParamRange
    ScalarHYield: ParamRange
    ScalarRG1: ParamRange
    ScalarRG2: ParamRange
    ScalarRG3: ParamRange
    ScalarRG4: ParamRange
    f22_EV_CP_number: ParamRange
    r50_EV_CP_number: ParamRange
    s7_EV_CP_number: ParamRange
    u150_EV_CP_number: ParamRange
    CAPEX_limit: int | float
    Export_kWh_price: int | float
    OPEX_limit: int | float
    target_max_concurrency: int | float
    time_budget_min: int | float
    timestep_hours: int | float


class Bounds(TypedDict):
    min: int | float
    max: int | float


ConstraintDict = Mapping[str, Bounds]
