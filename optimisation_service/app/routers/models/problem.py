from pydantic import BaseModel, Field

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
    CAPEX_limit: int | float = Field(description="CAPEX limit to set in EPOCH. Not Implemented !")
    Export_kWh_price: int | float = Field(description="Export kWh price to set in EPOCH.")
    OPEX_limit: int | float = Field(description="OPEX limit to set in EPOCH. Not Implemented !")
    target_max_concurrency: int | float = Field(description="Number of cores to allocate to EPOCH. Not Implemented !")
    time_budget_min: int | float
    timestep_hours: int | float = Field(default=1.0)
