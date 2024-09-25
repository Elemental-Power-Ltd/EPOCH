#include "FileHandling.hpp"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <regex>
#include <string>
#include <sstream>
#include <vector>

#include <spdlog/spdlog.h>

#include "../Definitions.hpp"
#include "../Exceptions.hpp"

// Define macros to simplify creating the mapping for each struct member
#define MEMBER_MAPPING_FLOAT(member) {#member, [](const InputValues& s) -> float { return s.member; }, nullptr}
#define MEMBER_MAPPING_INT(member) {#member, nullptr, [](const InputValues& s) -> int { return s.member; }}

// Create an array of MemberMapping for the struct members with a common pattern (using only MEMBER_MAPPING... macros)
MemberMapping memberMappings[] = {
	MEMBER_MAPPING_FLOAT(timestep_hours), MEMBER_MAPPING_FLOAT(timewindow),
	MEMBER_MAPPING_FLOAT(Fixed_load1_scalar_lower), MEMBER_MAPPING_FLOAT(Fixed_load1_scalar_upper), MEMBER_MAPPING_FLOAT(Fixed_load1_scalar_step),
	MEMBER_MAPPING_FLOAT(Fixed_load2_scalar_lower), MEMBER_MAPPING_FLOAT(Fixed_load2_scalar_upper), MEMBER_MAPPING_FLOAT(Fixed_load2_scalar_step),
	MEMBER_MAPPING_FLOAT(Flex_load_max_lower), MEMBER_MAPPING_FLOAT(Flex_load_max_upper), MEMBER_MAPPING_FLOAT(Flex_load_max_step),
	MEMBER_MAPPING_FLOAT(Mop_load_max_lower), MEMBER_MAPPING_FLOAT(Mop_load_max_upper), MEMBER_MAPPING_FLOAT(Mop_load_max_step),
	MEMBER_MAPPING_FLOAT(ScalarRG1_lower), MEMBER_MAPPING_FLOAT(ScalarRG1_upper), MEMBER_MAPPING_FLOAT(ScalarRG1_step),
	MEMBER_MAPPING_FLOAT(ScalarRG2_lower), MEMBER_MAPPING_FLOAT(ScalarRG2_upper), MEMBER_MAPPING_FLOAT(ScalarRG2_step),
	MEMBER_MAPPING_FLOAT(ScalarRG3_lower), MEMBER_MAPPING_FLOAT(ScalarRG3_upper), MEMBER_MAPPING_FLOAT(ScalarRG3_step),
	MEMBER_MAPPING_FLOAT(ScalarRG4_lower), MEMBER_MAPPING_FLOAT(ScalarRG4_upper), MEMBER_MAPPING_FLOAT(ScalarRG4_step),
	MEMBER_MAPPING_FLOAT(ScalarHYield_lower), MEMBER_MAPPING_FLOAT(ScalarHYield_upper), MEMBER_MAPPING_FLOAT(ScalarHYield_step),
	MEMBER_MAPPING_INT(s7_EV_CP_number_lower), MEMBER_MAPPING_INT(s7_EV_CP_number_upper), MEMBER_MAPPING_INT(s7_EV_CP_number_step),
	MEMBER_MAPPING_INT(f22_EV_CP_number_lower), MEMBER_MAPPING_INT(f22_EV_CP_number_upper), MEMBER_MAPPING_INT(f22_EV_CP_number_step),
	MEMBER_MAPPING_INT(r50_EV_CP_number_lower), MEMBER_MAPPING_INT(r50_EV_CP_number_upper), MEMBER_MAPPING_INT(r50_EV_CP_number_step),
	MEMBER_MAPPING_INT(u150_EV_CP_number_lower), MEMBER_MAPPING_INT(u150_EV_CP_number_upper),MEMBER_MAPPING_INT(u150_EV_CP_number_step),
	MEMBER_MAPPING_FLOAT(EV_flex_lower), MEMBER_MAPPING_FLOAT(EV_flex_upper), MEMBER_MAPPING_FLOAT(EV_flex_step),
	MEMBER_MAPPING_FLOAT(ScalarHL1_lower), MEMBER_MAPPING_FLOAT(ScalarHL1_upper), MEMBER_MAPPING_FLOAT(ScalarHL1_step),
	MEMBER_MAPPING_FLOAT(ASHP_HPower_lower), MEMBER_MAPPING_FLOAT(ASHP_HPower_upper), MEMBER_MAPPING_FLOAT(ASHP_HPower_step),
	MEMBER_MAPPING_INT(ASHP_HSource_lower), MEMBER_MAPPING_INT(ASHP_HSource_upper), MEMBER_MAPPING_INT(ASHP_HSource_step),
	MEMBER_MAPPING_FLOAT(ASHP_RadTemp_lower), MEMBER_MAPPING_FLOAT(ASHP_RadTemp_upper), MEMBER_MAPPING_FLOAT(ASHP_RadTemp_step),
	MEMBER_MAPPING_FLOAT(ASHP_HotTemp_lower), MEMBER_MAPPING_FLOAT(ASHP_HotTemp_upper), MEMBER_MAPPING_FLOAT(ASHP_HotTemp_step),
	MEMBER_MAPPING_FLOAT(GridImport_lower), MEMBER_MAPPING_FLOAT(GridImport_upper), MEMBER_MAPPING_FLOAT(GridImport_step),
	MEMBER_MAPPING_FLOAT(GridExport_lower), MEMBER_MAPPING_FLOAT(GridExport_upper), MEMBER_MAPPING_FLOAT(GridExport_step),
	MEMBER_MAPPING_FLOAT(Import_headroom_lower), MEMBER_MAPPING_FLOAT(Import_headroom_upper), MEMBER_MAPPING_FLOAT(Import_headroom_step),
	MEMBER_MAPPING_FLOAT(Export_headroom_lower), MEMBER_MAPPING_FLOAT(Export_headroom_upper), MEMBER_MAPPING_FLOAT(Export_headroom_step),
	MEMBER_MAPPING_FLOAT(Min_power_factor_lower), MEMBER_MAPPING_FLOAT(Min_power_factor_upper), MEMBER_MAPPING_FLOAT(Min_power_factor_step),
	MEMBER_MAPPING_FLOAT(ESS_charge_power_lower), MEMBER_MAPPING_FLOAT(ESS_charge_power_upper), MEMBER_MAPPING_FLOAT(ESS_charge_power_step),
	MEMBER_MAPPING_FLOAT(ESS_discharge_power_lower), MEMBER_MAPPING_FLOAT(ESS_discharge_power_upper), MEMBER_MAPPING_FLOAT(ESS_discharge_power_step),
	MEMBER_MAPPING_FLOAT(ESS_capacity_lower), MEMBER_MAPPING_FLOAT(ESS_capacity_upper), MEMBER_MAPPING_FLOAT(ESS_capacity_step),
	MEMBER_MAPPING_FLOAT(ESS_start_SoC_lower), MEMBER_MAPPING_FLOAT(ESS_start_SoC_upper), MEMBER_MAPPING_FLOAT(ESS_start_SoC_step),
	MEMBER_MAPPING_INT(ESS_charge_mode_lower), MEMBER_MAPPING_INT(ESS_charge_mode_upper),
	MEMBER_MAPPING_INT(ESS_discharge_mode_lower), MEMBER_MAPPING_INT(ESS_discharge_mode_upper),
	MEMBER_MAPPING_FLOAT(Export_kWh_price),
	MEMBER_MAPPING_FLOAT(time_budget_min), MEMBER_MAPPING_INT(target_max_concurrency),
	MEMBER_MAPPING_FLOAT(CAPEX_limit), MEMBER_MAPPING_FLOAT(OPEX_limit)
};


