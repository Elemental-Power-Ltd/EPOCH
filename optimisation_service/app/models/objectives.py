from enum import IntEnum, StrEnum


class Objectives(StrEnum):
    carbon_balance_scope_1 = "carbon_balance_scope_1"
    carbon_balance_scope_2 = "carbon_balance_scope_2"
    cost_balance = "cost_balance"
    capex = "capex"
    payback_horizon = "payback_horizon"
    annualised_cost = "annualised_cost"
    carbon_cost = "carbon_cost"


_OBJECTIVES = [
    Objectives.carbon_balance_scope_1,
    Objectives.carbon_balance_scope_2,
    Objectives.capex,
    Objectives.cost_balance,
    Objectives.annualised_cost,
    Objectives.payback_horizon,
    Objectives.carbon_cost,
]


class ObjectivesDirection(IntEnum):
    carbon_balance_scope_1 = -1
    carbon_balance_scope_2 = -1
    cost_balance = -1
    capex = 1
    payback_horizon = 1
    annualised_cost = 1
    carbon_cost = 1


ObjectiveValues = dict[Objectives, int | float]
