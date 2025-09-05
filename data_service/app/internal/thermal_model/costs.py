"""Calculate costs from the size of the components and THIRD_PARTY's cost table."""

from ...models.heating_load import InterventionEnum, ThermalModelResult
from ...models.thermal_model import SurveyedSizes
from .building_elements import BuildingElement
from .links import ConductiveLink
from .network import HeatNetwork, create_structure_from_params, create_structure_from_survey
from .phpp.interventions import THIRD_PARTY_INTERVENTIONS, StructuralArea


def get_wall_areas(structure: HeatNetwork) -> float:
    """
    Get the exterior wall area of this structure in m^2.

    Parameters
    ----------
    structure
        Structure, of which some are BuildingElement.Wall* types

    Returns
    -------
    float
        External area of the walls in contact with the outside air, in m^2
    """
    wall_types = frozenset({
        BuildingElement.WallEast,
        BuildingElement.WallNorth,
        BuildingElement.WallSouth,
        BuildingElement.WallWest,
    })
    area = 0.0
    for u, v, data in structure.edges(data=True):
        if (u in wall_types or v in wall_types) and BuildingElement.ExternalAir in {u, v}:
            area += data["conductive"].interface_area
    return area


def get_window_areas(structure: HeatNetwork) -> float:
    """
    Get the exterior window area of this structure in m^2.

    Parameters
    ----------
    structure
        Structure, of which some are BuildingElement.Window* types

    Returns
    -------
    float
        External area of the walls in contact with the outside air, in m^2
    """
    window_types = frozenset({
        BuildingElement.WindowsEast,
        BuildingElement.WindowsNorth,
        BuildingElement.WindowsSouth,
        BuildingElement.WindowsWest,
    })
    area = 0.0
    for u, v, data in structure.edges(data=True):
        if (u in window_types or v in window_types) and BuildingElement.ExternalAir in {u, v}:
            area += data["conductive"].interface_area
    return area


def get_ceiling_areas(structure: HeatNetwork) -> float:
    """
    Get the loft area of this structure.

    The loft area is marked as the section between the roof and the internal air (we treat the whole thing as one element)

    Parameters
    ----------
    structure
        Structure, which has a (InternalAir, Roof) edge

    Returns
    -------
    float
        Size of the loft in contact with the internal air in m^2
    """
    return float(
        structure.get_edge_data(
            BuildingElement.InternalAir,
            BuildingElement.Roof,
            default={"conductive": ConductiveLink(interface_area=0.0, heat_transfer=0.0)},
        )["conductive"].interface_area
    )


def get_floor_areas(structure: HeatNetwork) -> float:
    """
    Get the floor area of this structure.

    The floor area is marked as the section between the floor and the internal air (we treat the whole thing as one element)

    Parameters
    ----------
    structure
        Structure, which has a (InternalAir, Floor) edge

    Returns
    -------
    float
        Size of the floor in contact with the internal air in m^2
    """
    return float(
        structure.get_edge_data(
            BuildingElement.InternalAir,
            BuildingElement.Floor,
            default={"conductive": ConductiveLink(interface_area=0.0, heat_transfer=0.0)},
        )["conductive"].interface_area
    )


def calculate_doubleglazing_cost(structure: HeatNetwork) -> float:
    """
    Calculate the cost of improving the windows for this site.

    This uses a fixed cost per m2 from THIRD_PARTY's tables, and returns
    the total cost in GBP.

    Parameters
    ----------
    structure
        Structure with BuildingElement.Windows* elements

    Returns
    -------
        Approximate total cost in GBP to replace the windows.
    """
    # This is "Replacement External Windows"
    # from THIRD_PARTY's table, described as
    # > Replacement of existing poor quality / fitting doors with new
    # > windows. Single glazing/ metal frame, etc with double or triple.
    return get_window_areas(structure) * THIRD_PARTY_INTERVENTIONS["Replacement External Windows"]["cost"]


def calculate_cladding_cost(structure: HeatNetwork) -> float:
    """
    Calculate the cost of cladding the building with external cladding.

    This uses a fixed cost per m2 from THIRD_PARTY's tables, and returns
    the total cost in GBP.
    This is likely to be an under-estimate as it presumes flat walls.

    Parameters
    ----------
    structure
        Structure with BuildingElement.Wall* elements

    Returns
    -------
        Approximate total cost in GBP to clad the exterior walls.
    """
    # This is "External Insulation to external cavity wall"
    # from THIRD_PARTY's table, not a External Overbuild
    return get_wall_areas(structure) * THIRD_PARTY_INTERVENTIONS["External Insulation to external cavity wall"]["cost"]


