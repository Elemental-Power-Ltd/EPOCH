import DefaultTaskData from "../../util/json/default/DefaultTaskData.json";
import DefaultSiteRange from "../../util/json/default/DefaultHumanFriendlySiteRange.json"

import {BuilderMode, ComponentsMap} from "../../Models/Core/ComponentBuilder";

export const getInitialComponentsMap = (mode: BuilderMode, baseline: any): ComponentsMap => {
    const defaultData = mode === "TaskDataMode" ? DefaultTaskData : DefaultSiteRange;

    // For now, we explicitly map out each component
    // we could instead derive this from the properties inside the schema
    // using the title property as the display name, falling back to the key
    const map: ComponentsMap = {
        building: {
            displayName: "Building",
            selected: false,
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
            displayName: "Gas Heater",
            selected: false,
            data: defaultData["gas_heater"]
        },
        grid: {
            displayName: "Grid",
            selected: false,
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
        solar_panels: {
            displayName: "Solar Panels",
            selected: false,
            data: defaultData["solar_panels"]
        }
    };

    Object.keys(baseline).forEach((key) => {
            // We don't want to take the config from the baseline
            if (key === "config") {
                return;
            }

            if (baseline[key] !== null) {
                if (mode === "TaskDataMode") {
                    map[key as keyof ComponentsMap].data = baseline[key];
                } else if (mode === "SiteRangeMode") {
                    map[key as keyof ComponentsMap].data = rangifyComponent(map[key as keyof ComponentsMap].data, baseline[key]);
                }

                map[key as keyof ComponentsMap].selected = true;
            }
        });

    return map;
}


// This function is one giant hack
// We have a baseline TaskData component that we want to translate into a SiteRange component
// This requires translating properties from a single value into ranges (with just that single value in them)
// but we don't know if those ranges should be {min,max,step} or an array without fully specifying for each component
// so we inspect the default rangeComponent to see what values are in there

// in future, we could inspect the HumanFriendlySiteRangeSchema instead

const rangifyComponent = (rangeComponent: any, baselineComponent: any): any =>  {

    if (Array.isArray(baselineComponent)) {
        // this is a repeat component, rangify each instance in the baseline against the first in the rangeComponent
        return baselineComponent.map((subc: any) => rangifyComponent(rangeComponent[0], subc));
    } else {
        let newComp: any = {...rangeComponent};

        // singleton component
        Object.keys(baselineComponent).forEach(key => {
            if (!(key in rangeComponent)) {
                return;
            }
            const val = rangeComponent[key]
            if (typeof val === "object" && val !== null && "min" in rangeComponent[key]) {
                // This property is min/max/step in the SiteRange form
                // e.g. Battery capacity

                newComp[key] = {
                    "min": baselineComponent[key],
                    "max": baselineComponent[key],
                    "step": 0
                };
            } else if (Array.isArray(rangeComponent[key])) {
                // This property is an array of values in the SiteRange form
                // we want it to take the single baseline value, so wrap that in an array
                // e.g. Battery mode
                newComp[key] = [baselineComponent[key]];
            } else {
                // This property is a primitive value
                // e.g. incumbent/age/lifetime
                newComp[key] = baselineComponent[key];
            }
        })
        return newComp;
    }
}