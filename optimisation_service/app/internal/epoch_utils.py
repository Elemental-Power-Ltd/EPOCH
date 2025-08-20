"""Wrappers for Epoch that are more ergonomic for python."""

import json
from typing import cast

from epoch_simulator import SimulationResult, TaskData

from app.models.core import SimulationMetrics, Grade
from app.models.epoch_types.task_data_type import TaskData as TaskDataPydantic
from app.models.metrics import Metric, MetricValues

type Jsonable = float | int | str | dict[str, Jsonable]


def simulation_result_to_pydantic(sim_result: SimulationResult) -> SimulationMetrics:
    """
    Convert and EPOCH SimulationResult into a Pydantic SiteMetrics object.

    Parameters
    ----------
    sim_result
        Epoch bindings for a SimulationResult.

    Returns
    -------
    SimulationMetrics
        A pydantic model of the metrics.

    """

    comp = sim_result.comparison
    scenario = sim_result.metrics
    baseline = sim_result.baseline_metrics

    # we have to do an awkward conversion between two enums with the same values here
    scenario_grade = Grade[scenario.scenario_environmental_impact_grade.name] if scenario.scenario_environmental_impact_grade is not None else None
    baseline_grade = Grade[baseline.scenario_environmental_impact_grade.name] if baseline.scenario_environmental_impact_grade is not None else None

    return SimulationMetrics(
        # Comparison metrics
        meter_balance=comp.meter_balance,
        operating_balance=comp.operating_balance,
        cost_balance=comp.cost_balance,
        npv_balance=comp.npv_balance,
        payback_horizon=comp.payback_horizon_years,
        carbon_balance_scope_1=comp.carbon_balance_scope_1,
        carbon_balance_scope_2=comp.carbon_balance_scope_2,
        carbon_balance_total=comp.combined_carbon_balance,
        carbon_cost=comp.carbon_cost,

        # Scenario Metrics
        total_gas_used=scenario.total_gas_used,
        total_electricity_imported=scenario.total_electricity_imported,
        total_electricity_generated=scenario.total_electricity_generated,
        total_electricity_exported=scenario.total_electricity_exported,
        total_electricity_curtailed=scenario.total_electricity_curtailed,
        total_electricity_used=scenario.total_electricity_used,
        total_electrical_shortfall=scenario.total_electrical_shortfall,
        total_heat_shortfall=scenario.total_heat_shortfall,
        total_ch_shortfall=scenario.total_ch_shortfall,
        total_dhw_shortfall=scenario.total_dhw_shortfall,

        capex=scenario.total_capex,
        total_gas_import_cost=scenario.total_gas_import_cost,
        total_electricity_import_cost=scenario.total_electricity_import_cost,
        total_electricity_export_gain=scenario.total_electricity_export_gain,

        total_meter_cost=scenario.total_meter_cost,
        total_operating_cost=scenario.total_operating_cost,
        annualised_cost=scenario.total_annualised_cost,
        total_net_present_value=scenario.total_net_present_value,

        total_scope_1_emissions=scenario.total_scope_1_emissions,
        total_scope_2_emissions=scenario.total_scope_2_emissions,
        total_combined_carbon_emissions=scenario.total_combined_carbon_emissions,

        scenario_environmental_impact_score=scenario.scenario_environmental_impact_score,
        scenario_environmental_impact_grade=scenario_grade,

        # Baseline Metrics
        baseline_gas_used=baseline.total_gas_used,
        baseline_electricity_imported=baseline.total_electricity_imported,
        baseline_electricity_generated=baseline.total_electricity_generated,
        baseline_electricity_exported=baseline.total_electricity_exported,
        baseline_electricity_curtailed=baseline.total_electricity_curtailed,
        baseline_electricity_used=baseline.total_electricity_used,

        baseline_electrical_shortfall=baseline.total_electrical_shortfall,
        baseline_heat_shortfall=baseline.total_heat_shortfall,
        baseline_ch_shortfall=baseline.total_ch_shortfall,
        baseline_dhw_shortfall=baseline.total_dhw_shortfall,

        baseline_gas_import_cost=baseline.total_gas_import_cost,
        baseline_electricity_import_cost=baseline.total_electricity_import_cost,
        baseline_electricity_export_gain=baseline.total_electricity_export_gain,

        baseline_meter_cost=baseline.total_meter_cost,
        baseline_operating_cost=baseline.total_operating_cost,
        baseline_net_present_value=baseline.total_net_present_value,

        baseline_scope_1_emissions=baseline.total_scope_1_emissions,
        baseline_scope_2_emissions=baseline.total_scope_2_emissions,
        baseline_combined_carbon_emissions=baseline.total_combined_carbon_emissions,

        baseline_environmental_impact_score=baseline.scenario_environmental_impact_score,
        baseline_environmental_impact_grade=baseline_grade,
    )


