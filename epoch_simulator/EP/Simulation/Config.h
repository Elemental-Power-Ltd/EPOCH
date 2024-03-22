#pragma once

#include <iostream>
#include <string>
#include <unordered_map>

#include <spdlog/spdlog.h>

class Config {

public:
    Config(float years_val = 1.0f, float days_val = 365.0f, float hours_val = 8760.0f, float timestep_minutes_val = 60.0f, float timestep_hours_val = 1.0f, float timewindow_val = 8760.0f,
        float Fixed_load1_scalar_val = 1.0f, float Fixed_load2_scalar_val = 6.0f, float Flex_load_max_val = 100.0f, float Mop_load_max_val = 200.0f,
        float ScalarRG1_val = 599.2f, float ScalarRG2_val = 75.6f, float ScalarRG3_val = 60.48f, float ScalarRG4_val = 0.00f,
        float ScalarHL1_val = 1.0f, float ScalarHYield1_val = 0.0f, float ScalarHYield2_val = 0.0f, float ScalarHYield3_val = 0.75f, float ScalarHYield4_val = 0.0f,
        float GridImport_val = 98.29f, float GridExport_val = 95.0f, float Import_headroom_val = 0.2f, float Export_headroom_val = 0.2f,
        float ESS_charge_power_val = 300.0f, float ESS_discharge_power_val = 300.0f, float ESS_capacity_val = 900.0f, float ESS_RTE_val = 0.86f, float ESS_aux_load_val = 0.75f, float ESS_start_SoC_val = 0.5f,
        int ESS_charge_mode_val = 1, int ESS_discharge_mode_val = 1,
        float import_kWh_price_val = 5.0f, float export_kWh_price_val = 30.0f,
        float time_budget_min_val = 1.0f, int target_max_concurrency_val = 44,
        float CAPEX_limit_val = 500.0f, float OPEX_limit_val = 20.0f, int paramIndex_val = 0)
        : years(years_val), days(days_val), hours(hours_val), timestep_minutes(timestep_minutes_val), timestep_hours(timestep_hours_val), timewindow(timewindow_val), 
        Fixed_load1_scalar(Fixed_load1_scalar_val), Fixed_load2_scalar(Fixed_load2_scalar_val), Flex_load_max(Flex_load_max_val), Mop_load_max(Mop_load_max_val),
        ScalarRG1(ScalarRG1_val), ScalarRG2(ScalarRG2_val), ScalarRG3(ScalarRG3_val), ScalarRG4(ScalarRG4_val),
        ScalarHL1(ScalarHL1_val), ScalarHYield1(ScalarHYield1_val), ScalarHYield2(ScalarHYield2_val), ScalarHYield3(ScalarHYield3_val), ScalarHYield4(ScalarHYield4_val),
        GridImport(GridImport_val), GridExport(GridExport_val), Import_headroom(Import_headroom_val), Export_headroom(Export_headroom_val), 
        ESS_charge_power(ESS_charge_power_val), ESS_discharge_power(ESS_discharge_power_val), ESS_capacity(ESS_capacity_val), ESS_RTE(ESS_RTE_val), ESS_aux_load(ESS_aux_load_val), ESS_start_SoC(ESS_start_SoC_val),
        ESS_charge_mode(ESS_charge_mode_val), ESS_discharge_mode(ESS_discharge_mode_val),
        Import_kWh_price(import_kWh_price_val), Export_kWh_price(export_kWh_price_val),
        time_budget_min(time_budget_min_val), target_max_concurrency(target_max_concurrency_val),
        CAPEX_limit(CAPEX_limit_val), OPEX_limit(OPEX_limit_val), paramIndex(paramIndex_val),
        // initialize unordered maps to allow setting of member variables using (string) dictionary keys
        param_map_float({ {"years",&years}, { "days",&days }, { "hours",&hours }, { "timestep_minutes",&timestep_minutes }, { "timestep_hours",&timestep_hours }, { "timewindow",&timewindow },
            { "Fixed_load1_scalar",&Fixed_load1_scalar }, { "Fixed_load2_scalar",&Fixed_load2_scalar }, { "Flex_load_max",&Flex_load_max }, { "Mop_load_max",&Mop_load_max },
            { "ScalarRG1",&ScalarRG1 }, { "ScalarRG2",&ScalarRG2 }, { "ScalarRG3",&ScalarRG3 }, { "ScalarRG4",&ScalarRG4 },
            { "ScalarHL1",&ScalarHL1 }, { "ScalarHYield1",&ScalarHYield1 }, { "ScalarHYield2",&ScalarHYield2 }, { "ScalarHYield3",&ScalarHYield3 }, { "ScalarHYield4",&ScalarHYield4 },
            { "GridImport",&GridImport }, { "GridExport",&GridExport }, { "Import_headroom",&Import_headroom }, { "Export_headroom",&Export_headroom },
            { "ESS_charge_power",&ESS_charge_power }, { "ESS_discharge_power",&ESS_discharge_power }, {"ESS_capacity",&ESS_capacity}, {"ESS_RTE",&ESS_RTE}, {"ESS_aux_load",&ESS_aux_load}, {"ESS_start_SoC",&ESS_start_SoC},
            { "import_kWh_price",&Import_kWh_price }, { "export_kWh_price",&Export_kWh_price }, { "time_budget_min",&time_budget_min }, { "CAPEX_limit",&CAPEX_limit }, { "OPEX_limit",&OPEX_limit }}),
        param_map_int({ {"ESS_charge_mode",&ESS_charge_mode}, {"ESS_discharge_mode",&ESS_discharge_mode}, {"target_max_concurrency",&target_max_concurrency }})
        {}
    
