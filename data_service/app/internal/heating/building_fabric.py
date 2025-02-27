"""
Functions for a simple model of building fabric.

Here, we apply a simple % saving to the total kwh per HDD number.
"""

import copy
import json
from pathlib import Path

from ...models.heating_load import InterventionEnum, ThermalModelResult
from ...models.weather import BaitAndModelCoefs
from ..thermal_model.fitting import create_structure_from_params
from ..thermal_model.building_elements import BuildingElement
from ..thermal_model.heat_capacities import CONCRETE_U_VALUE

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


def apply_thermal_model_fabric_interventions(
    params: ThermalModelResult, interventions: list[InterventionEnum]
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

    Returns
    -------
    ThermalModelResult
        Parameters for thermal modelling of the improved building.
    """
    # Make sure that we don't beat this later
    initial_u_value = params.u_value

    structure = create_structure_from_params(
        scale_factor=params.scale_factor,
        ach=params.ach,
        u_value=params.u_value,
        boiler_power=params.boiler_power,
        setpoint=params.setpoint,
    )

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

    U_VALUE_DB = json.loads(Path("./", "app", "internal", "thermal_model", "u_values.json").read_text())
    existing_rvalue_sum = 1.0 / params.u_value

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
        params.ach = min(params.ach * 0.8, 10.0)

    if InterventionEnum.Cladding in interventions:
        existing_rvalue_sum -= (
            wall_frac
            / U_VALUE_DB["Brick 102mm, mineral wool slab in cavity 50mm, 100mm standard aerated block (k=0.17), 13mm plaster"]
        )
        existing_rvalue_sum += wall_frac / IMPROVED_U_WALL
        params.ach = 0.6

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
    params.u_value = min(initial_u_value, 1.0 / existing_rvalue_sum)
    return params
