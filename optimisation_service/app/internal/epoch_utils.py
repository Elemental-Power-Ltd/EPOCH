"""
Wrappers for Epoch that are more ergonomic for python.
"""

from epoch_simulator import SimulationResult, TaskData

from app.internal.metrics import calculate_carbon_cost
from app.models.metrics import _EPOCH_NATIVE_METRICS, Metric, MetricValues

TaskData.__hash__ = lambda td: hash(repr(td))  # type: ignore
TaskData.__eq__ = lambda td, oth: repr(td) == repr(oth)  # type: ignore


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
    objective_values = MetricValues()
    for objective in _EPOCH_NATIVE_METRICS:
        objective_values[objective] = getattr(sim_result, objective)

    objective_values[Metric.carbon_cost] = calculate_carbon_cost(
        capex=objective_values[Metric.capex], carbon_balance_scope_1=objective_values[Metric.carbon_balance_scope_1]
    )

    return objective_values


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
    task_data_dict = {}
    task_data_fields = [field for field in dir(task_data) if not field.startswith("__") and field != "from_json"]
    for task_data_field in task_data_fields:
        asset = getattr(task_data, task_data_field)
        asset_fields = [field for field in dir(asset) if not field.startswith("__") and field != "from_json"]
        asset_dict = {}
        if len(asset_fields) > 0:
            for asset_field in asset_fields:
                attr_value = getattr(asset, asset_field)
                if asset_field in ["heat_source", "battery_mode"]:
                    asset_dict[asset_field] = attr_value.name
                else:
                    asset_dict[asset_field] = attr_value
            task_data_dict[task_data_field] = asset_dict
    return task_data_dict
