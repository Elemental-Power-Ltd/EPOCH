from enum import StrEnum


class Objectives(StrEnum):
    carbon_balance = "carbon_balance"
    cost_balance = "cost_balance"
    capex = "capex"
    payback_horizon = "payback_horizon"
    annualised_cost = "annualised_cost"


_OBJECTIVES = [objective.value for objective in Objectives]

_OBJECTIVES_DIRECTION = {"carbon_balance": -1, "cost_balance": -1, "capex": 1, "payback_horizon": 1, "annualised_cost": 1}
