from collections.abc import Mapping
from typing import Final

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


class ParamRange(BaseModel):
    min: int | float
    max: int | float
    step: int | float


class ParameterDict(BaseModel):
    ASHP_HPower: ParamRange = param_range
    ASHP_HSource: ParamRange = param_range
    ASHP_HotTemp: ParamRange = param_range
    ASHP_RadTemp: ParamRange = param_range
    ESS_capacity: ParamRange = param_range
    ESS_charge_mode: ParamRange = param_range
    ESS_charge_power: ParamRange = param_range
    ESS_discharge_mode: ParamRange = param_range
    ESS_discharge_power: ParamRange = param_range
    ESS_start_SoC: ParamRange = param_range
    EV_flex: ParamRange = param_range
    Export_headroom: ParamRange = param_range
    Fixed_load1_scalar: ParamRange = param_range
    Fixed_load2_scalar: ParamRange = param_range
    Flex_load_max: ParamRange = param_range
    GridExport: ParamRange = param_range
    GridImport: ParamRange = param_range
    Import_headroom: ParamRange = param_range
    Min_power_factor: ParamRange = param_range
    Mop_load_max: ParamRange = param_range
    ScalarHL1: ParamRange = param_range
    ScalarHYield: ParamRange = param_range
    ScalarRG1: ParamRange = param_range
    ScalarRG2: ParamRange = param_range
    ScalarRG3: ParamRange = param_range
    ScalarRG4: ParamRange = param_range
    f22_EV_CP_number: ParamRange = param_range
    r50_EV_CP_number: ParamRange = param_range
    s7_EV_CP_number: ParamRange = param_range
    u150_EV_CP_number: ParamRange = param_range
    DHW_cylinder_volume: ParamRange = param_range
    CAPEX_limit: int | float = Field(description="CAPEX limit to set in EPOCH. Not Implemented !")
    Export_kWh_price: int | float = Field(description="Export kWh price to set in EPOCH.")
    OPEX_limit: int | float = Field(description="OPEX limit to set in EPOCH. Not Implemented !")
    target_max_concurrency: int | float = Field(description="Number of cores to allocate to EPOCH. Not Implemented !")
    time_budget_min: int | float
    timestep_hours: int | float
    timewindow: float | int


OldParameterDict = Mapping[str, list[int | float] | tuple[int | float] | int | float]


def is_variable_paramrange(param_range: ParamRange) -> bool:
    """
    Checks if a parameter range is variable or not.

    Parameters
    ----------
    value
        Param range to evaluate.

    Returns
    -------
    is_var
        Boolean if value is variable or not.
    """
    if (param_range.step != 0) and (param_range.min != param_range.max):
        return True
    return False
