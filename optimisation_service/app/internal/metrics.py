import numpy as np


def calculate_carbon_cost(capex: float | int, carbon_balance_scope_1: float | int) -> float | int:
    """
    Calculates the salix carbon cost of a scenario.
    It is the total CAPEX of a scenario divided by its scope 1 carbon emission savings in tonnes.
    The carbon emissions need to be adjusted by multiplying each assets savings by its lifetime years.
    The lifetime years of each asset and the carbon cost equation can be found:
    https://www.salixfinance.co.uk/sites/default/files/2024-10/Guidance%20Notes%20%282%29.pdf.
    Since, only heat pumps currently affect the carbon emissions, the ASSET_LIFETIME_YEARS is set to 20.
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
    if capex > 0 and carbon_balance_scope_1 > 0:
        ASSET_LIFETIME_YEARS = 20
        return capex / (carbon_balance_scope_1 * ASSET_LIFETIME_YEARS / 1000)

    if capex > 0 and carbon_balance_scope_1 <= 0:
        return float(np.finfo(np.float32).max)

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
    if capex > 0 and cost_balance > 0:
        return capex / cost_balance

    if capex > 0 and cost_balance <= 0:
        return float(np.finfo(np.float32).max)

    return 0
