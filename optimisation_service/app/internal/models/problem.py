from typing import Mapping, TypedDict

OldParameterDict = Mapping[str, list[int | float] | tuple[int | float] | int | float]


class ParamRange(TypedDict):
    min: int | float
    max: int | float
    step: int | float


ParamConst = int | float


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
    CAPEX_limit: ParamConst
    Export_kWh_price: ParamConst
    OPEX_limit: ParamConst
    target_max_concurrency: ParamConst
    time_budget_min: ParamConst
    timestep_hours: ParamConst


class Bounds(TypedDict):
    min: int | float | None = None
    max: int | float | None = None


ConstraintDict = Mapping[str, Bounds]
