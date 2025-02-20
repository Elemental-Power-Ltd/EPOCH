/**
 * This file contains hardcoded config options for the Data visualisation
 */


export const color_map = {
    'Grid_Import': '#a4a6a5', // Grey -- 'GridImp'
    'PVdcGen': '#edd980',  // Yellow -- 'RGenSelf'
    'PVacGen': '#edd980',  // Yellow -- 'RGenSelf'
    'ESS_discharge': '#7333a1',  // Purple -- 'ESSdisch'
    'ESS_RTL': '#d0a3f0',  // Light purple -- 'ESSLoss'
    'ESS_AuxLoad': '#d0a3f0',  // Light purple -- 'ESSLoss'
    'Hotel_load': '#63d2f7',  // Bright blue -- 'Hotel'
    'EV_targetload': '#0a6a8a',  // Dark blue -- '6 EV-h 3x22kW'
    'EV_actualload': '#0a6a8a',  // Dark blue -- '6 EV-h 3x22kW'
    'Data_centre_target_load': '#aad7e6',  // Sky blue -- 'Datacentre'
    'Data_centre_actual_load': '#aad7e6',  // Sky blue -- 'Datacentre'
    'ESS_charge': '#7333a1',  // Purple -- 'ESSchrg'
    'MOP_load': '#81bf7a',  // Green -- 'Pool or U-Poly'
    'Grid_Export': '#a4a6a5', // Grey -- 'GridImp'
    'Actual_curtailed_export': '#ff0000', // Red 'Curtailed Export'
    'DHW_load': '#ffA500', // Orange 'DHW load' (and tank discharge)

    // ASHP data
    'ASHP_elec_load': '#9FC131',
    'ASHP_DHW_output': '#DBF227',
    'ASHP_CH_output': '#D6D58E',
    'ASHP_free_heat': '#005C53',
    'ASHP_used_hotroom_heat': '#042940',
}

export const default_positive_stackbars = ['ESS_RTL', 'ESS_AuxLoad', 'Hotel_load', 'EV_actualload', 'Data_centre_actual_load',
    'ESS_charge', 'MOP_load', 'Grid_Export', 'Actual_curtailed_export', 'DHW_load', 'DHW_charging', 'ASHP_elec_load',]

export const default_negative_stackbars = ['Grid_Import','PVacGen','ESS_discharge']

// Dropdown options for number of days to keep
export const daysOptions = [
    { value: 1, label: "1 Day" },
    { value: 2, label: "2 Days" },
    { value: 7, label: "7 Days" },
    { value: 30, label: "30 Days" },
];