// Define macros to simplify creating the mapping for each struct member
#define OUT_MEMBER_MAPPING_FLOAT(member) {#member, [](const OutputValues& s) -> float { return s.member; }, nullptr}
#define OUT_MEMBER_MAPPING_INT(member) {#member, nullptr, [](const OutputValues& s) -> int { return s.member; }}
#define OUT_MEMBER_MAPPING_UINT64(member) {#member, nullptr, [](const OutputValues& s) -> uint64_t { return s.member; }}

OutMemberMapping OutMemberMappings[] = {
	OUT_MEMBER_MAPPING_FLOAT(maxVal),
	OUT_MEMBER_MAPPING_FLOAT(minVal),
	OUT_MEMBER_MAPPING_FLOAT(meanVal),
	OUT_MEMBER_MAPPING_FLOAT(est_seconds),
	OUT_MEMBER_MAPPING_FLOAT(est_hours),
	OUT_MEMBER_MAPPING_UINT64(num_scenarios),
	OUT_MEMBER_MAPPING_FLOAT(time_taken),
	OUT_MEMBER_MAPPING_FLOAT(Fixed_load1_scalar), OUT_MEMBER_MAPPING_FLOAT(Fixed_load2_scalar), OUT_MEMBER_MAPPING_FLOAT(Flex_load_max), OUT_MEMBER_MAPPING_FLOAT(Mop_load_max),
	OUT_MEMBER_MAPPING_FLOAT(ScalarRG1), OUT_MEMBER_MAPPING_FLOAT(ScalarRG2), OUT_MEMBER_MAPPING_FLOAT(ScalarRG3), OUT_MEMBER_MAPPING_FLOAT(ScalarRG4), OUT_MEMBER_MAPPING_FLOAT(ScalarHYield),
	OUT_MEMBER_MAPPING_INT(s7_EV_CP_number), OUT_MEMBER_MAPPING_INT(f22_EV_CP_number), OUT_MEMBER_MAPPING_INT(r50_EV_CP_number), OUT_MEMBER_MAPPING_INT(u150_EV_CP_number), OUT_MEMBER_MAPPING_FLOAT(EV_flex),
	OUT_MEMBER_MAPPING_FLOAT(GridImport), OUT_MEMBER_MAPPING_FLOAT(GridExport), OUT_MEMBER_MAPPING_FLOAT(Import_headroom), OUT_MEMBER_MAPPING_FLOAT(Export_headroom), OUT_MEMBER_MAPPING_FLOAT(Min_power_factor),
	OUT_MEMBER_MAPPING_FLOAT(ScalarHL1), OUT_MEMBER_MAPPING_FLOAT(ASHP_HPower), OUT_MEMBER_MAPPING_FLOAT(ASHP_HSource), OUT_MEMBER_MAPPING_FLOAT(ASHP_RadTemp), OUT_MEMBER_MAPPING_FLOAT(ASHP_HotTemp),
	OUT_MEMBER_MAPPING_FLOAT(ESS_charge_power), OUT_MEMBER_MAPPING_FLOAT(ESS_discharge_power), OUT_MEMBER_MAPPING_FLOAT(ESS_capacity), OUT_MEMBER_MAPPING_FLOAT(ESS_start_SoC),
	OUT_MEMBER_MAPPING_INT(ESS_charge_mode), OUT_MEMBER_MAPPING_INT(ESS_discharge_mode),
	OUT_MEMBER_MAPPING_FLOAT(Export_kWh_price),
	OUT_MEMBER_MAPPING_FLOAT(CAPEX), OUT_MEMBER_MAPPING_FLOAT(annualised), OUT_MEMBER_MAPPING_FLOAT(scenario_cost_balance), OUT_MEMBER_MAPPING_FLOAT(payback_horizon), OUT_MEMBER_MAPPING_FLOAT(scenario_carbon_balance),
	OUT_MEMBER_MAPPING_UINT64(CAPEX_index), OUT_MEMBER_MAPPING_UINT64(annualised_index), OUT_MEMBER_MAPPING_UINT64(scenario_cost_balance_index), OUT_MEMBER_MAPPING_UINT64(payback_horizon_index), OUT_MEMBER_MAPPING_UINT64(scenario_carbon_balance_index),
	OUT_MEMBER_MAPPING_UINT64(scenario_index),
	OUT_MEMBER_MAPPING_UINT64(num_scenarios), OUT_MEMBER_MAPPING_FLOAT(est_hours), OUT_MEMBER_MAPPING_FLOAT(est_seconds)
};

