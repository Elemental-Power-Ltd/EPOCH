#pragma once

#include <functional>
#include <string>
#include <vector>

// Elemental Power definitions


using CustomDataTable = std::vector<std::pair<std::string, std::vector<float>>>;

struct SimulationResult {
	float Rgen_total;
	float Total_load;
	float ESUM;
	float ESS_available_discharge_power;
	float ESS_available_charge_power;
	float TS_ESS_Rgen_only_charge;
	float TS_ESS_discharge;
	float TS_ESS_charge;
	float TS_ESS_resulting_SoC;
	float TS_Pre_grid_balance;
	float TS_Grid_Import;
	float TS_Grid_Export;
	float TS_Post_grid_balance;
	float TS_Pre_flex_import_shortfall;
	float TS_Pre_Mop_curtailed_export;
	float TS_Actual_import_shortfall;
	float TS_Actual_curtailed_export;
	float TS_Actual_high_priority_load;
	float TS_Actual_low_priority_load;
	float heatload;
	float scaled_heatload;
	float Electrical_load_scaled_heat_yield;
	float TS_Heat_shortfall;
	float TS_Heat_surplus;
	float runtime;
	float paramIndex;
	float total_annualised_cost;
	float TS_project_CAPEX;
	float TS_scenario_cost_balance;
	float TS_payback_horizon_years;
	float TS_scenario_carbon_balance;
};


struct OutputValues {
	float maxVal;
	float minVal;
	float meanVal;
	float time_taken;
	float Fixed_load1_scalar; float Fixed_load2_scalar; float Flex_load_max; float Mop_load_max;
	float ScalarRG1; float ScalarRG2; float ScalarRG3; float ScalarRG4;
	float ScalarHL1; float ScalarHYield1; float ScalarHYield2; float ScalarHYield3; float ScalarHYield4;
	float GridImport; float GridExport; float Import_headroom; float Export_headroom;
	float ESS_charge_power; float ESS_discharge_power; float ESS_capacity; float ESS_RTE; float ESS_aux_load; float ESS_start_SoC;
	int ESS_charge_mode; int ESS_discharge_mode;
	float import_kWh_price; float export_kWh_price;
	float CAPEX; float annualised; float scenario_cost_balance; float payback_horizon; float scenario_carbon_balance;
	int CAPEX_index; int annualised_index; int scenario_cost_balance_index; int payback_horizon_index; int scenario_carbon_balance_index;
	int scenario_index;
	int num_scenarios; float est_hours; float est_seconds;
};



struct InputValues {
	float timestep_minutes; float timestep_hours; float timewindow;
	float Fixed_load1_scalar_lower; float Fixed_load1_scalar_upper; float Fixed_load1_scalar_step;
	float Fixed_load2_scalar_lower; float Fixed_load2_scalar_upper; float Fixed_load2_scalar_step;
	float Flex_load_max_lower; float Flex_load_max_upper; float Flex_load_max_step;
	float Mop_load_max_lower; float Mop_load_max_upper; float Mop_load_max_step;
	float ScalarRG1_lower; float ScalarRG1_upper; float ScalarRG1_step;
	float ScalarRG2_lower; float ScalarRG2_upper; float ScalarRG2_step;
	float ScalarRG3_lower; float ScalarRG3_upper; float ScalarRG3_step;
	float ScalarRG4_lower; float ScalarRG4_upper; float ScalarRG4_step;
	float ScalarHL1_lower; float ScalarHL1_upper; float ScalarHL1_step;
	float ScalarHYield1_lower; float ScalarHYield1_upper; float ScalarHYield1_step;
	float ScalarHYield2_lower; float ScalarHYield2_upper; float ScalarHYield2_step;
	float ScalarHYield3_lower; float ScalarHYield3_upper; float ScalarHYield3_step;
	float ScalarHYield4_lower; float ScalarHYield4_upper; float ScalarHYield4_step;
	float GridImport_lower; float GridImport_upper; float GridImport_step;
	float GridExport_lower; float GridExport_upper; float GridExport_step;
	float Import_headroom_lower; float Import_headroom_upper; float Import_headroom_step;
	float Export_headroom_lower; float Export_headroom_upper; float Export_headroom_step;
	float ESS_charge_power_lower; float ESS_charge_power_upper; float ESS_charge_power_step;
	float ESS_discharge_power_lower; float ESS_discharge_power_upper; float ESS_discharge_power_step;
	float ESS_capacity_lower; float ESS_capacity_upper; float ESS_capacity_step;
	float ESS_RTE_lower; float ESS_RTE_upper; float ESS_RTE_step;
	float ESS_aux_load_lower; float ESS_aux_load_upper; float ESS_aux_load_step;
	float ESS_start_SoC_lower; float ESS_start_SoC_upper; float ESS_start_SoC_step;
	int ESS_charge_mode_lower; int ESS_charge_mode_upper;
	int ESS_discharge_mode_lower; int ESS_discharge_mode_upper;
	float import_kWh_price; float export_kWh_price;
	float time_budget_min; int target_max_concurrency;
	float CAPEX_limit; float OPEX_limit;
};

