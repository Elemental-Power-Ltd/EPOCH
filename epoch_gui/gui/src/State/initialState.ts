import DefaultTaskData from "../util/json/default/DefaultTaskData.json";
import {ComponentsMap} from "../Models/Core/TaskData";

// TODO - it may be better to derive this from the schema?
export const initialComponents: ComponentsMap = {
    building: {
        displayName: "Building",
        selected: false,
        data: DefaultTaskData["building"]},
    data_centre: {
        displayName: "Data Centre",
        selected: false,
        data: DefaultTaskData["data_centre"]},
    domestic_hot_water: {
        displayName: "Domestic Hot Water",
        selected: false,
        data: DefaultTaskData["domestic_hot_water"]
    },
    electric_vehicles: {
        displayName: "Electric Vehicles",
        selected: false, data:
            DefaultTaskData["electric_vehicles"]},
    energy_storage_system: {
        displayName: "Energy Storage",
        selected: false,
        data: DefaultTaskData["energy_storage_system"]
    },
    grid: {
        displayName: "Grid",
        selected: false,
        data: DefaultTaskData["grid"]},
    heat_pump: {
        displayName: "Heat Pump",
        selected: false,
        data: DefaultTaskData["heat_pump"]},
    mop: {
        displayName: "Mop",
        selected: false, data:
            DefaultTaskData["mop"]},
    renewables: {
        displayName: "Renewables",
        selected: false,
        data: DefaultTaskData["renewables"]
    },
};

// FIXME - for simplicity, the config is hardcoded (at 10m)
export const hardcodedConfig = {capex_limit: 10000000};