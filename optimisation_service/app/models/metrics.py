from enum import IntEnum, StrEnum


class Metric(StrEnum):
    carbon_balance_scope_1 = "carbon_balance_scope_1"
    carbon_balance_scope_2 = "carbon_balance_scope_2"
    cost_balance = "cost_balance"
    capex = "capex"
    payback_horizon = "payback_horizon"
    annualised_cost = "annualised_cost"
    carbon_cost = "carbon_cost"


_EPOCH_NATIVE_METRICS = [
    Metric.carbon_balance_scope_1,
    Metric.carbon_balance_scope_2,
    Metric.capex,
    Metric.cost_balance,
    Metric.annualised_cost,
    Metric.payback_horizon,
]

_SERVICE_NATIVE_METRICS = [
    Metric.carbon_cost,
]

_METRICS = _EPOCH_NATIVE_METRICS + _SERVICE_NATIVE_METRICS


class MetricDirection(IntEnum):
    carbon_balance_scope_1 = -1
    carbon_balance_scope_2 = -1
    cost_balance = -1
    capex = 1
    payback_horizon = 1
    annualised_cost = 1
    carbon_cost = 1


MetricValues = dict[Metric, int | float]
