"""
This script contains some very simple logic to auto-generate bindings from struct definitions

It is not designed to be robust and should never be called automatically as part of a build process

"""


def make_report_data_bindings():
    # paste in the latest definition for ReportData in here and then re-run this function

    report_data_string = """
    struct ReportData {

    // TempSum
    year_TS Actual_import_shortfall;
    year_TS Actual_curtailed_export;
    year_TS Heat_shortfall;
    year_TS Heat_surplus;

    // Hotel
    year_TS Hotel_load;
    year_TS Heatload;

    // PV
    year_TS PVdcGen;
    year_TS PVacGen;

    // EV
    year_TS EV_targetload;
    year_TS EV_actualload;

    // ESS
    year_TS ESS_charge;
    year_TS ESS_discharge;
    year_TS ESS_resulting_SoC;
    year_TS ESS_AuxLoad;
    year_TS ESS_RTL;

    // DataCentre
    year_TS Data_centre_target_load;
    year_TS Data_centre_actual_load;
    year_TS Data_centre_target_heat;
    year_TS Data_centre_available_hot_heat;

    // Grid
    year_TS Grid_Import;
    year_TS Grid_Export;

    // MOP
    year_TS MOP_load;

    // GasCombustionHeater
    year_TS GasCH_load;
    
    // DHW
    year_TS DHW_load;
    year_TS DHW_charging;
    year_TS DHW_SoC;
    year_TS DHW_Standby_loss;
    year_TS DHW_ave_temperature;
    year_TS DHW_Shortfall;
    """
    
    for line in report_data_string.split("\n"):
        if "year_TS" in line:
            # remove 'year_TS ' and everything before it
            timeseries_name = line.split("year_TS ")[-1]
            
            # remove ';' and everything after it
            timeseries_name = timeseries_name.split(";")[0]
            
            print(f"\t\t.def_readonly(\"{timeseries_name}\", &ReportData::{timeseries_name})")
            
    

if __name__ == "__main__":
    make_report_data_bindings()