std::vector<float> readCSVColumn(const std::filesystem::path& filename, int column, bool skipHeader) {
	std::ifstream file(filename);
	std::vector<float> columnValues;
	std::string line;
	bool columnHasValues = false;

	if (!file.is_open()) {
		throw FileReadException(filename.filename().string());
	}

	if (skipHeader) {
		// Ignore the first line
		std::getline(file, line);
	}

	while (std::getline(file, line)) {

		// Check if the line contains only commas (and possibly whitespaces), which indicates the end of the file
		if (std::all_of(line.begin(), line.end(), [](char c) { return c == ',' || std::isspace(c); })) {
			break;
		}

		std::stringstream ss(line);
		std::string cell;
		std::vector<std::string> row;

		// Parse each cell in the row
		while (std::getline(ss, cell, ',')) {
			row.emplace_back(cell);
		}

		// If the row ends with a comma, add an empty string to the row (signifying an empty column)
		if (line.back() == ',') {
			row.emplace_back("");
		}

		// Convert the value from the specified column to float and store it in the vector
		int column_1 = column - 1;

		if (row.size() <= column_1) {
			spdlog::error("Insufficient columns at line {}", line);
			throw FileReadException(filename.filename().string());
		}

		if (row[column_1] == "") {
			// treat missing values as 0
			columnValues.emplace_back(0.0f);
		}
		else {
			try {
				float val = std::stof(row[column_1]);
				columnValues.emplace_back(val);
			}
			catch (const std::exception& e) {
				spdlog::error("Failed to parse float in line {} ({})", line, e.what());
				throw FileReadException(filename.filename().string());
			}
		}
	}

	return columnValues;
}

// Read a column from a CSV file, ignoring the first entry
std::vector<float> readCSVColumnAndSkipHeader(const std::filesystem::path& filename, int column)
{
	return readCSVColumn(filename, column, true);
}

// Read a column from a CSV file, including the first entry
std::vector<float> readCSVColumnWithoutSkip(const std::filesystem::path& filename, int column)
{
	return readCSVColumn(filename, column, false);
}

