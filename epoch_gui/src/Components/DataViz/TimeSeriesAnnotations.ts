import {EpochSiteData, NonNullReportDataType} from "../../Models/Endpoints";


type Units = "kWh" | "Deg (c)" | "£/KwH" | "gCO₂/kWh"

interface Annotation {
    // The human-readable name for this time series
    name: string;
    // The units of this timeseries (as a string
    units: Units;
    // whether this is an input to EPOCH or an output from it
    type: "Input" | "Output"
}

type AnnotationMap = {[key: string]: Annotation};

// This map contains annotations for timeseries we expect to find in ReportData and SiteData
const staticAnnotationsMap: AnnotationMap = {
    // Output (fields in ReportData)
    "Grid_Import": {name: "Grid Import", units: "kWh", type: "Output"},
    "PVdcGen": {name: "Solar Generation (DC)", units: "kWh", type: "Output"},
    "PVacGen": {name: "Solar Generation (AC)", units: "kWh", type: "Output"},
    "ESS_discharge": {name: "ESS Discharge", units: "kWh", type: "Output"},
    "ESS_RTL": {name: "ESS Round-trip-loss", units: "kWh", type: "Output"},
    "ESS_AuxLoad": {name: "ESS Auxiliary Load", units: "kWh", type: "Output"},
    "Hotel_load": {name: "Building Load", units: "kWh", type: "Output"},
    "EV_targetload": {name: "EV Target Load", units: "kWh", type: "Output"},
    "EV_actualload": {name: "EV Actual Load", units: "kWh", type: "Output"},
    "Data_centre_target_load": {name: "Data Centre Target Load", units: "kWh", type: "Output"},
    "Data_centre_actual_load": {name: "Data Centre Actual Load", units: "kWh", type: "Output"},
    "ESS_charge": {name: "ESS Charge", units: "kWh", type: "Output"},
    "MOP_load": {name: "Mop Load", units: "kWh", type: "Output"},
    "Grid_Export": {name: "Grid Export", units: "kWh", type: "Output"},
    "Actual_curtailed_export": {name: "Actual Curtailed Export", units: "kWh", type: "Output"},
    "DHW_load": {name: "DHW Load", units: "kWh", type: "Output"},
    "ASHP_elec_load": {name: "ASHP Electrical Load", units: "kWh", type: "Output"},
    "ASHP_DHW_output": {name: "ASHP DHW Output", units: "kWh", type: "Output"},
    "ASHP_CH_output": {name: "ASHP CH Output", units: "kWh", type: "Output"},
    "ASHP_free_heat": {name: "ASHP Free Heat", units: "kWh", type: "Output"},
    "ASHP_used_hotroom_heat": {name: "ASHP Used Hotroom Heat", units: "kWh", type: "Output"},
    "Actual_import_shortfall": {name: "Import Shortfall", units: "kWh", type: "Output"},
    "DHW_Shortfall": {name: "DHW Shortfall", units: "kWh", type: "Output"},
    "DHW_SoC": {name: "DHW State of Charge", units: "kWh", type: "Output"},
    "DHW_Standby_loss": {name: "DHW Standby Loss", units: "kWh", type: "Output"},
    "DHW_ave_temperature": {name: "DHW Average Temperature", units: "Deg (c)", type: "Output"},
    "DHW_charging": {name: "DHW Charge", units: "kWh", type: "Output"},
    "ESS_resulting_SoC": {name: "ESS State of Charge", units: "kWh", type: "Output"},
    "Heat_surplus": {name: "Heat Surplus", units: "kWh", type: "Output"},
    "Heat_shortfall": {name: "Heat Shortfall", units: "kWh", type: "Output"},
    "Heatload": {name: "Heat Load", units: "kWh", type: "Output"},
    "GasCH_load": {name: "Gas CH Load", units: "kWh", type: "Output"},

    // Input (fields in SiteData)
    // note, we only include the singleton timeseries here
    // solar_yields, import_tariffs and fabric_interventions must be dynamically added at runtime
    "building_eload": {name: "Building Electrical Demand", units: "kWh", type: "Input"},
    "building_hload": {name: "Baseline Heat Demand", units: "kWh", type: "Input"},
    "ev_eload": {name: "EV Demand", units: "kWh", type: "Input"},
    "dhw_demand": {name: "DHW Demand", units: "kWh", type: "Input"},
    "air_temperature": {name: "Air Temperature", units: "Deg (c)", type: "Input"},
    "grid_co2": {name: "Grid Carbon Intensity", units: "gCO₂/kWh", type: "Input"},
}

// extended version of the Annotation array that also includes the timeseries data
interface AnnotationWithData extends Annotation {
    data: number[];
}

export type DataAnnotationMap = {[key: string]: AnnotationWithData};

export const getAnnotatedSeries = (taskData: any, siteData: EpochSiteData, reportData: NonNullReportDataType): DataAnnotationMap => {

    // Add the SiteData

    const annotatedSeries: DataAnnotationMap = {};

    // add the top-level timeseries
    annotatedSeries["building_eload"] = {...staticAnnotationsMap["building_eload"], data: siteData["building_eload"]}
    annotatedSeries["building_hload"] = {...staticAnnotationsMap["building_hload"], data: siteData["building_hload"]}
    annotatedSeries["ev_eload"] = {...staticAnnotationsMap["ev_eload"], data: siteData["ev_eload"]}
    annotatedSeries["dhw_demand"] = {...staticAnnotationsMap["dhw_demand"], data: siteData["dhw_demand"]}
    annotatedSeries["air_temperature"] = {...staticAnnotationsMap["air_temperature"], data: siteData["air_temperature"]}
    annotatedSeries["grid_co2"] = {...staticAnnotationsMap["grid_co2"], data: siteData["grid_co2"]}

    // add the solar yields from SiteData
    siteData.solar_yields.forEach((yieldSeries, idx) => {
        // a yield array is used if any of the SolarPanel entries have it as their yield_index
        const used = taskData.solar_panels.some((panel: any) => panel.yield_index === idx);

        // idx + 1: use 1-based indexing for display
        const name = used ? `Solar Yield ${idx + 1}` : `Solar Yield ${idx + 1} (unused)`;

        annotatedSeries[name] = {name: name, units: "kWh", type: "Input", data: yieldSeries}
    })

    // add the fabric interventions
    siteData.fabric_interventions.forEach((intervention, idx) => {
        // fabric_intervention_index is a 1-based index
        const used = idx + 1 === taskData.building?.fabric_intervention_index;
        const name = used ? `Reduced Heating Demand` : `Reduced Heating Demand ${idx + 1} (unused)`;

        annotatedSeries[name] = {name: name, units: "kWh", type: "Input", data: intervention.reduced_hload}
    })

    // add the import tariffs
    siteData.import_tariffs.forEach((tariff, idx) => {
        const used = idx === taskData.grid?.tariff_index;
        // idx + 1: use 1-based indexing for display
        const name = used ? `Import Tariff ${idx + 1}` : `Import Tariff ${idx + 1} (unused)`;

        annotatedSeries[name] = {name: name, units: "£/KwH", type: "Input", data: tariff}
    })

    // add the report data

    // we only want to add the report data of timeseries that exist for this scenario
    // assume building_eload has the correct length
    const requiredLength = siteData.building_eload.length;

    Object.keys(reportData).forEach((key) => {
        if (reportData[key].length === requiredLength) {
            if (key in staticAnnotationsMap) {
                annotatedSeries[key] = {...staticAnnotationsMap[key], data: reportData[key]}
            } else {
                console.error(`No timeseries annotation found for ${key}`);
            }
        }
    })

    return annotatedSeries;
}
