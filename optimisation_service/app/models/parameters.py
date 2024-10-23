from collections.abc import Mapping
from typing import Final, TypedDict

from pydantic import BaseModel, Field

ParametersWRange: Final = [
    "Fixed_load1_scalar",
    "Fixed_load2_scalar",
    "Flex_load_max",
    "Mop_load_max",
    "ScalarRG1",
    "ScalarRG2",
    "ScalarRG3",
    "ScalarRG4",
    "ScalarHYield",
    "s7_EV_CP_number",
    "f22_EV_CP_number",
    "r50_EV_CP_number",
    "u150_EV_CP_number",
    "EV_flex",
    "ASHP_HPower",
    "ASHP_HSource",
    "ASHP_RadTemp",
    "ASHP_HotTemp",
    "ScalarHL1",
    "GridImport",
    "GridExport",
    "Import_headroom",
    "Export_headroom",
    "Min_power_factor",
    "ESS_charge_power",
    "ESS_discharge_power",
    "ESS_capacity",
    "ESS_start_SoC",
    "ESS_charge_mode",
    "ESS_discharge_mode",
    "DHW_cylinder_volume",
]

ParametersWORange: Final = [
    "Export_kWh_price",
    "time_budget_min",
    "target_max_concurrency",
    "timestep_hours",
    "CAPEX_limit",
    "OPEX_limit",
    "timewindow",
]

param_range = Field(
    examples=[{"min": 0, "max": 10, "step": 1}, {"min": 10, "max": 10, "step": 0}],
    description="Dictionary to define parameter range for EPOCH to consume."
    + "Range max must be greater than range min."
    + "Range step must be 0 if min = max and vice versa.",
)


class EndpointParamRange(BaseModel):
    min: int | float
    max: int | float
    step: int | float


class EndpointParameterDict(BaseModel):
    ASHP_HPower: EndpointParamRange = param_range
    ASHP_HSource: EndpointParamRange = param_range
    ASHP_HotTemp: EndpointParamRange = param_range
    ASHP_RadTemp: EndpointParamRange = param_range
    ESS_capacity: EndpointParamRange = param_range
    ESS_charge_mode: EndpointParamRange = param_range
    ESS_charge_power: EndpointParamRange = param_range
    ESS_discharge_mode: EndpointParamRange = param_range
    ESS_discharge_power: EndpointParamRange = param_range
    ESS_start_SoC: EndpointParamRange = param_range
    EV_flex: EndpointParamRange = param_range
    Export_headroom: EndpointParamRange = param_range
    Fixed_load1_scalar: EndpointParamRange = param_range
    Fixed_load2_scalar: EndpointParamRange = param_range
    Flex_load_max: EndpointParamRange = param_range
    GridExport: EndpointParamRange = param_range
    GridImport: EndpointParamRange = param_range
    Import_headroom: EndpointParamRange = param_range
    Min_power_factor: EndpointParamRange = param_range
    Mop_load_max: EndpointParamRange = param_range
    ScalarHL1: EndpointParamRange = param_range
    ScalarHYield: EndpointParamRange = param_range
    ScalarRG1: EndpointParamRange = param_range
    ScalarRG2: EndpointParamRange = param_range
    ScalarRG3: EndpointParamRange = param_range
    ScalarRG4: EndpointParamRange = param_range
    f22_EV_CP_number: EndpointParamRange = param_range
    r50_EV_CP_number: EndpointParamRange = param_range
    s7_EV_CP_number: EndpointParamRange = param_range
    u150_EV_CP_number: EndpointParamRange = param_range
    DHW_cylinder_volume: EndpointParamRange = param_range
    CAPEX_limit: int | float = Field(description="CAPEX limit to set in EPOCH. Not Implemented !")
    Export_kWh_price: int | float = Field(description="Export kWh price to set in EPOCH.")
    OPEX_limit: int | float = Field(description="OPEX limit to set in EPOCH. Not Implemented !")
    target_max_concurrency: int | float = Field(description="Number of cores to allocate to EPOCH. Not Implemented !")
    time_budget_min: int | float
    timestep_hours: int | float
    timewindow: float | int


class ParamRange(TypedDict):
    min: int | float
    max: int | float
    step: int | float


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
    DHW_cylinder_volume: ParamRange
    CAPEX_limit: int | float
    Export_kWh_price: int | float
    OPEX_limit: int | float
    target_max_concurrency: int | float
    time_budget_min: int | float
    timestep_hours: int | float
    timewindow: float | int


OldParameterDict = Mapping[str, list[int | float] | tuple[int | float] | int | float]