std::vector<std::vector<float>> readCSVAsTable(const std::filesystem::path& filename) {
	std::vector<std::vector<float>> table{};

	std::ifstream file(filename);
	std::string line;

	// Check if the file is open
	if (!file.is_open()) {
		throw FileReadException(filename.filename().string());
	}

	// Read file line by line
	while (std::getline(file, line)) {
		std::vector<float> rowData;
		std::stringstream ss(line);
		std::string cell;

		// Parse the line into double values
		while (std::getline(ss, cell, ',')) {
			rowData.push_back(std::stod(cell));
		}

		table.emplace_back(rowData);
	}
	file.close();
	return table;
}

// Function to read a specific row from a CSV file
std::vector<float> readCSVrow(const std::filesystem::path& filename, int row) {
	std::ifstream file(filename);
	std::vector<float> rowData;
	std::string line;
	int currentRow = 0;

	// Check if the file is open
	if (!file.is_open()) {
		throw FileReadException(filename.filename().string());
	}

	// Read file line by line
	while (std::getline(file, line)) {
		if (currentRow == row) {
			std::stringstream ss(line);
			std::string cell;

			// Parse the line into double values
			while (std::getline(ss, cell, ',')) {
				rowData.push_back(std::stod(cell));
			}

			break; // Stop reading after the desired row is found
		}
		currentRow++;
	}

	file.close();
	return rowData;
}

void printVector(const std::vector<float>& vec) {
	for (float value : vec) {
		spdlog::info("vector value {}", value);
	}
	
}


void writeResultsToCSV(std::filesystem::path filepath, const std::vector<SimulationResult>& results)
{
	std::ofstream outFile(filepath);

	if (!outFile.is_open()) {
		spdlog::error("Failed to open the output file!");
		throw FileReadException(filepath.filename().string());
	}

	// write the column headers
	for (int i = 0; i < resultHeader.size() - 1; i++) {
		outFile << resultHeader[i];
		outFile << ",";
	}
	// write the final column without a comma
	outFile << resultHeader[resultHeader.size() - 1];
	outFile << "\n";

	// write each result
	for (const auto& result : results) {
		// These must be written in exactly the same order as the resultHeader
		outFile << result.paramIndex << ",";
		outFile << result.runtime << ",";

		outFile << result.total_annualised_cost << ",";
		outFile << result.project_CAPEX << ",";
		outFile << result.scenario_cost_balance << ",";
		outFile << result.payback_horizon_years << ",";
		outFile << result.scenario_carbon_balance << ",";

		outFile << result.Rgen_total << ",";
		outFile << result.Total_load << ",";
		outFile << result.ESUM << ",";
		outFile << result.ESS_available_discharge_power << ",";
		outFile << result.ESS_available_charge_power << ",";
		outFile << result.ESS_Rgen_only_charge << ",";
		outFile << result.ESS_discharge << ",";
		outFile << result.ESS_charge << ",";
		outFile << result.ESS_resulting_SoC << ",";
		outFile << result.Pre_grid_balance << ",";
		outFile << result.Grid_Import << ",";
		outFile << result.Grid_Export << ",";
		outFile << result.Post_grid_balance << ",";
		outFile << result.Pre_flex_import_shortfall << ",";
		outFile << result.Pre_Mop_curtailed_export << ",";
		outFile << result.Actual_import_shortfall << ",";
		outFile << result.Actual_curtailed_export << ",";
		outFile << result.Actual_high_priority_load << ",";
		outFile << result.Actual_low_priority_load << ",";
		outFile << result.Heatload << ",";
		outFile << result.Scaled_heatload << ",";
		outFile << result.Electrical_load_scaled_heat_yield << ",";
		outFile << result.Heat_shortfall << ",";
		outFile << result.Heat_surplus;  // no comma
		outFile << '\n';
	}
}

void writeResultsToCSV(std::filesystem::path filepath, const std::vector<ObjectiveResult>& results)
{
	std::ofstream outFile(filepath);

	if (!outFile.is_open()) {
		spdlog::error("Failed to open the output file!");
		throw FileReadException(filepath.filename().string());
	}

	// write the column headers
	writeObjectiveResultHeader(outFile);

	// write each result
	for (const auto& result : results) {
		writeObjectiveResultRow(outFile, result);
	}
}

void appendResultToCSV(std::filesystem::path filepath, const ObjectiveResult& result) {
	// open the file in append mode
	std::ofstream outFile(filepath, std::ios::app);

	if (!outFile.is_open()) {
		spdlog::error("Failed to open the output file!");
		throw FileReadException(filepath.filename().string());
	}

	outFile << result.payback_horizon_years << "," << result.project_CAPEX << "\n";

}

void writeObjectiveResultHeader(std::ofstream& outFile) {
	outFile << "Parameter index" << ",";
	outFile << "annualised_cost" << ",";
	outFile << "capex" << ",";
	outFile << "cost_balance" << ",";
	outFile << "payback_horizon" << ",";
	outFile << "carbon_balance";

	// deliberately omit the comma for carbon balance
	// to allow the loop to have a comma for each entry (before)

	for (auto paramName: taskDataParamNames) {
		outFile << ",";
		outFile << paramName;
	}
	// no trailing comma
	outFile << "\n";
}

