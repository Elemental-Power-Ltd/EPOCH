#pragma once

#include <iostream>
#include <string>
#include <unordered_map>
#include <Eigen/Core>

#include <spdlog/spdlog.h>

using year_TS = Eigen::VectorXf;

class TaskData {

public:
    TaskData(
        float years_val = 1.0f, 
        float days_val = 365.0f, 
        float hours_val = 8760.0f, 
        float timestep_hours_val = 1.0f, 
        float timewindow_val = 8760.0f,
        float Fixed_load1_scalar_val = 1.0f, 
        float Fixed_load2_scalar_val = 3.0f, 
        float Flex_load_max_val = 50.0f, 
        float Mop_load_max_val = 300.0f,
        float ScalarRG1_val = 599.2f, 
        float ScalarRG2_val = 75.6f, 
        float ScalarRG3_val = 60.48f, 
        float ScalarRG4_val = 0.0f, 
        float ScalarHYield_val = 0.75f,
        int s7_EV_CP_number_val = 0, 
        int f22_EV_CP_number_val = 3,
        int r50_EV_CP_number_val = 0,
        int u150_EV_CP_number_val = 0,
        float EV_flex_val = 0.5f,
        float ScalarHL1_val = 1.0f, 
        float ASHP_HPower_val = 70.0f, 
        int ASHP_HSource_val = 1, 
        float ASHP_RadTemp_val = 70.0f, 
        float ASHP_HotTemp_val = 43.0f,
        float GridImport_val = 140.0f, 
        float GridExport_val = 100.0f, 
        float Import_headroom_val = 0.4f, 
        float Export_headroom_val = 0.0f, 
        float Min_power_factor_val = 0.95f,
        float ESS_charge_power_val = 300.0f,
        float ESS_discharge_power_val = 300.0f, 
        float ESS_capacity_val = 800.0f, 
        float ESS_start_SoC_val = 0.5f,
        int ESS_charge_mode_val = 1, 
        int ESS_discharge_mode_val = 1,
        float Export_kWh_price_val = 5.0f,
        float time_budget_min_val = 1.0f, 
        int target_max_concurrency_val = 44,
        float CAPEX_limit_val = 1000.0f, 
        float OPEX_limit_val = 20.0f, 
        int paramIndex_val = 0, 
        float cylinder_vol = 2500.0f
        ):
            years(years_val), 
            days(days_val), 
            hours(hours_val), 
            timestep_hours(timestep_hours_val), 
            timewindow(timewindow_val),
            Fixed_load1_scalar(Fixed_load1_scalar_val), 
            Fixed_load2_scalar(Fixed_load2_scalar_val), 
            Flex_load_max(Flex_load_max_val), 
            Mop_load_max(Mop_load_max_val),
            ScalarRG1(ScalarRG1_val), 
            ScalarRG2(ScalarRG2_val), 
            ScalarRG3(ScalarRG3_val), 
            ScalarRG4(ScalarRG4_val), 
            ScalarHYield(ScalarHYield_val),
            s7_EV_CP_number(s7_EV_CP_number_val), 
            f22_EV_CP_number(f22_EV_CP_number_val), 
            r50_EV_CP_number(r50_EV_CP_number_val), 
            u150_EV_CP_number(u150_EV_CP_number_val), 
            EV_flex(EV_flex_val),
            ScalarHL1(ScalarHL1_val), 
            ASHP_HPower(ASHP_HPower_val), 
            ASHP_HSource(ASHP_HSource_val), 
            ASHP_RadTemp(ASHP_RadTemp_val), 
            ASHP_HotTemp(ASHP_HotTemp_val),
            GridImport(GridImport_val), 
            GridExport(GridExport_val), 
            Import_headroom(Import_headroom_val), 
            Export_headroom(Export_headroom_val), 
            Min_power_factor(Min_power_factor_val),
            ESS_charge_power(ESS_charge_power_val), 
            ESS_discharge_power(ESS_discharge_power_val), 
            ESS_capacity(ESS_capacity_val), 
            ESS_start_SoC(ESS_start_SoC_val),
            ESS_charge_mode(ESS_charge_mode_val), 
            ESS_discharge_mode(ESS_discharge_mode_val),
            Export_kWh_price(Export_kWh_price_val),
            time_budget_min(time_budget_min_val), 
            target_max_concurrency(target_max_concurrency_val),
            CAPEX_limit(CAPEX_limit_val), 
            OPEX_limit(OPEX_limit_val), 
            DHW_cylinder_volume(cylinder_vol),
            paramIndex(paramIndex_val), 

