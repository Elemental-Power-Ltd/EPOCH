

export type Direction = "North" | "East" | "South" | "West";
export type HeatSource = "Boiler" | "HeatPump";
export type Location = "Cardiff" | "London" | "Edinburgh";
export type BuildingType = "Domestic" | "TownHall" | "LeisureCentre";

export interface PanelInfo {
    solar_peak: number;
    direction: Direction;
}

export interface HeatInfo {
    heat_power: number;
    heat_source: HeatSource;
}

export interface InsulationInfo {
    double_glazing: boolean;
    cladding: boolean;
    loft: boolean;
}

export interface BatteryInfo {
    capacity: number;
    power: number;
}

export interface SimulationRequest {
    location: Location;
    building: BuildingType;

    panels: PanelInfo[];
    heat: HeatInfo;
    insulation: InsulationInfo;
    battery: BatteryInfo | null;

    full_reporting: boolean;
}
