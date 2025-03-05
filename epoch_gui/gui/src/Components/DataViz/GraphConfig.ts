/**
 * This file contains hardcoded config options for the Data visualisation
 */

export const color_map = {
    'Actual_import_shortfall':      ' #c6c6c6', // Light Grey          
    'Actual_curtailed_export':      ' #c6c6c6', // Light Grey          
    'Grid_Import':                  ' #636363', // Grey
    'Grid_Export':                  ' #636363', // Grey
    'Hotel_load':                   ' #00b6f3',  // Bright blue -- 'Hotel'
    'MOP_load':                     ' #19cca8',  // Blue / Green (blue for elec load)
    'EV_targetload':                ' #0a6a8a',  // Dark blue -- '6 EV-h 3x22kW'
    'EV_actualload':                ' #0a6a8a',  // Dark blue -- '6 EV-h 3x22kW'
    'PVdcGen':                      ' #81bf7a',  // Green
    'PVacGen':                      ' #81bf7a',  // Green
    'ESS_charge':                   ' #7333a1',  // Purple -- 'ESSchrg'
    'ESS_discharge':                ' #7333a1',  // Purple -- 'ESSdisch'
    'ESS_resulting_SoC':            'rgb(148, 24, 156)',  // Dark pink/purple
    'ESS_AuxLoad':                  ' #d0a3f0',  // Light purple -- 'ESSLoss'
    'ESS_RTL':                      ' #d0a3f0',  // Light purple -- 'ESSLoss'
    'Data_centre_target_load':      ' #aad7e6',  // Sky blue -- 'Datacentre'
    'Data_centre_actual_load':      ' #aad7e6',  // Sky blue -- 'Datacentre'
    'Data_centre_target_heat':      ' #6c0101',    // Dark red
    'Data_centre_available_hot_heat': ' #6c0101',  // Dark red
    'GasCH_load':                   ' #ff0000 ', // Red
    'Heatload':                     ' #ff0000',  // Red
    'Heat_shortfall':               ' #fb9a99',  // Pink
    'Heat_surplus':                 ' #fb9a99',  // Pink
    'DHW_load':                     ' #ffA500', // Orange 'DHW load' (and tank discharge)
    'DHW_charging':                 ' #ffA500', // Orange
    'DHW_SoC':                      ' #aa8c04', // yellow
    'DHW_Standby_loss':             ' #aa8c04', // yellow (make dark?)
    'DHW_ave_temperature':          ' #cd6300', // Dark orange
    'DHW_Shortfall':                ' #d8995d', // faded orange
     // ASHP data
    'ASHP_elec_load':               '#9FC131',
    'ASHP_DHW_output':              '#DBF227',
    'ASHP_CH_output':               '#D6D58E',
    'ASHP_free_heat':               '#005C53',
    'ASHP_used_hotroom_heat':       '#042940',
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

// the default variables for each line plot
export const lineChartDefaults = [
    {var1: 'DHW_load', var2: 'DHW_charging'},
    {var1: 'DHW_SoC', var2: 'DHW_charging'},
    {var1: 'PVacGen', var2: 'Grid_Import'},
    {var1: 'Hotel_load', var2: 'ESS_discharge'}
]
