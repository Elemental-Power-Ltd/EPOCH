"""
Wrappers for Epoch that are more ergonomic for python.
"""

from enum import Enum

from app.internal.metrics import calculate_carbon_cost
from app.models.metrics import _EPOCH_NATIVE_METRICS, Metric, MetricValues

from .log import logger

try:
    from epoch_simulator import (
        BatteryMode,
        Building,
        Config,
        DataCentre,
        DomesticHotWater,
        EnergyStorageSystem,
        Grid,
        HeatPump,
        HeatSource,
        Renewables,
        SimulationResult,
        Simulator,
        TaskData,
    )

    TaskData.__hash__ = lambda td: hash(repr(td))  # type: ignore
    TaskData.__eq__ = lambda td, oth: repr(td) == repr(oth)  # type: ignore

    HAS_EPOCH = True
except ImportError as ex:
    logger.warning(f"Failed to import Epoch python bindings due to {ex}")
    HAS_EPOCH = False

    # bodge ourselves some horrible stubs so that
    # we can run tests without EPOCH
    class SimulationResult: ...  # type: ignore

    class Config:  # type: ignore
        capex_limit: float

    class Building:  # type: ignore
        scalar_heat_load: float
        scalar_electrical_load: float
        fabric_intervention_index: int

    class DataCentre:  # type: ignore
        maximum_load: float
        hotroom_temp: float

    class DomesticHotWater:  # type: ignore
        cylinder_volume: float

    class ElectricVehicles:  # type: ignore
        flexible_load_ratio: float
        small_chargers: int
        fast_chargers: int
        rapid_chargers: int
        ultra_chargers: int
        scalar_electrical_load: float

    class BatteryMode(Enum):  # type: ignore
        CONSUME = "CONSUME"

    class EnergyStorageSystem:  # type: ignore
        capacity: float
        charge_power: float
        discharge_power: float
        battery_mode: BatteryMode
        initial_charge: float

    class Grid:  # type: ignore
        export_headroom: float
        grid_export: float
        grid_import: float
        import_headroom: float
        min_power_factor: float
        tariff_index: int

    class HeatSource(Enum):  # type: ignore
        AMBIENT_AIR = "AMBIENT_AIR"
        HOTROOM = "HOTROOM"

    class HeatPump:  # type: ignore
        heat_power: float
        heat_source: HeatSource
        send_temp: float

    class Mop:  # type: ignore
        maximum_load: float

    class Renewables:  # type: ignore
        yield_scalars: list[float]

    class TaskData:  # type: ignore
        config: Config
        building: Building
        data_centre: DataCentre
        domestic_hot_water: DomesticHotWater
        electric_vehicles: ElectricVehicles
        energy_storage_system: EnergyStorageSystem
        grid: Grid
        heat_pump: HeatPump
        mop: Mop
        renewables: Renewables

        @staticmethod
        def from_json(json_str: str): ...

    class Simulator:  # type: ignore
        def __init__(self, inputDir: str): ...
        def simulate_scenario(self, task_data: TaskData, fullReporting: bool = False) -> SimulationResult:
            raise NotImplementedError()


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
    for metric in _EPOCH_NATIVE_METRICS:
        metric_values[metric] = getattr(sim_result, metric)

    metric_values[Metric.carbon_cost] = calculate_carbon_cost(
        capex=metric_values[Metric.capex], carbon_balance_scope_1=metric_values[Metric.carbon_balance_scope_1]
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