def calculate_loft_cost(structure: HeatNetwork) -> float:
    """
    Calculate the cost of insulating the loft of this building.

    This uses a fixed cost per m2 from THIRD_PARTY's tables, and returns
    the total cost in GBP.

    Parameters
    ----------
    structure
        Structure, which has a (InternalAir, Roof) edge

    Returns
    -------
        Approximate total cost in GBP to insulate the loft.
    """
    # This is "Insulation to ceiling void" from THIRD_PARTY's table
    # Described as
    # > Blown stone fireproof insulation to be installed in loft voids.
    return get_ceiling_areas(structure) * THIRD_PARTY_INTERVENTIONS["Insulation to ceiling void"]["cost"]


def calculate_intervention_costs_structure(structure: HeatNetwork, interventions: list[InterventionEnum]) -> float:
    """
    Calculate the costs for a list of interventions on a pre-made Heat Network structure.

    The HeatNetwork represents a building with walls, windows, ceiling etc. and we will
    look up the interventions you want to make and their appropriate costs per m^2.
    These will be scaled by the size of the building and added together.

    Parameters
    ----------
    structure
        HeatNetwork of the building with walls, windows etc to improve
    interventions
        The interventions you wish to apply e.g. Cladding, Double Glazing

    Returns
    -------
        Total cost for those interventions on this structure in GBP.
    """
    if not interventions:
        # If we're doing no interventions,
        # it costs nothing
        return 0.0
    INTERVENTION_MAP = {
        InterventionEnum.Cladding: calculate_cladding_cost,
        InterventionEnum.DoubleGlazing: calculate_doubleglazing_cost,
        InterventionEnum.Loft: calculate_loft_cost,
    }
    return sum(INTERVENTION_MAP[intervention](structure) for intervention in interventions)


def calculate_intervention_costs_params(params: ThermalModelResult, interventions: list[InterventionEnum]) -> float:
    """
    Calculate the costs for a list of interventions on a building described by fitted parameters.

    We'll use the fitted parameters, probably from a thermal model fitting processs, to create a simple structure
    which is a cuboid of the building. We'll then  look up the interventions you want to make and
    their appropriate costs per m^2. These will be scaled by the size of the building and added together.

    Parameters
    ----------
    params
        Parameters, including a scale factor that you wish to apply to the building.
    interventions
        The interventions you wish to apply e.g. Cladding, Double Glazing

    Returns
    -------
        Total cost for those interventions on this structure in GBP.
    """
    structure = create_structure_from_params(
        scale_factor=params.scale_factor,
        ach=params.ach,
        u_value=params.u_value,
        boiler_power=params.boiler_power,
        setpoint=params.setpoint,
    )
    return calculate_intervention_costs_structure(structure, interventions)


def calculate_THIRD_PARTY_intervention_costs(
    surveyed_sizes: SurveyedSizes, interventions: list[str] | list[InterventionEnum]
) -> float:
    """
    Calculate the costs for a list of interventions on a building surveyed by THIRD_PARTY.

    Parameters
    ----------
    surveyed_sizes
        Sizes of windows, walls etc that you measured from a floor plan in m^2.
    interventions
        The interventions you wish to apply with names matching those in the survey report (or generic types for an estimate)

    Returns
    -------
        Total cost for those interventions on this structure in GBP.
    """
    structure = create_structure_from_survey(surveyed_sizes)
    window_area = get_window_areas(structure)
    exterior_wall_area = get_wall_areas(structure)
    floor_area = get_floor_areas(structure)
    ceiling_area = get_ceiling_areas(structure)

    total_cost = 0.0
    for intervention_name in interventions:
        # We've got a generic intervention
        if intervention_name == InterventionEnum.Cladding:
            total_cost += calculate_cladding_cost(structure)
        elif intervention_name == InterventionEnum.DoubleGlazing:
            total_cost += calculate_doubleglazing_cost(structure)
        elif intervention_name == InterventionEnum.Loft:
            total_cost += calculate_loft_cost(structure)
        else:
            # We've got a specific intervention from the table
            acts_on = THIRD_PARTY_INTERVENTIONS[intervention_name.lower()]["acts_on"]
            cost = THIRD_PARTY_INTERVENTIONS[intervention_name.lower()]["cost"]
            match acts_on:
                case StructuralArea.WindowArea:
                    total_cost += window_area * cost
                case StructuralArea.FloorArea:
                    total_cost += floor_area * cost
                case StructuralArea.RoofArea:
                    total_cost += ceiling_area * cost
                case StructuralArea.ExteriorWallArea:
                    total_cost += exterior_wall_area * cost
    return total_cost
