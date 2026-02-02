"""
Generate all possible combinations of assets to create an upgrade tree.

This includes functions to check for what the combinations should be.
"""

import itertools
import logging

from app.models.epoch_types.config import Config
from app.models.epoch_types.task_data_type import (
    Building,
    DataCentre,
    DomesticHotWater,
    ElectricVehicles,
    EnergyStorageSystem,
    GasHeater,
    Grid,
    HeatPump,
    Mop,
    SolarPanel,
)
from app.models.epoch_types.task_data_type import TaskData as TaskDataPydantic
from app.models.site_data import EpochSiteData

import epoch_simulator as eps
from epoch_simulator import SimulationResult
from epoch_simulator import TaskData as EpochTaskData

type AnyComponent = (
    Building
    | DataCentre
    | DomesticHotWater
    | ElectricVehicles
    | EnergyStorageSystem
    | GasHeater
    | Grid
    | HeatPump
    | Mop
    | list[SolarPanel]
    | Config
    | None
)


def analyse_differences(start: TaskDataPydantic, end: TaskDataPydantic) -> dict[str, AnyComponent]:
    """
    Check the differences between two TaskDatas and mark what should be added to go from start to end.

    This checks each component in the end TaskData, and checks if it is different between start and end.
    If the component is added, we'll mark it as `component: {component_data}` in the changed_dict.
    If it is removed, we'll mark it as `component: None` in the changed_dict.
    Gas heaters are handled differently: they're often removed when heat pumps are installed,
    so we need to check if we've kept a backup gas heater or if it's being removed entirely.

    Parameters
    ----------
    start
        TaskData to start from
    end
        TaskData to end at, tracking what we have added to `start`

    Returns
    -------
    dict[str, Component | None]
        If a component is added, a type: component mapping for each component. Might be a list of components for solar panels.
        If None, means that component is removed.
    """
    changed = {}
    for field in sorted(end.model_fields_set):
        end_val = getattr(end, field)
        start_val = getattr(start, field)
        if end_val != start_val:
            changed[field] = end_val

    # If we're installing a heat pump and removing the gas heater, don't track that as a change.
    if "gas_heater" in changed and changed["gas_heater"] is None and changed.get("heat_pump") is not None:
        del changed["gas_heater"]
    return changed


def generate_upgrade_tree(
    start: TaskDataPydantic, end: TaskDataPydantic, site_data: EpochSiteData, config: Config | None = None
) -> dict[str, SimulationResult]:
    """
    Generate an upgrade tree of all the possible upgrades between start and end.

    This considers one upgrade roughly to be one key in the TaskData e.g. a heat_pump or solar_panels
    If you change one aspect of a component, we treat the whole component as having been replaced
    e.g. changing the fabric index swaps the whole building component, or we change all solar arrays at once.

    Parameters
    ----------
    start
        TaskData representing the "starting position" with no upgrades that will be used as a baseline
    end
        TaskData representing the "ending position" with all upgrades included.
    site_data
        EPOCH site data including heating, electrical load, tariffs etc
    config
        Configuration for the Simulator which picks reasonable defaults if not provided

    Returns
    -------
    dict[str, SiteOptimisationResult]
        Dictionary with bitstring names and raw optimisation result keys.
    """
    logger = logging.getLogger(__name__)
    if config is None:
        config = Config()

    # Copy the old site data and re-set the baseline to be the no-upgrades `start` case (making sure we don't overwrite it
    # if this was a site data that the user wants to re-visit elsewhere)
    site_data = site_data.model_copy(deep=True)
    site_data.baseline = start
    sim = eps.Simulator.from_json(site_data.model_dump_json(), config.model_dump_json())

    # We only count the number of additions, as each removal only happens when we add a component
    # e.g. adding a heat pump leads to removal of a gas heater; or changing solar panels removes the old ones.
    to_add = analyse_differences(start, end)
    num_differences = len(to_add)
    keys = sorted(to_add.keys())
    if num_differences > 8:
        logger.warning(f"Many differences in this site: expecting {2**num_differences} combinations, which will be slow.")

    all_results = {}
    for combination in itertools.product([False, True], repeat=num_differences):
        included = [key for key, c in zip(keys, combination, strict=False) if c]
        curr_td = start.model_copy(deep=True)
        for key in included:
            curr_td.__setattr__(key, getattr(end, key))
            # If we're installing a heat pump and know there's no gas heater at the end,
            # remove it during this step.
            if key == "heat_pump" and end.gas_heater is None:
                curr_td.gas_heater = None
        # Use these pithy names as they're easier to scan over when looking at the dict
        # and can be nicely re-labelled
        node_name = "".join(str(int(c)) for c in combination)
        res = sim.simulate_scenario(taskData=EpochTaskData.from_json(curr_td.model_dump_json()))
        all_results[node_name] = res
    return all_results
