from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field


class Building(BaseModel):
    COMPONENT_IS_MANDATORY: bool
    scalar_heat_load: list[Annotated[int, Field(ge=0)]]
    scalar_electrical_load: list[Annotated[int, Field(ge=0)]]
    fabric_intervention_index: list[Annotated[int, Field(ge=0)]]


class DataCentre(BaseModel):
    COMPONENT_IS_MANDATORY: bool
    maximum_load: list[Annotated[int, Field(ge=0)]]
    hotroom_temp: list[float]


class DomesticHotWater(BaseModel):
    COMPONENT_IS_MANDATORY: bool
    cylinder_volume: list[Annotated[float, Field(ge=0)]]


class ElectricVehicles(BaseModel):
    COMPONENT_IS_MANDATORY: bool
    flexible_load_ratio: list[Annotated[float, Field(ge=0.0, le=1.0)]]
    small_chargers: list[Annotated[int, Field(ge=0)]]
    fast_chargers: list[Annotated[int, Field(ge=0)]]
    rapid_chargers: list[Annotated[int, Field(ge=0)]]
    ultra_chargers: list[Annotated[int, Field(ge=0)]]
    scalar_electrical_load: list[Annotated[int, Field(ge=0)]]


class BatteryModeEnum(StrEnum):
    CONSUME = "CONSUME"


class EnergyStorageSystem(BaseModel):
    COMPONENT_IS_MANDATORY: bool
    capacity: list[Annotated[float, Field(gt=0.0)]]
    charge_power: list[Annotated[float, Field(gt=0.0)]]
    discharge_power: list[Annotated[float, Field(gt=0.0)]]
    battery_mode: list[BatteryModeEnum]
    initial_charge: list[Annotated[float, Field(ge=0.0)]]


class Grid(BaseModel):
    COMPONENT_IS_MANDATORY: bool
    export_headroom: list[Annotated[float, Field(ge=0.0, le=1.0)]]
    grid_export: list[Annotated[int, Field(ge=0)]]
    grid_import: list[Annotated[int, Field(ge=0)]]
    import_headroom: list[Annotated[float, Field(ge=0.0, le=1.0)]]
    min_power_factor: list[Annotated[float, Field(ge=0.0, le=1.0)]]
    tariff_index: list[Annotated[int, Field(ge=0)]]


class HeatSourceEnum(StrEnum):
    AMBIENT_AIR = "AMBIENT_AIR"
    HOTROOM = "HOTROOM"


class HeatPump(BaseModel):
    COMPONENT_IS_MANDATORY: bool
    heat_power: list[Annotated[float, Field(ge=0.0)]]
    heat_source: list[HeatSourceEnum]
    send_temp: list[float]


class Mop(BaseModel):
    COMPONENT_IS_MANDATORY: bool
    maximum_load: list[Annotated[int, Field(ge=0)]]


class Renewables(BaseModel):
    COMPONENT_IS_MANDATORY: bool
    yield_scalars: list[list[Annotated[float, Field(ge=0.0)]]]


class Config(BaseModel):
    capex_limit: Annotated[float, Field(ge=0.0)]


class SiteRange(BaseModel):
    building: Building | None = None
    data_centre: DataCentre | None = None
    domestic_hot_water: DomesticHotWater | None = None
    electric_vehicles: ElectricVehicles | None = None
    energy_storage_system: EnergyStorageSystem | None = None
    grid: Grid | None = None
    heat_pump: HeatPump | None = None
    mop: Mop | None = None
    renewables: Renewables | None = None
    config: Config | None = None
