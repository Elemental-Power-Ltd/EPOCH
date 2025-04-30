import DefaultTaskData from "../../util/json/default/DefaultTaskData.json";
import DefaultSiteRange from "../../util/json/default/DefaultHumanFriendlySiteRange.json"

import {BuilderMode, ComponentsMap} from "../../Models/Core/ComponentBuilder";

export const getInitialComponentsMap = (mode: BuilderMode): ComponentsMap => {
    const defaultData = mode === "TaskDataMode" ? DefaultTaskData : DefaultSiteRange;

    // For now, we explicitly map out each component
    // we could instead derive this from the properties inside the schema
    // using the title property as the display name, falling back to the key
    const map: ComponentsMap = {
        building: {
            displayName: "Building",
            selected: true,
            data: defaultData["building"]
        },
        data_centre: {
            displayName: "Data Centre",
            selected: false,
            data: defaultData["data_centre"]
        },
        domestic_hot_water: {
            displayName: "Domestic Hot Water",
            selected: false,
            data: defaultData["domestic_hot_water"]
        },
        electric_vehicles: {
            displayName: "EV Chargers",
            selected: false,
            data: defaultData["electric_vehicles"]
        },
        energy_storage_system: {
            displayName: "Energy Storage",
            selected: false,
            data: defaultData["energy_storage_system"]
        },
        gas_heater: {
            "displayName": "Gas Heater",
            selected: false,
            data: defaultData["gas_heater"]
        },
        grid: {
            displayName: "Grid",
            selected: true,
            data: defaultData["grid"]
        },
        heat_pump: {
            displayName: "Heat Pump",
            selected: false,
            data: defaultData["heat_pump"]
        },
        mop: {
            displayName: "Mop",
            selected: false,
            data: defaultData["mop"]
        },
        renewables: {
            displayName: "Renewables",
            selected: false,
            data: defaultData["renewables"]
        },
        config: {
            displayName: "Config",
            selected: true,
            data: defaultData["config"]
        }

    };

    return map;
}
