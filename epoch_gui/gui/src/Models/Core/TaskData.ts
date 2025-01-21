
// These are all of the different Component Types in TaskData
export type ComponentType =
    | "building"
    | "data_centre"
    | "domestic_hot_water"
    | "electric_vehicles"
    | "energy_storage_system"
    | "grid"
    | "heat_pump"
    | "mop"
    | "renewables";



export interface ComponentDetails {
    displayName: string;
    selected: boolean;
    data: any;
}


// This defines the display data needed for constructing a TaskData
export type ComponentsMap = {
    [key in ComponentType]: ComponentDetails;
};