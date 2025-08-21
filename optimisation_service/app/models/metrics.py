from enum import IntEnum, StrEnum


class Metric(StrEnum):
    """
    A subset of the metrics returned from an EPOCH simulation.

    Specifically the metrics that are in any way meaningful for use as an optimisation objective.
    This primarily means that the baseline metrics are excluded.
    """

    meter_balance = "meter_balance"
    operating_balance = "operating_balance"
    cost_balance = "cost_balance"
    npv_balance = "npv_balance"

    payback_horizon = "payback_horizon"

    carbon_balance_scope_1 = "carbon_balance_scope_1"
    carbon_balance_scope_2 = "carbon_balance_scope_2"
    carbon_balance_total = "carbon_balance_total"

    carbon_cost = "carbon_cost"

    total_gas_used = "total_gas_used"
    total_electricity_imported = "total_electricity_imported"
    total_electricity_generated = "total_electricity_generated"
    total_electricity_exported = "total_electricity_exported"
    total_electricity_curtailed = "total_electricity_curtailed"
    total_electricity_used = "total_electricity_used"

    total_electrical_shortfall = "total_electrical_shortfall"
    total_heat_shortfall = "total_heat_shortfall"
    total_ch_shortfall = "total_ch_shortfall"
    total_dhw_shortfall = "total_dhw_shortfall"

    capex = "capex"
    total_gas_import_cost = "total_gas_import_cost"
    total_electricity_import_cost = "total_electricity_import_cost"
    total_electricity_export_gain = "total_electricity_export_gain"

    total_meter_cost = "total_meter_cost"
    total_operating_cost = "total_operating_cost"
    annualised_cost = "annualised_cost"
    total_net_present_value = "total_net_present_value"

    total_scope_1_emissions = "total_scope_1_emissions"
    total_scope_2_emissions = "total_scope_2_emissions"
    total_combined_carbon_emissions = "total_combined_carbon_emissions"


# 1 for objectives we want to minimise, -1 for objectives we want to maximise
class MetricDirection(IntEnum):
    meter_balance = -1
    operating_balance = -1
    cost_balance = -1
    npv_balance = -1

    payback_horizon = 1

    carbon_balance_scope_1 = -1
    carbon_balance_scope_2 = -1
    carbon_balance_total = -1

    carbon_cost = 1

    total_gas_used = 1
    total_electricity_imported = 1
    total_electricity_generated = -1
    total_electricity_exported = -1
    total_electricity_curtailed = 1
    total_electricity_used = 1

    total_electrical_shortfall = 1
    total_heat_shortfall = 1
    total_ch_shortfall = 1
    total_dhw_shortfall = 1

    capex = 1
    total_gas_import_cost = 1
    total_electricity_import_cost = 1
    total_electricity_export_gain = -1

    total_meter_cost = 1
    total_operating_cost = 1
    annualised_cost = 1
    total_net_present_value = -1

    total_scope_1_emissions = 1
    total_scope_2_emissions = 1
    total_combined_carbon_emissions = 1


MetricValues = dict[Metric, int | float]

_METRICS: list[Metric] = list(Metric)
_OBJECTIVES: list[Metric] = list(Metric)