    int calculate_timesteps() const {
        // number of hours is a float in case we need sub-hourly timewindows
        float float_timestep = timewindow / timestep_hours;
        int int_timestep = static_cast<int>(float_timestep);
        return int_timestep;
    }

    // Setter functions to set the value of data members
    void set_param_float(const std::string& key, float value) {
        // insert type checking to ensure that the two int parameters are not set using a float?
        auto it = param_map_float.find(key);
        if (it != param_map_float.end()) {
            *(it->second) = value;
        }
        else {
            spdlog::warn("Parameter {} not found!", key);
        }
    }

    void set_param_int(const std::string& key, int value) {
        // insert type checking to ensure that the non-int parameters are not set using an int?
        auto it = param_map_int.find(key);
        if (it != param_map_int.end()) {
            *(it->second) = value;
        }
        else {
            if (key != "Parameter index") {
                spdlog::warn("Parameter {} not found!", key);
            }
        }
    }

    void print_param_float(const std::string& key) {
        auto it = param_map_float.find(key);
        std::cout << "Parameter " << key << " = " << *(it->second) << std::endl;
    }
    void print_param_int(const std::string& key) {
        auto it = param_map_int.find(key);
        std::cout << "Parameter " << key << " = " << *(it->second) << std::endl;
    }

    std::unordered_map<std::string, float*> param_map_float;
    std::unordered_map<std::string, int*> param_map_int;

    float years;
    float days;
    float hours;
    float timestep_minutes;
    float timestep_hours;
    float timewindow;
    float Fixed_load1_scalar;
    float Fixed_load2_scalar;
    float Flex_load_max;
    float Mop_load_max;
    float ScalarRG1;
    float ScalarRG2;
    float ScalarRG3;
    float ScalarRG4;
    float ScalarHL1;
    float ScalarHYield1;
    float ScalarHYield2;
    float ScalarHYield3;
    float ScalarHYield4;
    float GridImport;
    float GridExport;
    float Import_headroom;
    float Export_headroom;
    float ESS_charge_power;
    float ESS_discharge_power;
    float ESS_capacity;
    float ESS_RTE;
    float ESS_aux_load;
    float ESS_start_SoC;
    int   ESS_charge_mode;
    int   ESS_discharge_mode;
    float Import_kWh_price; 
    float Export_kWh_price;
    float time_budget_min;
    int target_max_concurrency;
    float CAPEX_limit;
    float OPEX_limit;

    uint64_t paramIndex;
};
