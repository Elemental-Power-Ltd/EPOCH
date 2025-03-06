"""Calculate costs from the size of the components and THIRD_PARTY's cost table."""

from ...models.heating_load import InterventionEnum, ThermalModelResult
from .building_elements import BuildingElement
from .fitting import create_structure_from_params
from .network import HeatNetwork


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
        if (u in wall_types or v in wall_types) and BuildingElement.ExternalAir in (u, v):
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
        if (u in window_types or v in window_types) and BuildingElement.ExternalAir in (u, v):
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
    return structure.get_edge_data(BuildingElement.InternalAir, BuildingElement.Roof)["conductive"].interface_area


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
    # This is " Replacement External Windows"
    # from THIRD_PARTY's table, described as
    # > Replacement of existing poor quality / fitting doors with new
    # > windows. Single glazing/ metal frame, etc with double or triple.
    COST_PER_M2 = 1001.83
    return get_window_areas(structure) * COST_PER_M2


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
    COST_PER_M2 = 415.68
    return get_wall_areas(structure) * COST_PER_M2


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
    COST_PER_M2 = 150.00
    return get_ceiling_areas(structure) * COST_PER_M2


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
