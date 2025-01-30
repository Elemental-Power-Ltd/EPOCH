
// These are all of the different Component Types present in TaskData & SiteRange
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

// Whether we are building components for a
//  - a single simulation (TaskData)
//  - an optimisation (SiteRange)
export type BuilderMode = "TaskDataMode" | "SiteRangeMode";


export interface ComponentDetails {
    displayName: string;
    selected: boolean;
    data: any;
}


// This defines the display data needed for constructing a TaskData
export type ComponentsMap = {
    [key in ComponentType]: ComponentDetails;
};