void writeObjectiveResultRow(std::ofstream& outFile, const ObjectiveResult& result) {
	// These must be written in exactly the same order as the header
	outFile << result.taskData.paramIndex << ",";

	outFile << result.total_annualised_cost << ",";
	outFile << result.project_CAPEX << ",";
	outFile << result.scenario_cost_balance << ",";
	outFile << result.payback_horizon_years << ",";
	outFile << result.scenario_carbon_balance << ",";

	const TaskData& taskData = result.taskData;

	outFile << taskData.Fixed_load1_scalar << ",";
	outFile << taskData.Fixed_load2_scalar << ",";
	outFile << taskData.Flex_load_max << ",";
	outFile << taskData.Mop_load_max << ",";
	outFile << taskData.ScalarRG1 << ",";
	outFile << taskData.ScalarRG2 << ",";
	outFile << taskData.ScalarRG3 << ",";
	outFile << taskData.ScalarRG4 << ",";
	outFile << taskData.ScalarHYield << ",";
	outFile << taskData.s7_EV_CP_number << ",";
	outFile << taskData.f22_EV_CP_number << ",";
	outFile << taskData.r50_EV_CP_number << ",";
	outFile << taskData.u150_EV_CP_number << ",";
	outFile << taskData.EV_flex << ",";
	outFile << taskData.ScalarHL1 << ",";
	outFile << taskData.ASHP_HPower << ",";
	outFile << taskData.ASHP_HSource << ",";
	outFile << taskData.ASHP_RadTemp << ",";
	outFile << taskData.ASHP_HotTemp << ",";
	outFile << taskData.GridImport << ",";
	outFile << taskData.GridExport << ",";
	outFile << taskData.Import_headroom << ",";
	outFile << taskData.Export_headroom << ",";
	outFile << taskData.Min_power_factor << ",";
	outFile << taskData.ESS_charge_power << ",";
	outFile << taskData.ESS_discharge_power << ",";
	outFile << taskData.ESS_capacity << ",";
	outFile << taskData.ESS_start_SoC << ",";
	outFile << taskData.Export_kWh_price << ",";
	outFile << taskData.time_budget_min << ",";
	outFile << taskData.CAPEX_limit << ",";
	outFile << taskData.OPEX_limit << ",";
	outFile << taskData.ESS_charge_mode << ",";
	outFile << taskData.ESS_discharge_mode; // no trailing comma
	outFile << "\n";
}

void writeTimeSeriesToCSV(std::filesystem::path filepath, FullSimulationResult fullResult)
{
	std::ofstream outFile(filepath);

	if (!outFile.is_open()) {
		spdlog::error("Failed to open the output file!");
		throw FileReadException(filepath.filename().string());
	}

	// Write the column headers

	outFile << "Rgen_total" << ",";
	outFile << "ESUM" << ",";
	outFile << "ESS_available_discharge_power" << ",";
	outFile << "ESS_available_charge_power" << ",";
	outFile << "ESS_Rgen_only_charge" << ",";
	outFile << "ESS_discharge" << ",";
	outFile << "ESS_charge" << ",";
	outFile << "ESS_resulting_SoC" << ",";
	outFile << "Pre_grid_balance" << ",";
	outFile << "Grid_Import" << ",";
	outFile << "Grid_Export" << ",";
	outFile << "Post_grid_balance" << ",";
	outFile << "Pre_flex_import_shortfall" << ",";
	outFile << "Pre_Mop_curtailed_export" << ",";
	outFile << "Actual_import_shortfall" << ",";
	outFile << "Actual_curtailed_export" << ",";
	outFile << "Actual_high_priority_load" << ",";
	outFile << "Actual_low_priority_load" << ",";
	outFile << "Heatload" << ",";
	outFile << "DWH_load" << ",";
	outFile << "DHW_charging" << ",";
	outFile << "DHW_SoC" << ",";
	outFile << "DHW_Standby_loss" << ",";
	outFile << "DHW_temperature" << ",";
	outFile << "DHW_Shortfall" << ",";
	outFile << "Scaled_heatload" << ",";
	outFile << "Electrical_load_scaled_heat_yield" << ",";
	outFile << "Heat_shortfall" << ",";
	outFile << "Heat_surplus";
	// no trailing comma
	outFile << "\n"; // newline

	// write the values
	for (int i = 0; i < fullResult.ESUM.size(); i++) {
		outFile << fullResult.Rgen_total[i] << ",";
		outFile << fullResult.ESUM[i] << ",";
		outFile << fullResult.ESS_available_discharge_power[i] << ",";
		outFile << fullResult.ESS_available_charge_power[i] << ",";
		outFile << fullResult.ESS_Rgen_only_charge[i] << ",";
		outFile << fullResult.ESS_discharge[i] << ",";
		outFile << fullResult.ESS_charge[i] << ",";
		outFile << fullResult.ESS_resulting_SoC[i] << ",";
		outFile << fullResult.Pre_grid_balance[i] << ",";
		outFile << fullResult.Grid_Import[i] << ",";
		outFile << fullResult.Grid_Export[i] << ",";
		outFile << fullResult.Post_grid_balance[i] << ",";
		outFile << fullResult.Pre_flex_import_shortfall[i] << ",";
		outFile << fullResult.Pre_Mop_curtailed_export[i] << ",";
		outFile << fullResult.Actual_import_shortfall[i] << ",";
		outFile << fullResult.Actual_curtailed_export[i] << ",";
		outFile << fullResult.Actual_high_priority_load[i] << ",";
		outFile << fullResult.Actual_low_priority_load[i] << ",";
		outFile << fullResult.Heatload[i] << ",";
		outFile << fullResult.DHW_load[i] << ",";
		outFile << fullResult.DHW_charging[i] << ",";
		outFile << fullResult.DHW_SoC[i] << ",";
		outFile << fullResult.DHW_Standby_loss[i] << ",";
		outFile << fullResult.DHW_ave_temperature[i] << ",";
		outFile << fullResult.DHW_Shortfall[i] << ",";
		outFile << fullResult.Scaled_heatload[i] << ",";
		outFile << fullResult.Electrical_load_scaled_heat_yield[i] << ",";
		outFile << fullResult.Heat_shortfall[i] << ",";
		outFile << fullResult.Heat_surplus[i]; // no trailing comma
		outFile << "\n";
	}

}

