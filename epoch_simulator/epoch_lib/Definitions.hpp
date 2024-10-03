#pragma once

#include <Eigen/Core>
#include <functional>
#include <string>

#include "Simulation/TaskData.hpp"

// Elemental Power definitions

const std::string EPOCH_VERSION = "0.2.2";

using year_TS = Eigen::VectorXf;

struct SimulationResult {
	float runtime;
	uint64_t paramIndex;

	float total_annualised_cost;
	float project_CAPEX;
	float scenario_cost_balance;
	float payback_horizon_years;
	float scenario_carbon_balance;
};

struct FullSimulationResult {
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

	float runtime;
	uint64_t paramIndex;

	float total_annualised_cost;
	float project_CAPEX;
	float scenario_cost_balance;
	float payback_horizon_years;
	float scenario_carbon_balance;

	float Baseline_electricity_cost;
	float Baseline_fuel_cost;

	float Baseline_electricity_carbon;
	float Baseline_fuel_carbon;

	float Scenario_electricity_cost;
	float Scenario_fuel_cost;
	float Scenario_grid_export_cost;
	float Resulting_EV_charge_revenue;
	float Resulting_Data_Centre_revenue;
	float Scenario_avoided_fuel_cost;

	float Scenario_electricity_carbon;
	float Scenario_fuel_carbon;
	float Scenario_grid_export_carbon;
	float Scenario_avoided_fuel_carbon;

	float ESS_PCS_CAPEX;
	float ESS_PCS_OPEX;
	float ESS_ENCLOSURE_CAPEX;
	float ESS_ENCLOSURE_OPEX;
	float ESS_ENCLOSURE_DISPOSAL;

	float PVpanel_CAPEX;
	float PVBoP_CAPEX;
	float PVroof_CAPEX;
	float PVground_CAPEX;
	float PV_OPEX;

	float EV_CP_cost;
	float EV_CP_install;

	float Grid_CAPEX;

	float ASHP_CAPEX;
};

// A struct containing all of the necessary vectors for cost calculations
// bridging from V7 to V8
struct CostVectors {
	year_TS actual_ev_load_e;
	year_TS actual_data_centre_load_e;
	year_TS building_load_e;

	year_TS heatload_h;
	year_TS heat_shortfall_h;

	year_TS grid_import_e;
	year_TS grid_export_e;
	year_TS actual_low_priority_load_e;
};


// Contains the five objectives and the TaskData that was used to produce the result
struct ObjectiveResult {
	float total_annualised_cost;
	float project_CAPEX;
	float scenario_cost_balance;
	float payback_horizon_years;
	float scenario_carbon_balance;

	TaskData taskData;
};

inline ObjectiveResult toObjectiveResult(const SimulationResult& simResult, const TaskData& taskData) noexcept {
	return ObjectiveResult {
		simResult.total_annualised_cost,
		simResult.project_CAPEX,
		simResult.scenario_cost_balance,
		simResult.payback_horizon_years,
		simResult.scenario_carbon_balance,
		taskData
	};
}


struct OutputValues {
	float maxVal;
	float minVal;
	float meanVal;
	float time_taken;
	float Fixed_load1_scalar; float Fixed_load2_scalar; float Flex_load_max; float Mop_load_max;
	float ScalarRG1; float ScalarRG2; float ScalarRG3; float ScalarRG4; float ScalarHYield;
	int s7_EV_CP_number; int f22_EV_CP_number; int r50_EV_CP_number; int u150_EV_CP_number; float EV_flex;
	float ScalarHL1; float ASHP_HPower; int ASHP_HSource; float ASHP_RadTemp; float ASHP_HotTemp;
	float GridImport; float GridExport; float Import_headroom; float Export_headroom; float Min_power_factor;
	float ESS_charge_power; float ESS_discharge_power; float ESS_capacity;  float ESS_start_SoC;
	int ESS_charge_mode; int ESS_discharge_mode; float DHW_cylinder_volume;
	float Export_kWh_price;
	float CAPEX; float annualised; float scenario_cost_balance; float payback_horizon; float scenario_carbon_balance;
	uint64_t CAPEX_index; uint64_t annualised_index; uint64_t scenario_cost_balance_index; uint64_t payback_horizon_index; uint64_t scenario_carbon_balance_index;
	uint64_t scenario_index;
	uint64_t num_scenarios; float est_hours; float est_seconds;
};


