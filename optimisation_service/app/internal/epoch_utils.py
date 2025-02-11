"""
Wrappers for Epoch that are more ergonomic for python.
"""

import numpy as np

from app.models.objectives import Objectives, ObjectiveValues

from .log import logger

try:
    from epoch_simulator import SimulationResult, Simulator, TaskData

    TaskData.__hash__ = lambda td: hash(repr(td))  # type: ignore
    TaskData.__eq__ = lambda td, oth: repr(td) == repr(oth)  # type: ignore

    HAS_EPOCH = True
except ImportError as ex:
    logger.warning(f"Failed to import Epoch python bindings due to {ex}")
    HAS_EPOCH = False

    # bodge ourselves some horrible stubs so that
    # we can run tests without EPOCH
    class SimulationResult: ...  # type: ignore

    class TaskData:  # type: ignore
        @staticmethod
        def from_json(json_str: str): ...

    class Simulator:  # type: ignore
        def __init__(self, inputDir: str): ...
        def simulate_scenario(self, task_data: TaskData, fullReporting: bool = False) -> SimulationResult:
            raise NotImplementedError()


def convert_sim_result(sim_result: SimulationResult) -> ObjectiveValues:
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
    objective_values = ObjectiveValues()
    for objective in [
        Objectives.annualised_cost,
        Objectives.capex,
        Objectives.carbon_balance_scope_1,
        Objectives.carbon_balance_scope_2,
        Objectives.cost_balance,
        Objectives.payback_horizon,
    ]:
        objective_values[objective] = getattr(sim_result, objective)

    if sim_result.capex > 0:
        if sim_result.carbon_balance_scope_1 > 0:
            objective_values[Objectives.carbon_cost] = sim_result.capex / (sim_result.carbon_balance_scope_1 / 1000)
        else:
            objective_values[Objectives.carbon_cost] = float(np.finfo(np.float32).max)
    else:
        objective_values[Objectives.carbon_cost] = 0

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