void writeCostDataToCSV(std::filesystem::path filepath, FullSimulationResult fullResult)
{
	std::ofstream outFile(filepath);

	if (!outFile.is_open()) {
		spdlog::error("Failed to open the output file!");
		throw FileReadException(filepath.filename().string());
	}

	// Write the column headers

	//outFile << "ESUM" << ",";
	outFile << "Baseline_electricity_cost (£)" << ",";	// no trailing comma
	outFile << "Baseline_fuel_cost (£)" << ",";
	
	outFile << "Baseline_electricity_carbon (kgCO2)" << ",";
	outFile << "Baseline_fuel_carbon (kgCO2)" << ",";
	
	outFile << "Scenario_electricity_cost (£)" << ",";
	outFile << "Scenario_fuel_cost (£)" << ",";
	outFile << "Scenario_grid_export_cost (£)" << ",";

	outFile << "Resulting_EV_charge_revenue (£)" << ",";
	outFile << "Resulting_Data_Centre_revenue (£)" << ",";
	outFile << "Scenario_avoided_fuel_cost (£)" << ",";

	outFile << "Scenario_electricity_carbon (kgCO2)" << ",";
	outFile << "Scenario_fuel_carbon (kgCO2)" << ",";
	outFile << "Scenario_grid_export_carbon (kgCO2)" << ",";
	outFile << "Scenario_avoided_fuel_carbon (kgCO2)" << ",";

	outFile << "ESS_PCS_CAPEX (£)" << ",";
	outFile << "ESS_PCS_OPEX (£)" << ",";
	outFile << "ESS_ENCLOSURE_CAPEX (£)" << ",";
	outFile << "ESS_ENCLOSURE_OPEX (£)" << ",";
	outFile << "ESS_ENCLOSURE_DISPOSAL (£)" << ",";

	outFile << "PVpanel_CAPEX (£)" << ",";
	outFile << "PVBoP_CAPEX (£)" << ",";
	outFile << "PVroof_CAPEX (£)" << ",";
	outFile << "PVground_CAPEX (£)" << ",";
	outFile << "PV_OPEX (£)" << ",";

	outFile << "EV_CP_cost (£)" << ",";
	outFile << "EV_CP_install (£)" << ",";

	outFile << "Grid_CAPEX (£)" << ",";

	outFile << "ASHP_CAPEX (£)";

	// no trailing comma
	outFile << "\n"; // newline

	// write the values
     //	outFile << fullResult.ESUM[i] << ",";
	outFile << fullResult.Baseline_electricity_cost << ","; 
	outFile << fullResult.Baseline_fuel_cost << ",";

	outFile << fullResult.Baseline_electricity_carbon << ",";
	outFile << fullResult.Baseline_fuel_carbon << ",";

	outFile << fullResult.Scenario_electricity_cost << ",";
	outFile << fullResult.Scenario_fuel_cost << ",";
	outFile << fullResult.Scenario_grid_export_cost << ",";
	
	outFile << fullResult.Resulting_EV_charge_revenue << ",";

	outFile << fullResult.Resulting_Data_Centre_revenue << ",";

	outFile << fullResult.Scenario_avoided_fuel_cost << ",";

	outFile << fullResult.Scenario_electricity_carbon << ",";
	outFile << fullResult.Scenario_fuel_carbon << ",";
	outFile << fullResult.Scenario_grid_export_carbon << ",";
	outFile << fullResult.Scenario_avoided_fuel_carbon << "'";
	

	outFile << fullResult.ESS_PCS_CAPEX << ",";
	outFile << fullResult.ESS_PCS_OPEX << ",";
	outFile << fullResult.ESS_ENCLOSURE_CAPEX << ",";
	outFile << fullResult.ESS_ENCLOSURE_OPEX << ",";
	outFile << fullResult.ESS_ENCLOSURE_DISPOSAL << ",";

	outFile << fullResult.PVpanel_CAPEX << ",";
	outFile << fullResult.PVBoP_CAPEX << ",";
	outFile << fullResult.PVroof_CAPEX << ",";
	outFile << fullResult.PVground_CAPEX << ",";
	outFile << fullResult.PV_OPEX << ",";

	outFile << fullResult.EV_CP_cost << ",";
	outFile << fullResult.EV_CP_install << ",";

	outFile << fullResult.Grid_CAPEX << ",";

	outFile << fullResult.ASHP_CAPEX; // no trailing comma

	outFile << "\n";
	

	//Report the objectives in same file

	//outFile << "ESUM" << ",";
	outFile << "Total_annualsed_cost (£)" << ",";	// no trailing comma
	outFile << "Project_CAPEX (£)" << ",";
	outFile << "Scenario_cost_balance (£)" << ",";
	outFile << "Payback_horizon" << ",";
	outFile << "Scenario_carbon_balance (kgCO2)" << ",";

	outFile << "\n";

	outFile << fullResult.total_annualised_cost << ",";
	outFile << fullResult.project_CAPEX << ",";
	outFile << fullResult.scenario_cost_balance << ",";
	outFile << fullResult.payback_horizon_years << ",";
	outFile << fullResult.scenario_carbon_balance;

	outFile << "\n";

}