struct InputValues {
	float timestep_hours; float timewindow;
	float Fixed_load1_scalar_lower; float Fixed_load1_scalar_upper; float Fixed_load1_scalar_step;
	float Fixed_load2_scalar_lower; float Fixed_load2_scalar_upper; float Fixed_load2_scalar_step;
	float Flex_load_max_lower; float Flex_load_max_upper; float Flex_load_max_step;
	float Mop_load_max_lower; float Mop_load_max_upper; float Mop_load_max_step;
	float ScalarRG1_lower; float ScalarRG1_upper; float ScalarRG1_step;
	float ScalarRG2_lower; float ScalarRG2_upper; float ScalarRG2_step;
	float ScalarRG3_lower; float ScalarRG3_upper; float ScalarRG3_step;
	float ScalarRG4_lower; float ScalarRG4_upper; float ScalarRG4_step;
	float ScalarHYield_lower; float ScalarHYield_upper; float ScalarHYield_step;
	int s7_EV_CP_number_lower; int s7_EV_CP_number_upper; int s7_EV_CP_number_step;
	int f22_EV_CP_number_lower; int f22_EV_CP_number_upper; int f22_EV_CP_number_step;
	int r50_EV_CP_number_lower; int r50_EV_CP_number_upper; int r50_EV_CP_number_step;
	int u150_EV_CP_number_lower; int u150_EV_CP_number_upper; int u150_EV_CP_number_step;
	float EV_flex_lower; float EV_flex_upper; float EV_flex_step;
	float ScalarHL1_lower; float ScalarHL1_upper; float ScalarHL1_step;
	float ASHP_HPower_lower; float ASHP_HPower_upper; float ASHP_HPower_step;
	int ASHP_HSource_lower; int ASHP_HSource_upper; int ASHP_HSource_step;
	float ASHP_RadTemp_lower; float ASHP_RadTemp_upper; float ASHP_RadTemp_step;
	float ASHP_HotTemp_lower; float ASHP_HotTemp_upper; float ASHP_HotTemp_step;
	float GridImport_lower; float GridImport_upper; float GridImport_step;
	float GridExport_lower; float GridExport_upper; float GridExport_step;
	float Import_headroom_lower; float Import_headroom_upper; float Import_headroom_step;
	float Export_headroom_lower; float Export_headroom_upper; float Export_headroom_step;
	float Min_power_factor_lower; float Min_power_factor_upper; float Min_power_factor_step;
	float ESS_charge_power_lower; float ESS_charge_power_upper; float ESS_charge_power_step;
	float ESS_discharge_power_lower; float ESS_discharge_power_upper; float ESS_discharge_power_step;
	float ESS_capacity_lower; float ESS_capacity_upper; float ESS_capacity_step;
	float ESS_start_SoC_lower; float ESS_start_SoC_upper; float ESS_start_SoC_step;
	int ESS_charge_mode_lower; int ESS_charge_mode_upper;
	int ESS_discharge_mode_lower; int ESS_discharge_mode_upper;
	float DHW_cylinder_volume_lower; float DHW_cylinder_volume_upper; float DHW_cylinder_volume_step;
	float Export_kWh_price;
	float time_budget_min; int target_max_concurrency;
	float CAPEX_limit; float OPEX_limit;
};

struct HistoricalData {
	year_TS hotel_eload_data;
	year_TS ev_eload_data;
	year_TS heatload_data;
	year_TS RGen_data_1;
	year_TS RGen_data_2;
	year_TS RGen_data_3;
	year_TS RGen_data_4;
	year_TS airtemp_data;
	year_TS importtariff_data;
	year_TS gridCO2_data;
	year_TS DHWdemand_data;
	Eigen::MatrixXf ASHPinputtable;
	Eigen::MatrixXf ASHPoutputtable;
};


// Define a struct that represents the mapping between member names and pointers
struct MemberMapping {
	const char* name;
	std::function<float(const InputValues&)> getFloat;
	std::function<int(const InputValues&)> getInt;
};


struct OutMemberMapping {
	const char* name;
	std::function<float(const OutputValues&)> getFloat;
	std::function<int(const OutputValues&)> getInt;
};

enum class Objective { CAPEX, AnnualisedCost, PaybackHorizon, CostBalance, CarbonBalance };