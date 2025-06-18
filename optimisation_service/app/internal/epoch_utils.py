"""
Wrappers for Epoch that are more ergonomic for python.
"""
import json

from epoch_simulator import SimulationResult, TaskData

from app.internal.metrics import calculate_carbon_cost
from app.models.epoch_types import TaskDataPydantic
from app.models.metrics import Metric, MetricValues


def convert_sim_result(sim_result: SimulationResult) -> MetricValues:
    """
    Convert an EPOCH SimulationResult into an ObjectiveValues dictionary.

    Parameters
    ----------
    sim_result
        SimulationResult to convert.

    Returns
    -------
    ObjectiveValues
        Dictionary of objective values.
    """
    metric_values = MetricValues()

    # Top-level fields
    metric_values[Metric.carbon_balance_scope_1] = sim_result.carbon_balance_scope_1
    metric_values[Metric.carbon_balance_scope_2] = sim_result.carbon_balance_scope_2
    metric_values[Metric.capex] = sim_result.capex
    metric_values[Metric.meter_balance] = sim_result.meter_balance
    metric_values[Metric.operating_balance] = sim_result.operating_balance
    metric_values[Metric.cost_balance] = sim_result.cost_balance
    metric_values[Metric.npv_balance] = sim_result.npv_balance
    metric_values[Metric.annualised_cost] = sim_result.annualised_cost
    metric_values[Metric.payback_horizon] = sim_result.payback_horizon

    # Nested SimulationMetrics
    metric_values[Metric.total_gas_used] = sim_result.metrics.total_gas_used
    metric_values[Metric.total_electricity_imported] = sim_result.metrics.total_electricity_imported
    metric_values[Metric.total_electricity_generated] = sim_result.metrics.total_electricity_generated
    metric_values[Metric.total_electricity_exported] = sim_result.metrics.total_electricity_exported

    metric_values[Metric.total_electrical_shortfall] = sim_result.metrics.total_electrical_shortfall
    metric_values[Metric.total_heat_shortfall] = sim_result.metrics.total_heat_shortfall

    metric_values[Metric.total_gas_import_cost] = sim_result.metrics.total_gas_import_cost
    metric_values[Metric.total_electricity_import_cost] = sim_result.metrics.total_electricity_import_cost
    metric_values[Metric.total_electricity_export_gain] = sim_result.metrics.total_electricity_export_gain
    metric_values[Metric.total_meter_cost] = sim_result.metrics.total_meter_cost
    metric_values[Metric.total_operating_cost] = sim_result.metrics.total_operating_cost
    metric_values[Metric.total_net_present_value] = sim_result.metrics.total_net_present_value

    metric_values[Metric.baseline_gas_used] = sim_result.baseline_metrics.total_gas_used
    metric_values[Metric.baseline_electricity_imported] = sim_result.baseline_metrics.total_electricity_imported
    metric_values[Metric.baseline_electricity_generated] = sim_result.baseline_metrics.total_electricity_generated
    metric_values[Metric.baseline_electricity_exported] = sim_result.baseline_metrics.total_electricity_exported

    metric_values[Metric.baseline_electrical_shortfall] = sim_result.baseline_metrics.total_electrical_shortfall
    metric_values[Metric.baseline_heat_shortfall] = sim_result.baseline_metrics.total_heat_shortfall

    metric_values[Metric.baseline_gas_import_cost] = sim_result.baseline_metrics.total_gas_import_cost
    metric_values[Metric.baseline_electricity_import_cost] = sim_result.baseline_metrics.total_electricity_import_cost
    metric_values[Metric.baseline_electricity_export_gain] = sim_result.baseline_metrics.total_electricity_export_gain
    metric_values[Metric.baseline_meter_cost] = sim_result.baseline_metrics.total_meter_cost
    metric_values[Metric.baseline_operating_cost] = sim_result.baseline_metrics.total_operating_cost
    metric_values[Metric.baseline_net_present_value] = sim_result.baseline_metrics.total_net_present_value

    # Derive carbon cost from capex and scope-1 carbon balance
    metric_values[Metric.carbon_cost] = calculate_carbon_cost(
        capex=metric_values[Metric.capex],
        carbon_balance_scope_1=metric_values[Metric.carbon_balance_scope_1]
    )

    return metric_values


def convert_TaskData_to_dictionary(task_data: TaskData) -> dict:
    """
    Converts an Epoch TaskData instance into a dictionary representation.

    Parameters
    ----------
    task_data
        The TaskData instance to convert.

    Returns
    -------
    task_data_dict
        A dictionary representation of the task_data.
    """
    return json.loads(task_data.to_json())


def convert_TaskData_to_pydantic(task_data: TaskData) -> TaskDataPydantic:
    """
    Converts an Epoch TaskData instance into a pydantic model

    Parameters
    ----------
    task_data
        The TaskData instance to convert.

    Returns
    -------
        A pydantic model of the TaskData
    """
    task_data_dict = convert_TaskData_to_dictionary(task_data)
    return TaskDataPydantic.model_validate(task_data_dict)
