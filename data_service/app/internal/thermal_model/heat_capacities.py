"""Heat capacities and u values for some common materials."""

from pathlib import Path

AIR_HEAT_CAPACITY = 1188  # J / m^3 K
BRICK_HEAT_CAPACITY = 840 * 1920  # J / m^3 K
CONCRETE_HEAT_CAPACITY = 880 * 2400  # J / m^3 K
TILE_HEAT_CAPACITY = 73.8 * 880 * 2  # J  m^2 K
GLASS_HEAT_CAPACITY = 1000.0  # made up

FLOOR_U_VALUE = 0.51
BRICK_U_VALUE = 0.56
STEEL_U_VALUE = 447.20
CONCRETE_U_VALUE = 1.25
ROOF_U_VALUE = 0.35
GLASS_U_VALUE = 2.80

U_VALUES_PATH = Path("./", "app", "internal", "thermal_model", "u_values.json")