def simulation_result_to_metric_dict(sim_result: SimulationResult) -> MetricValues:
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

    # Comparative fields between the scenario and baseline
    comp = sim_result.comparison
    metric_values[Metric.meter_balance] = comp.meter_balance
    metric_values[Metric.operating_balance] = comp.operating_balance
    metric_values[Metric.cost_balance] = comp.cost_balance
    metric_values[Metric.npv_balance] = comp.npv_balance

    metric_values[Metric.payback_horizon] = comp.payback_horizon_years

    metric_values[Metric.carbon_balance_scope_1] = comp.carbon_balance_scope_1
    metric_values[Metric.carbon_balance_scope_2] = comp.carbon_balance_scope_2
    metric_values[Metric.carbon_balance_total] = comp.combined_carbon_balance

    metric_values[Metric.carbon_cost] = comp.carbon_cost

    # Nested SimulationMetrics
    metrics = sim_result.metrics
    metric_values[Metric.total_gas_used] = metrics.total_gas_used
    metric_values[Metric.total_electricity_imported] = metrics.total_electricity_imported
    metric_values[Metric.total_electricity_generated] = metrics.total_electricity_generated
    metric_values[Metric.total_electricity_exported] = metrics.total_electricity_exported
    metric_values[Metric.total_electricity_curtailed] = metrics.total_electricity_curtailed
    metric_values[Metric.total_electricity_used] = metrics.total_electricity_used

    metric_values[Metric.total_electrical_shortfall] = metrics.total_electrical_shortfall
    metric_values[Metric.total_heat_shortfall] = metrics.total_heat_shortfall
    metric_values[Metric.total_ch_shortfall] = metrics.total_ch_shortfall
    metric_values[Metric.total_dhw_shortfall] = metrics.total_dhw_shortfall

    metric_values[Metric.capex] = sim_result.metrics.total_capex
    metric_values[Metric.total_gas_import_cost] = sim_result.metrics.total_gas_import_cost
    metric_values[Metric.total_electricity_import_cost] = sim_result.metrics.total_electricity_import_cost
    metric_values[Metric.total_electricity_export_gain] = sim_result.metrics.total_electricity_export_gain

    metric_values[Metric.total_meter_cost] = sim_result.metrics.total_meter_cost
    metric_values[Metric.total_operating_cost] = sim_result.metrics.total_operating_cost
    metric_values[Metric.annualised_cost] = sim_result.metrics.total_annualised_cost
    metric_values[Metric.total_net_present_value] = sim_result.metrics.total_net_present_value

    metric_values[Metric.total_scope_1_emissions] = sim_result.metrics.total_scope_1_emissions
    metric_values[Metric.total_scope_2_emissions] = sim_result.metrics.total_scope_2_emissions
    metric_values[Metric.total_combined_carbon_emissions] = sim_result.metrics.total_combined_carbon_emissions

    return metric_values


def convert_TaskData_to_dictionary(task_data: TaskData) -> dict[str, Jsonable]:
    """
    Convert an Epoch TaskData instance into a dictionary representation.

    Parameters
    ----------
    task_data
        The TaskData instance to convert.

    Returns
    -------
    task_data_dict
        A dictionary representation of the task_data.
    """
    return cast(dict[str, Jsonable], json.loads(task_data.to_json()))


def convert_TaskData_to_pydantic(task_data: TaskData) -> TaskDataPydantic:
    """
    Convert an Epoch TaskData instance into a pydantic model.

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
