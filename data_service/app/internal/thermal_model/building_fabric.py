"""
Functions for a simple model of building fabric.

Here, we apply a simple % saving to the total kwh per HDD number.
"""

import copy
import json
from pathlib import Path

from ...models.heating_load import InterventionEnum, ThermalModelResult
from ...models.weather import BaitAndModelCoefs
from .building_elements import BuildingElement
from .heat_capacities import CONCRETE_U_VALUE, U_VALUES_PATH
from .network import HeatNetwork, create_structure_from_params

# FABRIC_SAVINGS = {
#    InterventionEnum.Loft: 1 - (2.4 / 100),  # via NEED 2021
#    InterventionEnum.Cladding: 1 - (8.8 / 100),  # via NEED 2021
#    InterventionEnum.DoubleGlazing: 1 - (4.4 / 100),
#    # via https://www.sciencedirect.com/science/article/abs/pii/S0378778819312782
# }

# These numbers are made up!
FABRIC_SAVINGS = {
    InterventionEnum.Loft: 1 - 0.1,
    InterventionEnum.Cladding: 1 - 0.2,
    InterventionEnum.DoubleGlazing: 1 - 0.15,
}

FABRIC_WINDCHILL = {InterventionEnum.Loft: 1.00, InterventionEnum.Cladding: 0.95, InterventionEnum.DoubleGlazing: 0.90}


def apply_fabric_interventions(bait_coefs: BaitAndModelCoefs, interventions: list[InterventionEnum]) -> BaitAndModelCoefs:
    """
    Apply some fabric interventions to the BAIT and model coefficients to mimic energy savings.

    This is currently a filthy hack -- be wary! It just drops the heating kWh per HDD by
    a flat savings percentage, and for some interventions will also affect the BAIT windchill
    coefficient.
    You can get the costs of each intervention from `/get-intervention-costs`.

    Parameters
    ----------
    bait_coefs
        Fitted BAIT and heating model coefficients, calculated from gas meter data.
    interventions
        Some building fabric interventions you would like to do.
        Currently assumes that these are multiplicative
        (e.g. two interventions with 10% saving lead to 19% total saving)

    Returns
    -------
    modified BAIT and heating model coefficients, mostly changed in `heating_kwh`
    """
    # make sure we don't mutate the original
    new_coefs = copy.deepcopy(bait_coefs)
    for intervention in interventions:
        new_coefs.heating_kwh *= FABRIC_SAVINGS[intervention]
        new_coefs.wind_chill *= FABRIC_WINDCHILL[intervention]
    return new_coefs


def apply_interventions_to_structure(
    structure: HeatNetwork, interventions: list[InterventionEnum], u_values_path: Path = U_VALUES_PATH
) -> HeatNetwork:
    """
    Apply a list of interventions to a pre-constructed HeatNetwork representing a structure.

    This will replace the heat transfer and ACH coefficients of the appropriate edges in the graph.

    Parameters
    ----------
    HeatNetwork
        A thermal network representing heat flows in a given building. This is copied, and not modified.
    interventions
        A list of interventions you would like to apply, e.g. InterventionEnum.Loft
    u_values_path
        Path to a JSON file containing U-values for interventions (you may wish to change this if importing from a notebook)

    Returns
    -------
    HeatNetwork
        A new heat network with the fabric interventions applied, ready for simulation.
    """
    new_structure = copy.deepcopy(structure)
    U_VALUE_DB = json.loads(u_values_path.read_text())
    if InterventionEnum.Loft in interventions:
        new_loft_u = U_VALUE_DB[
            "Pitched roof - Slates or tiles, sarking felt, ventilated air space,"
            + " 300mm insulation between joists, 9.5 mm plasterboard"
        ]
        new_structure[BuildingElement.InternalAir][BuildingElement.Roof]["conductive"].heat_transfer = new_loft_u

    if InterventionEnum.DoubleGlazing in interventions:
        new_window_u = U_VALUE_DB["Glazed wood or PVC-U door Metal Double Glazed"]

        for window in [BuildingElement.WindowsSouth, BuildingElement.WindowsNorth]:
            new_structure[BuildingElement.InternalAir][window]["conductive"].heat_transfer = new_window_u
            new_structure[window][BuildingElement.ExternalAir]["conductive"].heat_transfer = new_window_u

        new_structure[BuildingElement.InternalAir][BuildingElement.ExternalAir]["convective"].ach *= 0.8

    if InterventionEnum.Cladding in interventions:
        new_wall_u = U_VALUE_DB[
            "Shiplap boards, airspace, standard aerated block 100mm,"
            + " mineral wool slab in cavity 50mm, 125mm high performance block (K=0.11), 13mm plaster"
        ]
        for wall in [BuildingElement.WallSouth, BuildingElement.WallEast, BuildingElement.WallNorth, BuildingElement.WallWest]:
            new_structure[BuildingElement.InternalAir][wall]["conductive"].heat_transfer = new_wall_u
            new_structure[wall][BuildingElement.ExternalAir]["conductive"].heat_transfer = new_wall_u

        new_structure[BuildingElement.InternalAir][BuildingElement.ExternalAir]["convective"].ach = 0.6

    return new_structure