        // initialize unordered maps to allow setting of member variables using (string) dictionary keys
        param_map_float(
            { 
                {"years",&years}, 
                {"days",&days }, 
                {"hours",&hours }, 
                {"timestep_hours",&timestep_hours }, 
                {"timewindow",&timewindow },
                {"Fixed_load1_scalar",&Fixed_load1_scalar }, 
                {"Fixed_load2_scalar",&Fixed_load2_scalar }, 
                {"Flex_load_max",&Flex_load_max }, 
                {"Mop_load_max",&Mop_load_max },
                {"ScalarRG1",&ScalarRG1 }, 
                {"ScalarRG2",&ScalarRG2 }, 
                {"ScalarRG3",&ScalarRG3 }, 
                {"ScalarRG4",&ScalarRG4 } , 
                {"ScalarHYield",&ScalarHYield },
                {"EV_flex",&EV_flex },
                {"ScalarHL1",&ScalarHL1 }, 
                {"ASHP_HPower", &ASHP_HPower }, 
                {"ASHP_RadTemp", &ASHP_RadTemp }, 
                {"ASHP_HotTemp", &ASHP_HotTemp },
                {"GridImport",&GridImport }, 
                {"GridExport",&GridExport }, 
                {"Import_headroom",&Import_headroom }, 
                {"Export_headroom",&Export_headroom }, 
                {"Min_power_factor",&Min_power_factor},
                {"ESS_charge_power",&ESS_charge_power }, 
                {"ESS_discharge_power",&ESS_discharge_power }, 
                {"ESS_capacity",&ESS_capacity},
                {"ESS_start_SoC",&ESS_start_SoC},
                {"Export_kWh_price",&Export_kWh_price }, 
                {"time_budget_min",&time_budget_min }, 
                {"CAPEX_limit",&CAPEX_limit }, 
                {"OPEX_limit",&OPEX_limit }, 
                {"DHW_cylinder_volume", &DHW_cylinder_volume}
            }),
        param_map_int({ { "s7_EV_CP_number",&s7_EV_CP_number }, { "f22_EV_CP_number",&f22_EV_CP_number }, { "r50_EV_CP_number",&r50_EV_CP_number }, { "u150_EV_CP_number",&u150_EV_CP_number},
            { "ASHP_HSource", &ASHP_HSource },
            {"ESS_charge_mode",&ESS_charge_mode}, {"ESS_discharge_mode",&ESS_discharge_mode}, {"target_max_concurrency",&target_max_concurrency } })
    {}
    
    int calculate_timesteps() const {
        // number of hours is a float in case we need sub-hourly timewindows
        float float_timestep = timewindow / timestep_hours;
        int int_timestep = static_cast<int>(float_timestep);
        return int_timestep;
    }

    // Setter functions to set the value of data members
    bool set_param_float(const std::string& key, float value) {
        // insert type checking to ensure that the two int parameters are not set using a float?
        auto it = param_map_float.find(key);
        if (it != param_map_float.end()) {
            *(it->second) = value;
            return true;
        }
        else {
            spdlog::warn("Parameter {} not found!", key);
        }
        return false;
    }

    bool set_param_int(const std::string& key, int value) {
        // insert type checking to ensure that the non-int parameters are not set using an int?
        auto it = param_map_int.find(key);
        if (it != param_map_int.end()) {
            *(it->second) = value;
            return true;
        }
        else {
            spdlog::warn("Parameter {} not found!", key);
        }
        return false;
    }

    void print_param_float(const std::string& key) {
        auto it = param_map_float.find(key);
        std::cout << "Parameter " << key << " = " << *(it->second) << std::endl;
    }
    void print_param_int(const std::string& key) {
        auto it = param_map_int.find(key);
        std::cout << "Parameter " << key << " = " << *(it->second) << std::endl;
    }

    float years;
    float days;
    float hours;
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
    float ScalarHYield;
    int s7_EV_CP_number;
    int f22_EV_CP_number;
    int r50_EV_CP_number;
    int u150_EV_CP_number;
    float EV_flex;
    float ScalarHL1;
    float ASHP_HPower;
    int ASHP_HSource;
    float ASHP_RadTemp;
    float ASHP_HotTemp;
    float GridImport;
    float GridExport;
    float Import_headroom;
    float Export_headroom;
    float Min_power_factor;
    float ESS_charge_power;
    float ESS_discharge_power;
    float ESS_capacity;
    float ESS_start_SoC;
    int ESS_charge_mode;
    int ESS_discharge_mode;
    float Export_kWh_price;
    float time_budget_min;
    int target_max_concurrency;
    float CAPEX_limit;
    float OPEX_limit;
    float DHW_cylinder_volume;

    uint64_t paramIndex;

    std::unordered_map<std::string, float*> param_map_float;
    std::unordered_map<std::string, int*> param_map_int;


};