// Custom function to convert a struct to a JSON object
nlohmann::json inputToJson(const InputValues& data) {

	size_t Size = std::size(memberMappings);

	nlohmann::json jsonObj;
	for (size_t i = 0; i < Size; ++i) {
		const auto& mapping = memberMappings[i];
		if (mapping.getFloat) {
			jsonObj[mapping.name] = mapping.getFloat(data);
		}
		else if (mapping.getInt) {
			jsonObj[mapping.name] = mapping.getInt(data);
		}
	}
	return jsonObj;
}


// Custom function to convert a struct to a JSON object
nlohmann::json outputToJson(const OutputValues& data) {

	size_t Size = std::size(OutMemberMappings);

	nlohmann::json jsonObj;
	for (size_t i = 0; i < Size; ++i) {
		const auto& mapping = OutMemberMappings[i];
		if (mapping.getFloat) {
			jsonObj[mapping.name] = mapping.getFloat(data);
		}
		else if (mapping.getInt) {
			jsonObj[mapping.name] = mapping.getInt(data);
		}
	}
	return jsonObj;
}

// function to group the keys in a JSON, such that we have a key-tuple JSON describing parameter ranges
nlohmann::json convert_to_ranges(nlohmann::json& j) {
	// This regex matches strings ending with "_lower", "_upper", or "_step"
	std::regex param_regex("(.+)(_lower|_upper|_step)$");
	std::smatch match;

	nlohmann::json new_json;
	for (auto& el : j.items()) {
		std::string key = el.key();
		if (std::regex_match(key, match, param_regex)) {
			// Extract the base parameter name and the suffix
			std::string param_base = match[1].str();
			std::string suffix = match[2].str();

			// Initialize the tuple if it doesn't exist
			if (!new_json.contains(param_base)) {
				//				new_json[param_base] = nlohmann::json::array({ nullptr, nullptr, nullptr });
				new_json[param_base] = nlohmann::json::array({ 0.0, 0.0, 0.0 });
			}

			// Assign the value to the correct position in the tuple
//			if (suffix == "_lower") new_json[param_base][0] = el.value();
//			else if (suffix == "_upper") new_json[param_base][1] = el.value();
//			else if (suffix == "_step") new_json[param_base][2] = el.value();
			if (suffix == "_lower") new_json[param_base][0] = el.value().is_null() ? nlohmann::json(0.0) : el.value();
			else if (suffix == "_upper") new_json[param_base][1] = el.value().is_null() ? nlohmann::json(0.0) : el.value();
			else if (suffix == "_step") new_json[param_base][2] = el.value().is_null() ? nlohmann::json(0.0) : el.value();
		}
		else {
			// Copy over any keys that don't match the pattern
			new_json[key] = el.value();
		}
	}

	return new_json;
}

