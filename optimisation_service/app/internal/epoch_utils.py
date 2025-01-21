"""
Wrappers for Epoch that are more ergonomic for python.
"""

from .log import logger

try:
    from epoch_simulator import SimulationResult, Simulator, TaskData

    TaskData.__hash__ = lambda td: hash(repr(td))
    TaskData.__eq__ = lambda td, oth: repr(td) == repr(oth)

    HAS_EPOCH = True
except ImportError as ex:
    logger.warning(f"Failed to import Epoch python bindings due to {ex}")
    HAS_EPOCH = False

    # bodge ourselves some horrible stubs so that
    # we can run tests without EPOCH
    class SimulationResult: ...  # type: ignore

    class TaskData: ...  # type: ignore

    class Simulator:  # type: ignore
        def __init__(self, inputDir: str): ...
        def simulate_scenario(self, task_data: TaskData, fullReporting: bool = False) -> SimulationResult:
            raise NotImplementedError()


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
