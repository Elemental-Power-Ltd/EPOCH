#pragma once

#include <Eigen/Core>
#include <functional>
#include <optional>
#include <string>

#include "Simulation/TaskData.hpp"

// Elemental Power definitions

const std::string EPOCH_VERSION = "1.1.0";

using year_TS = Eigen::VectorXf;

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
};

struct SimulationResult {
	float runtime;

	float total_annualised_cost;
	float project_CAPEX;
	float scenario_cost_balance;
	float payback_horizon_years;
	float scenario_carbon_balance_scope_1;
	float scenario_carbon_balance_scope_2;

	std::optional<ReportData> report_data;
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
	year_TS grid_export_prices;
};


// Contains the five objectives and the TaskData that was used to produce the result
struct ObjectiveResult {
	float total_annualised_cost;
	float project_CAPEX;
	float scenario_cost_balance;
	float payback_horizon_years;
	float scenario_carbon_balance_scope_1;
	float scenario_carbon_balance_scope_2;

	TaskData taskData;
};

inline ObjectiveResult toObjectiveResult(const SimulationResult& simResult, const TaskData& taskData) noexcept {
	return ObjectiveResult {
		simResult.total_annualised_cost,
		simResult.project_CAPEX,
		simResult.scenario_cost_balance,
		simResult.payback_horizon_years,
		simResult.scenario_carbon_balance_scope_1,
		simResult.scenario_carbon_balance_scope_2,
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


struct OutMemberMapping {
	const char* name;
	std::function<float(const OutputValues&)> getFloat;
	std::function<int(const OutputValues&)> getInt;
};

enum class Objective { CAPEX, AnnualisedCost, PaybackHorizon, CostBalance, CarbonBalance };