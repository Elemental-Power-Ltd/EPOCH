"""GivEnergy API types, which can be nested and complex."""

from typing import TypedDict

# ruff: noqa: D101


class SolarArrayDict(TypedDict):
    array: int  # index
    voltage: float  # Volt
    current: float  # Amp
    power: float  # Watts


class GridDict(TypedDict):
    current: float  # Amp
    voltage: float  # Volt
    power: float  # Watt
    frequency: float  # Hz


class SolarDict(TypedDict):
    arrays: list[SolarArrayDict]


class BatteryDict(TypedDict):
    percent: float
    power: float
    temperature: float


class InverterDict(TypedDict):
    temperature: float
    output_voltage: float
    output_frequency: float
    eps_power: float
    power: float


class ConsumptionDict(TypedDict):
    consumption: float
    power: float


class GivEnergyPowerDict(TypedDict):
    solar: SolarDict
    grid: GridDict
    battery: BatteryDict
    inverter: InverterDict
    consumption: ConsumptionDict


class BatteryAggregateDict(TypedDict):
    charge: float
    discharge: float


GridAggregateDict = TypedDict("GridAggregateDict", {"import": float, "export": float})  # import is reserved


class GivEnergyAggregateDict(TypedDict):
    solar: float
    grid: dict[str, float]
    battery: dict[str, float]
    consumption: float
    ac_charge: float


class GivEnergyDict(TypedDict, total=False):
    power: GivEnergyPowerDict
    time: str
    status: str
    today: GivEnergyAggregateDict
    total: GivEnergyAggregateDict
    is_metered: str


class GivEnergyLinksDict(TypedDict, total=False):
    next: str


class FullGivEnergyResponse(TypedDict, total=False):
    data: list[GivEnergyDict]
    links: GivEnergyLinksDict
    detail: str | None
