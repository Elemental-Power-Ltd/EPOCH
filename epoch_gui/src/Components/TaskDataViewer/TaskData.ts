export enum BatteryMode {
  CONSUME = "CONSUME",
  CONSUME_PLUS = "CONSUME_PLUS",
}

export enum GasType {
  NATURAL_GAS = "NATURAL_GAS",
  LIQUID_PETROLEUM_GAS = "LIQUID_PETROLEUM_GAS",
}

export enum HeatSource {
  AMBIENT_AIR = "AMBIENT_AIR",
  HOTROOM = "HOTROOM",
}

export interface Config {
  capex_limit: number;
  use_boiler_upgrade_scheme: boolean;
  general_grant_funding: number;
  npv_time_horizon: number;
  npv_discount_factor: number;
}

export interface Building {
  scalar_heat_load: number;
  scalar_electrical_load: number;
  fabric_intervention_index: number;
  incumbent: boolean;
  age: number;
  lifetime: number;
}

export interface DataCentre {
  maximum_load: number;
  hotroom_temp: number;
  incumbent: boolean;
  age: number;
  lifetime: number;
}

export interface DomesticHotWater {
  cylinder_volume: number;
  incumbent: boolean;
  age: number;
  lifetime: number;
}

export interface ElectricVehicles {
  flexible_load_ratio: number;
  small_chargers: number;
  fast_chargers: number;
  rapid_chargers: number;
  ultra_chargers: number;
  scalar_electrical_load: number;
  incumbent: boolean;
  age: number;
  lifetime: number;
}

export interface EnergyStorageSystem {
  capacity: number;
  charge_power: number;
  discharge_power: number;
  battery_mode: BatteryMode;
  initial_charge: number;
  incumbent: boolean;
  age: number;
  lifetime: number;
}

export interface GasHeater {
  maximum_output: number;
  gas_type: GasType;
  boiler_efficiency: number;
  incumbent: boolean;
  age: number;
  lifetime: number;
}

export interface Grid {
  grid_export: number;
  grid_import: number;
  import_headroom: number;
  tariff_index: number;
  export_tariff: number;
  incumbent: boolean;
  age: number;
  lifetime: number;
}

export interface HeatPump {
  heat_power: number;
  heat_source: HeatSource;
  send_temp: number;
  incumbent: boolean;
  age: number;
  lifetime: number;
}

export interface Mop {
  maximum_load: number;
  incumbent: boolean;
  age: number;
  lifetime: number;
}

export interface SolarPanel {
  yield_scalar: number;
  yield_index: number;
  incumbent: boolean;
  age: number;
  lifetime: number;
}

export interface TaskData {
  config: Config;
  building?: Building;
  data_centre?: DataCentre;
  domestic_hot_water?: DomesticHotWater;
  electric_vehicles?: ElectricVehicles;
  energy_storage_system?: EnergyStorageSystem;
  gas_heater?: GasHeater;
  grid?: Grid;
  heat_pump?: HeatPump;
  mop?: Mop;
  solar_panels?: SolarPanel[];
}
