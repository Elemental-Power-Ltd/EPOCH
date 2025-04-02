/**
 * This file contains hardcoded config options for the Data visualisation
 */
export const color_map = {
    'Actual_import_shortfall':      ' #960202', // Dark red (darker than in M-VEST)       or ' #6c757d', // *Dark grey
    'Actual_curtailed_export':      ' #87502d', // Light Brown (as in M-VEST)                   or ' #ced4da', // *Light grey
    'Grid_Import':                  ' #a4a6a5', // Grey (as in M-VEST)
    'Grid_Export':                  ' #a4a6a5', // Grey (as in M-VEST)
    'Hotel_load':                   ' #63d2f7', // Bright blue (as in M-VEST)
    'MOP_load':                     ' #81bf7a', // Green (as in M-VEST)
    'EV_targetload':                ' #0a6a8a', // Dark blue (as in M-VEST)
    'EV_actualload':                ' #0a6a8a', // Dark blue (as in M-VEST)
    'PVdcGen':                      ' #edd980', // Yellow (as in M-VEST)
    'PVacGen':                      ' #edd980', // Yellow (as in M-VEST)
    'ESS_charge':                   ' #6a51a3', // Purple (as in M-VEST)
    'ESS_discharge':                ' #6a51a3', // Purple (as in M-VEST)        -- or #7333a1
    'ESS_resulting_SoC':            ' #9e9ac8', // *Plum                        -- or #9467bd
    'ESS_AuxLoad':                  ' #cbc9e2', // Light purple (as in M-VEST)
    'ESS_RTL':                      ' #cbc9e2', // Light purple (as in M-VEST)  -- or #d0a3f0
    'Data_centre_target_load':      ' #aad7e6', // Sky blue (as in M-VEST)
    'Data_centre_actual_load':      ' #aad7e6', // Sky blue (as in M-VEST)
    'Data_centre_target_heat':      ' #3498db', // *Cornflower blue
    'Data_centre_available_hot_heat': ' #edd980', // Yellow ("Free heat" in M-VEST)
    'GasCH_load':                   ' #ff6347', // *Tomato red 
    'Heatload':                     ' #964B00', // Brown-red (as in M-VEST)
    'Heat_shortfall':               ' #ff0000', // Red (as in M-VEST)
    'Heat_surplus':                 ' #5a5b5b', // Dark grey (as in M-VEST)
    'DHW_charging':                 ' #f57200', // *Bright Orange (similar to DHW_load)
    'DHW_load':                     ' #f57200', // *Bright Orange (similar to GasCH_load)
    'DHW_Standby_loss':             ' #ffb347', // *Light orange (similar to DHW_load)
    'DHW_SoC':                      ' #fabc7e', // *Peach (similar to DHW charging/loss)
    'DHW_ave_temperature':          ' #b77b1a', // *Orange/brown (similar to DHW_Standby_loss)
    'DHW_Shortfall':                ' #cb6363', // *Pastel pink (contrast with DHW_load)
    'ASHP_elec_load':               ' #405f3d', // *Olive green (similar to MOP_load, implying energy usage)
    'ASHP_DHW_output':              ' #ffA500', // *Orange (similar to DHW_load, implying hot water output)
    'ASHP_CH_output':               ' #6a3601', // *Brown (similar to Heatload)
    'ASHP_free_heat':               ' #827902', // *Dark Yellow (similar to Data_centre_available_hot_heat)
    'ASHP_used_hotroom_heat':       ' #402c0f', // *Dark Brown (similar to Heatload, implying used heat)
}

// We group energy data into a number of distinct sets
// elec | heat
// draw | supply | surplus | shortfall
export const elec_supply_stackbars = ['Grid_Export', 'Hotel_load', 'MOP_load', 'EV_actualload',
    'ESS_charge', 'ESS_AuxLoad', 'Data_centre_actual_load', 'ASHP_elec_load']

export const heat_supply_stackbars = ['Heatload', 'DHW_charging', 'ASHP_used_hotroom_heat']

export const elec_draw_stackbars = ['Grid_Import','PVacGen','ESS_discharge', 'ESS_RTL']

export const heat_draw_stackbars = ['GasCH_load', 'Data_centre_available_hot_heat', 'DHW_load', 'DHW_Standby_loss',
    'ASHP_DHW_output', 'ASHP_CH_output']

export const elec_shortfall_stackbars = ['Actual_import_shortfall'];
export const heat_shortfall_stackbars = ['Heat_shortfall', 'DHW_Shortfall'];

export const elec_surplus_stackbars = ['Actual_curtailed_export'];
export const heat_surplus_stackbars = ['Heat_surplus'];

// we can then assemble these sets into various combinations for the different things we want to plot

export const all_shortfall_stackbars = [...elec_shortfall_stackbars, ...heat_shortfall_stackbars];
export const all_surplus_stackbars = [...elec_surplus_stackbars, ...heat_surplus_stackbars];
// flagged stackbars are ones that we want to highlight in the gui (because they represent potential issues)
export const all_flagged_stackbars = [...all_shortfall_stackbars, ...all_surplus_stackbars];

// mark the stackbars on whether we need them above or below 0
export const all_positive_stackbars = [...elec_supply_stackbars, ...heat_supply_stackbars, ...all_surplus_stackbars];
export const all_negative_stackbars = [...elec_draw_stackbars, ...heat_draw_stackbars, ...all_shortfall_stackbars];

export const all_energy_stackbars = [...all_positive_stackbars, ...all_negative_stackbars];


export type StackbarOption = "all" | "elec" | "heat";

// Dropdown options for bar chart variables to plot
export const stackbarGroups: {value: StackbarOption, label: string}[] = [
        { value: 'all', label: 'Show all' },
        { value: 'elec', label: 'Electricity variables only' },
        { value: 'heat', label: 'Heat variables only' },
];

// Dropdown options for number of days to keep
export const daysOptions = [
    { value: 1, label: "1 Day" },
    { value: 2, label: "2 Days" },
    { value: 7, label: "7 Days" },
    { value: 30, label: "30 Days" },
    { value: 90, label: "90 Days" },
    { value: 365, label: "1 Year" }
];

// the default variables for each line plot
export const lineChartDefaults = [
    {var1: 'DHW_load', var2: 'DHW_charging'},
    {var1: 'DHW_SoC', var2: 'DHW_charging'},
    {var1: 'PVacGen', var2: 'Grid_Import'},
    {var1: 'Hotel_load', var2: 'ESS_discharge'}
]
