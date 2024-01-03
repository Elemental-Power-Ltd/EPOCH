#pragma once

#include <iostream>
#include <thread>
#include <vector>

#include "../json.hpp"
#include "../FileIO.h"
#include "../Threadsafe.h"
#include "../Definitions.h"


struct paramRange {
	std::string name;
	float min, max, step;
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


class Optimiser {
public:
	Optimiser();

	OutputValues runMainOptimisation(nlohmann::json inputJson);
	OutputValues initialiseOptimisation(nlohmann::json inputJson);


private:
	int generateTasks(const std::vector<paramRange>& paramGrid, SafeQueue<std::vector<std::pair<std::string, float>>>& taskQueue);
	void appendSumToDataTable(CustomDataTable& outTable, CustomDataTable& singleTable);
	std::pair<float, float> findMinValueandIndex(const CustomDataTable& dataColumns, const std::string& columnName);
	std::pair<float, float> findMaxValueandIndex(const CustomDataTable& dataColumns, const std::string& columnName);
	std::tuple<float, float, float> getColumnStats(const std::vector<std::pair<std::string, std::vector<float>>>& CustomDataTable);
	void appendDataColumns(std::vector<std::pair<std::string, std::vector<float>>>& cumDataColumns, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumnsN);
	CustomDataTable SumDataTable(const CustomDataTable& dataTable);



};

