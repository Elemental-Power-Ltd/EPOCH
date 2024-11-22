"""Building elements and useful properties by type."""

import enum

from .heat_capacities import (
    BRICK_HEAT_CAPACITY,
    BRICK_U_VALUE,
    CONCRETE_HEAT_CAPACITY,
    CONCRETE_U_VALUE,
    GLASS_HEAT_CAPACITY,
    GLASS_U_VALUE,
)


class BuildingElement(enum.StrEnum):
    """Specific set of building elements we can use."""

    Ground = enum.auto()
    Sun = enum.auto()
    ExternalAir = enum.auto()

    InternalAir = enum.auto()
    WallSouth = enum.auto()
    WallEast = enum.auto()
    WallNorth = enum.auto()
    WallWest = enum.auto()

    WindowsSouth = enum.auto()
    WindowsEast = enum.auto()
    WindowsNorth = enum.auto()
    WindowsWest = enum.auto()

    Floor = enum.auto()
    Roof = enum.auto()

    InternalGains = enum.auto()
    HeatSource = enum.auto()
    HeatingSystem = enum.auto()


ELEMENT_U_VALUES = {
    BuildingElement.WallSouth: BRICK_U_VALUE,
    BuildingElement.WallNorth: BRICK_U_VALUE,
    BuildingElement.WallEast: BRICK_U_VALUE,
    BuildingElement.WallWest: BRICK_U_VALUE,
    BuildingElement.Floor: CONCRETE_U_VALUE,
    BuildingElement.Roof: CONCRETE_U_VALUE,
    BuildingElement.WindowsEast: GLASS_U_VALUE,
    BuildingElement.WindowsWest: GLASS_U_VALUE,
    BuildingElement.WindowsNorth: GLASS_U_VALUE,
    BuildingElement.WindowsSouth: GLASS_U_VALUE,
}

ELEMENT_HEAT_CAPACITIES = {
    BuildingElement.WallSouth: BRICK_HEAT_CAPACITY,
    BuildingElement.WallNorth: BRICK_HEAT_CAPACITY,
    BuildingElement.WallEast: BRICK_HEAT_CAPACITY,
    BuildingElement.WallWest: BRICK_HEAT_CAPACITY,
    BuildingElement.Floor: CONCRETE_HEAT_CAPACITY,
    BuildingElement.Roof: CONCRETE_HEAT_CAPACITY,
    BuildingElement.WindowsEast: GLASS_HEAT_CAPACITY,
    BuildingElement.WindowsWest: GLASS_HEAT_CAPACITY,
    BuildingElement.WindowsNorth: GLASS_HEAT_CAPACITY,
    BuildingElement.WindowsSouth: GLASS_HEAT_CAPACITY,
}