// temporarily store the defaults as a constexpr struct
// ultimately the defaults should be read from a file
constexpr InputValues defaultInput = {
	//float timestep_minutes; float timestep_hours; float timewindow;
	60, 1, 8760,

	//float Fixed_load1_scalar_lower; float Fixed_load1_scalar_upper; float Fixed_load1_scalar_step;
	1, 1, 0,

	//float Fixed_load2_scalar_lower; float Fixed_load2_scalar_upper; float Fixed_load2_scalar_step;
	3, 3, 0,

	//float Flex_load_max_lower; float Flex_load_max_upper; float Flex_load_max_step;
	50.0, 50.0, 0,

	//float Mop_load_max_lower; float Mop_load_max_upper; float Mop_load_max_step;
	300.0, 300.0, 0,

	//float ScalarRG1_lower; float ScalarRG1_upper; float ScalarRG1_step;
	599.2, 599.2, 0,

	//float ScalarRG2_lower; float ScalarRG2_upper; float ScalarRG2_step;
	75.6, 75.6, 0,

	//float ScalarRG3_lower; float ScalarRG3_upper; float ScalarRG3_step;
	60.48, 60.48, 0,

	//float ScalarRG4_lower; float ScalarRG4_upper; float ScalarRG4_step;
	0.0, 0.0, 0,

	//float ScalarHL1_lower; float ScalarHL1_upper; float ScalarHL1_step;
	1.0, 1.0, 0,

	//float ScalarHYield1_lower; float ScalarHYield1_upper; float ScalarHYield1_step;
	0.0, 0.0, 0,

	//float ScalarHYield2_lower; float ScalarHYield2_upper; float ScalarHYield2_step;
	0.0, 0.0, 0,

	//float ScalarHYield3_lower; float ScalarHYield3_upper; float ScalarHYield3_step;
	0.75, 0.75, 0,

	//float ScalarHYield4_lower; float ScalarHYield4_upper; float ScalarHYield4_step;
	0.0, 0.0, 0,

	//float GridImport_lower; float GridImport_upper; float GridImport_step;
	98.29, 98.29, 0.0,

	//float GridExport_lower; float GridExport_upper; float GridExport_step;
	95.0, 95.0, 0,

	//float Import_headroom_lower; float Import_headroom_upper; float Import_headroom_step;
	0.0, 0.0, 0,

	//float Export_headroom_lower; float Export_headroom_upper; float Export_headroom_step;
	0.0, 0.0, 0,

	//float ESS_charge_power_lower; float ESS_charge_power_upper; float ESS_charge_power_step;
	300.0, 600.0, 300.0,

	//float ESS_discharge_power_lower; float ESS_discharge_power_upper; float ESS_discharge_power_step;
	300.0, 600.0, 300.0,

	//float ESS_capacity_lower; float ESS_capacity_upper; float ESS_capacity_step;
	800.0, 900.0, 20,

	//float ESS_RTE_lower; float ESS_RTE_upper; float ESS_RTE_step;
	0.86, 0.86, 0,

	//float ESS_aux_load_lower; float ESS_aux_load_upper; float ESS_aux_load_step;
	0.75, 0.75, 0,

	//float ESS_start_SoC_lower; float ESS_start_SoC_upper; float ESS_start_SoC_step;
	0.5, 0.5, 0,

	//int ESS_charge_mode_lower; int ESS_charge_mode_upper;
	1, 1,

	//int ESS_discharge_mode_lower; int ESS_discharge_mode_upper;
	1, 1,

	//float import_kWh_price; float export_kWh_price;
	30, 5,

	//float time_budget_min; int target_max_concurrency;
	1.0, 44,

	//float CAPEX_limit; float OPEX_limit;
	500, 20,
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


