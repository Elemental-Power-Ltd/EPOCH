from enum import IntEnum, StrEnum


class Objectives(StrEnum):
    carbon_balance = "carbon_balance"
    cost_balance = "cost_balance"
    capex = "capex"
    payback_horizon = "payback_horizon"
    annualised_cost = "annualised_cost"


_OBJECTIVES = [
    Objectives.carbon_balance,
    Objectives.capex,
    Objectives.cost_balance,
    Objectives.annualised_cost,
    Objectives.payback_horizon,
]


class ObjectivesDirection(IntEnum):
    carbon_balance = -1
    cost_balance = -1
    capex = 1
    payback_horizon = 1
    annualised_cost = 1