def apply_thermal_model_fabric_interventions(
    params: ThermalModelResult,
    interventions: list[InterventionEnum],
    structure: HeatNetwork | None = None,
    u_values_path: Path = U_VALUES_PATH,
) -> ThermalModelResult:
    """
    Apply interventions to a thermal model result with realistic U-values.

    This will use the ratios of windows, walls, etc from the standard structure
    and treat the calculated U-value as a composite U-value of all the components.
    Then, we'll assume that the existing compontents are all a reasonably bad version,
    and swap out their U-values for the new ones.
    We use the RDSAP U-value database in a JSON file, and also apply air changes per hour
    corrections depending on the intervention.

    Parameters
    ----------
    params
        Fitted thermal model result with U value and ACH
    interventions
        List of building fabric interventions you'd like to do
    structure
        The structure to apply these interventions to; if None, will create a simple structure from the parameters.
    u_values_path
        Path to a JSON file of materials and U-values

    Returns
    -------
    ThermalModelResult
        Parameters for thermal modelling of the improved building.
    """
    # Don't clobber the previously-fit thermal model.
    new_params = copy.deepcopy(params)
    if structure is None:
        structure = create_structure_from_params(
            scale_factor=new_params.scale_factor,
            ach=new_params.ach,
            u_value=new_params.u_value,
            boiler_power=new_params.boiler_power,
            setpoint=new_params.setpoint,
        )
    # Make sure that we don't beat this later
    initial_u_value = new_params.u_value

    window_area = 0.0
    wall_area = 0.0
    floor_area = 0.0
    roof_area = 0.0
    for u, v, data in structure.edges(data=True):
        if BuildingElement.ExternalAir not in {u, v}:
            continue
        if "window" in u.value.lower() or "window" in v.value.lower():
            window_area += data["conductive"].interface_area
        if "wall" in u.value.lower() or "wall" in v.value.lower():
            wall_area += data["conductive"].interface_area
        if BuildingElement.Roof in {u, v}:
            roof_area += data["conductive"].interface_area
        if BuildingElement.Floor in {u, v}:
            floor_area += data["conductive"].interface_area

    total_area = window_area + wall_area + floor_area + roof_area
    wall_frac = wall_area / total_area
    roof_frac = roof_area / total_area
    window_frac = window_area / total_area
    floor_frac = floor_area / total_area

    U_VALUE_DB = json.loads(u_values_path.read_text())
    existing_rvalue_sum = 1.0 / new_params.u_value

    IMPROVED_U_WALL = U_VALUE_DB[
        "Shiplap boards, airspace, standard aerated block 100mm,"
        + " mineral wool slab in cavity 50mm, 125mm high performance block (K=0.11), 13mm plaster"
    ]
    IMPROVED_U_LOFT = U_VALUE_DB[
        "Pitched roof - Slates or tiles, sarking felt, ventilated air space,"
        + " 300mm insulation between joists, 9.5 mm plasterboard"
    ]
    IMPROVED_U_WINDOW = U_VALUE_DB["Glazed wood or PVC-U door Metal Double Glazed"]
    IMPROVED_U_FLOOR = CONCRETE_U_VALUE

    # Apply some checks to these equations: make sure we don't drop below the minimum U value of any given component,
    # and that we don't end up with a negative total U-value
    if InterventionEnum.DoubleGlazing in interventions:
        existing_rvalue_sum -= window_frac / U_VALUE_DB["Glazed wood or PVC-U door Metal Single Glazed"]
        existing_rvalue_sum += window_frac / IMPROVED_U_WINDOW
        new_params.ach = min(new_params.ach * 0.8, 10.0)

    if InterventionEnum.Cladding in interventions:
        existing_rvalue_sum -= (
            wall_frac
            / U_VALUE_DB["Brick 102mm, mineral wool slab in cavity 50mm, 100mm standard aerated block (k=0.17), 13mm plaster"]
        )
        existing_rvalue_sum += wall_frac / IMPROVED_U_WALL
        new_params.ach = 0.6

    if InterventionEnum.Loft in interventions:
        existing_rvalue_sum -= (
            roof_frac
            / U_VALUE_DB[
                "Pitched roof - Slates or tiles, sarking felt, ventilated air space,"
                + " 100mm insulation between joists, 9.5 mm plasterboard"
            ]
        )
        existing_rvalue_sum += roof_frac / IMPROVED_U_LOFT

    minimum_r_value = (
        wall_frac / IMPROVED_U_WALL
        + window_frac / IMPROVED_U_WINDOW
        + roof_frac / IMPROVED_U_LOFT
        + floor_frac / IMPROVED_U_FLOOR
    )
    existing_rvalue_sum = min(minimum_r_value, existing_rvalue_sum)
    new_params.u_value = min(initial_u_value, 1.0 / existing_rvalue_sum)
    return new_params
