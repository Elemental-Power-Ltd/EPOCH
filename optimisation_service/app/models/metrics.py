from enum import IntEnum, StrEnum


class Metric(StrEnum):
    carbon_balance_scope_1 = "carbon_balance_scope_1"
    carbon_balance_scope_2 = "carbon_balance_scope_2"
    meter_balance = "meter_balance"
    operating_balance = "operating_balance"
    cost_balance = "cost_balance"
    capex = "capex"
    payback_horizon = "payback_horizon"
    annualised_cost = "annualised_cost"
    carbon_cost = "carbon_cost"

    total_gas_used = "total_gas_used"
    total_electricity_imported = "total_electricity_imported"
    total_electricity_generated = "total_electricity_generated"
    total_electricity_exported = "total_electricity_exported"

    total_electrical_shortfall = "total_electrical_shortfall"
    total_heat_shortfall = "total_heat_shortfall"

    total_gas_import_cost = "total_gas_import_cost"
    total_electricity_import_cost = "total_electricity_import_cost"
    total_electricity_export_gain = "total_electricity_export_gain"
    total_meter_cost = "total_meter_cost"

    baseline_gas_used = "baseline_gas_used"
    baseline_electricity_imported = "baseline_electricity_imported"
    baseline_electricity_generated = "baseline_electricity_generated"
    baseline_electricity_exported = "baseline_electricity_exported"

    baseline_electrical_shortfall = "baseline_electrical_shortfall"
    baseline_heat_shortfall = "baseline_heat_shortfall"

    baseline_gas_import_cost = "baseline_gas_import_cost"
    baseline_electricity_import_cost = "baseline_electricity_import_cost"
    baseline_electricity_export_gain = "baseline_electricity_export_gain"
    baseline_meter_cost = "baseline_meter_cost"


# these metrics can be used as an optimisation objective
_EPOCH_NATIVE_OBJECTIVE_METRICS = [
    Metric.carbon_balance_scope_1,
    Metric.carbon_balance_scope_2,
    Metric.capex,
    Metric.meter_balance,
    Metric.operating_balance,
    Metric.cost_balance,
    Metric.annualised_cost,
    Metric.payback_horizon,

    Metric.total_gas_used,
    Metric.total_electricity_imported,
    Metric.total_electricity_generated,
    Metric.total_electricity_exported,

    Metric.total_electrical_shortfall,
    Metric.total_heat_shortfall,

    Metric.total_gas_import_cost,
    Metric.total_electricity_import_cost,
    Metric.total_electricity_export_gain,
    Metric.total_meter_cost,
]


# the objectives are native to EPOCH but cannot be optimised over
_EPOCH_NATIVE_NON_OBJECTIVE_METRICS = [
    Metric.baseline_gas_used,
    Metric.baseline_electricity_imported,
    Metric.baseline_electricity_generated,

    Metric.baseline_electricity_exported,
    Metric.baseline_electrical_shortfall,

    Metric.baseline_heat_shortfall,
    Metric.baseline_gas_import_cost,
    Metric.baseline_electricity_import_cost,
    Metric.baseline_electricity_export_gain,
    Metric.baseline_meter_cost
]

_SERVICE_NATIVE_METRICS = [
    Metric.carbon_cost,
]

_OBJECTIVES = _EPOCH_NATIVE_OBJECTIVE_METRICS + _SERVICE_NATIVE_METRICS
_METRICS = _EPOCH_NATIVE_OBJECTIVE_METRICS + _EPOCH_NATIVE_NON_OBJECTIVE_METRICS + _SERVICE_NATIVE_METRICS

# The portfolio metrics can be combined by summing all site-level results
_SUMMABLE_METRICS = [
    Metric.annualised_cost,
    Metric.capex,
    Metric.carbon_balance_scope_1,
    Metric.carbon_balance_scope_2,
    Metric.meter_balance,
    Metric.operating_balance,
    Metric.cost_balance,

    Metric.total_gas_used,
    Metric.total_electricity_imported,
    Metric.total_electricity_generated,
    Metric.total_electricity_exported,

    Metric.total_electrical_shortfall,
    Metric.total_heat_shortfall,

    Metric.total_gas_import_cost,
    Metric.total_electricity_import_cost,
    Metric.total_electricity_export_gain,
    Metric.total_meter_cost,

    Metric.baseline_gas_used,
    Metric.baseline_electricity_imported,
    Metric.baseline_electricity_generated,
    Metric.baseline_electricity_exported,

    Metric.baseline_electrical_shortfall,
    Metric.baseline_heat_shortfall,

    Metric.baseline_gas_import_cost,
    Metric.baseline_electricity_import_cost,
    Metric.baseline_electricity_export_gain,
    Metric.baseline_meter_cost,
]


# 1 for objectives we want to minimise, -1 for objectives we want to maximise
class MetricDirection(IntEnum):
    carbon_balance_scope_1 = -1
    carbon_balance_scope_2 = -1
    meter_balance = -1
    operating_balance = -1
    cost_balance = -1
    capex = 1
    payback_horizon = 1
    annualised_cost = 1
    carbon_cost = 1

    total_gas_used = 1
    total_electricity_imported = 1
    total_electricity_generated = -1
    total_electricity_exported = -1

    total_electrical_shortfall = 1
    total_heat_shortfall = 1

    total_gas_import_cost = 1
    total_electricity_import_cost = 1
    total_electricity_export_gain = -1
    total_meter_cost = 1


MetricValues = dict[Metric, int | float]
