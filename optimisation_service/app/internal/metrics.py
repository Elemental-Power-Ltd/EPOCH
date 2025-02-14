import numpy as np


def calculate_carbon_cost(capex: float | int, carbon_balance_scope_1: float | int) -> float | int:
    """
    Calculate the carbon cost from CAPEX and scope 1 carbon emission savings.
    Returns largest float32 if CAPEX is non null and carbon_balance_scope_1 is null or negative.
    Returns 0 if CAPEX is null.

    Parameters
    ----------
    capex
        CAPEX.
    carbon_balance_scope_1
        scope 1 carbon emission savings

    Returns
    -------
    carbon_cost
        Carbon cost.
    """

    if capex > 0:
        if carbon_balance_scope_1 > 0:
            return capex / (carbon_balance_scope_1 * 20 / 1000)
        else:
            return float(np.finfo(np.float32).max)
    else:
        return 0


def calculate_payback_horizon(capex: float | int, cost_balance: float | int) -> float | int:
    """
    Calculate payback horizon from CAPEX and cost balance.
    Returns largest float32 if CAPEX is non null and cost balance is null or negative.
    Returns 0 if CAPEX is null.

    Parameters
    ----------
    capex
        CAPEX.
    cost_balance
        Cost balance.

    Returns
    -------
    payback_horizon
        Payback horizon.
    """

    if capex > 0:
        if cost_balance > 0:
            return capex / cost_balance
        else:
            return float(np.finfo(np.float32).max)
    else:
        return 0