nlohmann::json handleJsonConversion(const InputValues& inputValues, std::filesystem::path inputParametersFilepath) {
	// Aim: to export 'inputvalues' to a json file that can be read e.g. as a Python dict, s.t. other EPL software can use this as an input

	nlohmann::json jsonObj = inputToJson(inputValues);
	nlohmann::json converted_json = convert_to_ranges(jsonObj);

	writeJsonToFile(converted_json, inputParametersFilepath);
	spdlog::info("JSON input saved succesfully");
	return converted_json;

}

void writeJsonToFile(const nlohmann::json& jsonObj, std::filesystem::path filepath) {
	try {
		std::ofstream file(filepath);
		file << jsonObj.dump(4);  // The "4" argument adds pretty-printing with indentation
		file.close();
	}
	catch (const std::exception e) {
		spdlog::warn("Error: {}", e.what());
	}
}

nlohmann::json readJsonFromFile(std::filesystem::path filepath)
{
	try {
		std::ifstream f(filepath);
		return nlohmann::json::parse(f);
	}
	catch (const std::exception& e) {
		throw FileReadException(filepath.filename().string());
	}
}

const HistoricalData readHistoricalData(const FileConfig& fileConfig)
{
	std::filesystem::path eloadFilepath = fileConfig.getEloadFilepath();

	//read the electric load data
	std::vector<float> hotel_eload_data = readCSVColumnAndSkipHeader(eloadFilepath, 4); // read the column of the CSV data and store in vector data
	std::vector<float> ev_eload_data = readCSVColumnAndSkipHeader(eloadFilepath, 5); // read the column of the CSV data and store in vector data

	//read the heat load data
	std::filesystem::path hloadFilepath = fileConfig.getHloadFilepath();
	std::vector<float> heatload_data = readCSVColumnAndSkipHeader(hloadFilepath, 4); // read the column of the CSV data and store in vector data
	
	//read the renewable generation data
	std::filesystem::path rgenFilepath = fileConfig.getRgenFilepath();
	std::vector<float> RGen_data_1 = readCSVColumnAndSkipHeader(rgenFilepath, 4); // read the column of the CSV data and store in vector data
	std::vector<float> RGen_data_2 = readCSVColumnAndSkipHeader(rgenFilepath, 5);
	std::vector<float> RGen_data_3 = readCSVColumnAndSkipHeader(rgenFilepath, 6);
	std::vector<float> RGen_data_4 = readCSVColumnAndSkipHeader(rgenFilepath, 7);

	//read in the air temperature data
	std::filesystem::path airtempFilepath = fileConfig.getAirtempFilepath();
	std::vector<float> airtemp_data = readCSVColumnAndSkipHeader(airtempFilepath, 4);

	//read in the import tariff data
	std::filesystem::path importtariffFilepath = fileConfig.getImporttariffFilepath();
	std::vector<float> importtariff_data = readCSVColumnAndSkipHeader(importtariffFilepath, 4);

	//read in the GridCO2 data
	std::filesystem::path gridCO2Filepath = fileConfig.getGridCO2Filepath();
	std::vector<float> gridCO2_data = readCSVColumnAndSkipHeader(gridCO2Filepath, 4);

	//read in the DWH demand data
	std::filesystem::path DHWloadFilepath = fileConfig.getDHWloadFilepath();
	std::vector<float> DHWload_data = readCSVColumnAndSkipHeader(DHWloadFilepath, 4); // read the column of the CSV data and store in vector data


	//read in the ASHP data
	std::filesystem::path ASHPinputFilepath = fileConfig.getASHPinputFilepath();
	std::vector<std::vector<float>> ASHPinputtable = readCSVAsTable(ASHPinputFilepath);

	std::filesystem::path ASHPoutputFilepath = fileConfig.getASHPoutputFilepath();
	std::vector<std::vector<float>> ASHPoutputtable = readCSVAsTable(ASHPoutputFilepath);

	
	return {
	   toEigen(hotel_eload_data),
	   toEigen(ev_eload_data),
	   toEigen(heatload_data),
	   toEigen(RGen_data_1),
	   toEigen(RGen_data_2),
	   toEigen(RGen_data_3),
	   toEigen(RGen_data_4),
	   toEigen(airtemp_data),
	   toEigen(importtariff_data),
	   toEigen(gridCO2_data),
	   toEigen(DHWload_data),
	   toEigen(ASHPinputtable),
	   toEigen(ASHPoutputtable)
	};
}

Eigen::VectorXf toEigen(const std::vector<float>& vec)
{
	Eigen::VectorXf eig = Eigen::VectorXf(vec.size());

	for (int i = 0; i < vec.size(); i++) {
		eig[i] = vec[i];
	}

	return eig;
}

Eigen::MatrixXf toEigen(const std::vector<std::vector<float>>& mat) {
	Eigen::MatrixXf eig = Eigen::MatrixXf(mat.size(), mat[0].size());

	for (int i = 0; i < mat.size(); i++) {
		for (int j = 0; j < mat[0].size(); j++) {
			eig(i,j) = mat[i][j];
		}
	}

	return eig;
}


