#include "FileHandling.hpp"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <regex>
#include <string>
#include <sstream>
#include <vector>

#include "../Definitions.h"

// Define macros to simplify creating the mapping for each struct member
#define MEMBER_MAPPING_FLOAT(member) {#member, [](const InputValues& s) -> float { return s.member; }, nullptr}
#define MEMBER_MAPPING_INT(member) {#member, nullptr, [](const InputValues& s) -> int { return s.member; }}

// Create an array of MemberMapping for the struct members with a common pattern (using only MEMBER_MAPPING... macros)
MemberMapping memberMappings[] = {
	MEMBER_MAPPING_FLOAT(timestep_minutes), MEMBER_MAPPING_FLOAT(timestep_hours), MEMBER_MAPPING_FLOAT(timewindow),
	MEMBER_MAPPING_FLOAT(Fixed_load1_scalar_lower), MEMBER_MAPPING_FLOAT(Fixed_load1_scalar_upper), MEMBER_MAPPING_FLOAT(Fixed_load1_scalar_step),
	MEMBER_MAPPING_FLOAT(Fixed_load2_scalar_lower), MEMBER_MAPPING_FLOAT(Fixed_load2_scalar_upper), MEMBER_MAPPING_FLOAT(Fixed_load2_scalar_step),
	MEMBER_MAPPING_FLOAT(Flex_load_max_lower), MEMBER_MAPPING_FLOAT(Flex_load_max_upper), MEMBER_MAPPING_FLOAT(Flex_load_max_step),
	MEMBER_MAPPING_FLOAT(Mop_load_max_lower), MEMBER_MAPPING_FLOAT(Mop_load_max_upper), MEMBER_MAPPING_FLOAT(Mop_load_max_step),
	MEMBER_MAPPING_FLOAT(ScalarRG1_lower), MEMBER_MAPPING_FLOAT(ScalarRG1_upper), MEMBER_MAPPING_FLOAT(ScalarRG1_step),
	MEMBER_MAPPING_FLOAT(ScalarRG2_lower), MEMBER_MAPPING_FLOAT(ScalarRG2_upper), MEMBER_MAPPING_FLOAT(ScalarRG2_step),
	MEMBER_MAPPING_FLOAT(ScalarRG3_lower), MEMBER_MAPPING_FLOAT(ScalarRG3_upper), MEMBER_MAPPING_FLOAT(ScalarRG3_step),
	MEMBER_MAPPING_FLOAT(ScalarRG4_lower), MEMBER_MAPPING_FLOAT(ScalarRG4_upper), MEMBER_MAPPING_FLOAT(ScalarRG4_step),
	MEMBER_MAPPING_FLOAT(ScalarHL1_lower), MEMBER_MAPPING_FLOAT(ScalarHL1_upper), MEMBER_MAPPING_FLOAT(ScalarHL1_step),
	MEMBER_MAPPING_FLOAT(ScalarHYield1_lower), MEMBER_MAPPING_FLOAT(ScalarHYield1_upper), MEMBER_MAPPING_FLOAT(ScalarHYield1_step),
	MEMBER_MAPPING_FLOAT(ScalarHYield2_lower), MEMBER_MAPPING_FLOAT(ScalarHYield2_upper), MEMBER_MAPPING_FLOAT(ScalarHYield2_step),
	MEMBER_MAPPING_FLOAT(ScalarHYield3_lower), MEMBER_MAPPING_FLOAT(ScalarHYield3_upper), MEMBER_MAPPING_FLOAT(ScalarHYield3_step),
	MEMBER_MAPPING_FLOAT(ScalarHYield4_lower), MEMBER_MAPPING_FLOAT(ScalarHYield4_upper), MEMBER_MAPPING_FLOAT(ScalarHYield4_step),
	MEMBER_MAPPING_FLOAT(GridImport_lower), MEMBER_MAPPING_FLOAT(GridImport_upper), MEMBER_MAPPING_FLOAT(GridImport_step),
	MEMBER_MAPPING_FLOAT(GridExport_lower), MEMBER_MAPPING_FLOAT(GridExport_upper), MEMBER_MAPPING_FLOAT(GridExport_step),
	MEMBER_MAPPING_FLOAT(Import_headroom_lower), MEMBER_MAPPING_FLOAT(Import_headroom_upper), MEMBER_MAPPING_FLOAT(Import_headroom_step),
	MEMBER_MAPPING_FLOAT(Export_headroom_lower), MEMBER_MAPPING_FLOAT(Export_headroom_upper), MEMBER_MAPPING_FLOAT(Export_headroom_step),
	MEMBER_MAPPING_FLOAT(ESS_charge_power_lower), MEMBER_MAPPING_FLOAT(ESS_charge_power_upper), MEMBER_MAPPING_FLOAT(ESS_charge_power_step),
	MEMBER_MAPPING_FLOAT(ESS_discharge_power_lower), MEMBER_MAPPING_FLOAT(ESS_discharge_power_upper), MEMBER_MAPPING_FLOAT(ESS_discharge_power_step),
	MEMBER_MAPPING_FLOAT(ESS_capacity_lower), MEMBER_MAPPING_FLOAT(ESS_capacity_upper), MEMBER_MAPPING_FLOAT(ESS_capacity_step),
	MEMBER_MAPPING_FLOAT(ESS_RTE_lower), MEMBER_MAPPING_FLOAT(ESS_RTE_upper), MEMBER_MAPPING_FLOAT(ESS_RTE_step),
	MEMBER_MAPPING_FLOAT(ESS_aux_load_lower), MEMBER_MAPPING_FLOAT(ESS_aux_load_upper), MEMBER_MAPPING_FLOAT(ESS_aux_load_step),
	MEMBER_MAPPING_FLOAT(ESS_start_SoC_lower), MEMBER_MAPPING_FLOAT(ESS_start_SoC_upper), MEMBER_MAPPING_FLOAT(ESS_start_SoC_step),
	MEMBER_MAPPING_INT(ESS_charge_mode_lower), MEMBER_MAPPING_INT(ESS_charge_mode_upper),
	MEMBER_MAPPING_INT(ESS_discharge_mode_lower), MEMBER_MAPPING_INT(ESS_discharge_mode_upper),
	MEMBER_MAPPING_FLOAT(import_kWh_price),
	MEMBER_MAPPING_FLOAT(export_kWh_price),
	MEMBER_MAPPING_FLOAT(time_budget_min), MEMBER_MAPPING_INT(target_max_concurrency),
	MEMBER_MAPPING_FLOAT(CAPEX_limit), MEMBER_MAPPING_FLOAT(OPEX_limit)
};


// Define macros to simplify creating the mapping for each struct member
#define OUT_MEMBER_MAPPING_FLOAT(member) {#member, [](const OutputValues& s) -> float { return s.member; }, nullptr}
#define OUT_MEMBER_MAPPING_INT(member) {#member, nullptr, [](const OutputValues& s) -> int { return s.member; }}

OutMemberMapping OutMemberMappings[] = {
	OUT_MEMBER_MAPPING_FLOAT(maxVal),
	OUT_MEMBER_MAPPING_FLOAT(minVal),
	OUT_MEMBER_MAPPING_FLOAT(meanVal),
	OUT_MEMBER_MAPPING_FLOAT(est_seconds),
	OUT_MEMBER_MAPPING_FLOAT(est_hours),
	OUT_MEMBER_MAPPING_INT(num_scenarios),
	OUT_MEMBER_MAPPING_FLOAT(time_taken),
	OUT_MEMBER_MAPPING_FLOAT(Fixed_load1_scalar), OUT_MEMBER_MAPPING_FLOAT(Fixed_load2_scalar), OUT_MEMBER_MAPPING_FLOAT(Flex_load_max), OUT_MEMBER_MAPPING_FLOAT(Mop_load_max),
	OUT_MEMBER_MAPPING_FLOAT(ScalarRG1), OUT_MEMBER_MAPPING_FLOAT(ScalarRG2), OUT_MEMBER_MAPPING_FLOAT(ScalarRG3), OUT_MEMBER_MAPPING_FLOAT(ScalarRG4),
	OUT_MEMBER_MAPPING_FLOAT(ScalarHL1), OUT_MEMBER_MAPPING_FLOAT(ScalarHYield1), OUT_MEMBER_MAPPING_FLOAT(ScalarHYield2), OUT_MEMBER_MAPPING_FLOAT(ScalarHYield3), OUT_MEMBER_MAPPING_FLOAT(ScalarHYield4),
	OUT_MEMBER_MAPPING_FLOAT(GridImport), OUT_MEMBER_MAPPING_FLOAT(GridExport), OUT_MEMBER_MAPPING_FLOAT(Import_headroom), OUT_MEMBER_MAPPING_FLOAT(Export_headroom),
	OUT_MEMBER_MAPPING_FLOAT(ESS_charge_power), OUT_MEMBER_MAPPING_FLOAT(ESS_discharge_power), OUT_MEMBER_MAPPING_FLOAT(ESS_capacity), OUT_MEMBER_MAPPING_FLOAT(ESS_RTE), OUT_MEMBER_MAPPING_FLOAT(ESS_aux_load), OUT_MEMBER_MAPPING_FLOAT(ESS_start_SoC),
	OUT_MEMBER_MAPPING_INT(ESS_charge_mode), OUT_MEMBER_MAPPING_INT(ESS_discharge_mode),
	OUT_MEMBER_MAPPING_FLOAT(import_kWh_price), OUT_MEMBER_MAPPING_FLOAT(export_kWh_price),
	OUT_MEMBER_MAPPING_FLOAT(CAPEX), OUT_MEMBER_MAPPING_FLOAT(annualised), OUT_MEMBER_MAPPING_FLOAT(scenario_cost_balance), OUT_MEMBER_MAPPING_FLOAT(payback_horizon), OUT_MEMBER_MAPPING_FLOAT(scenario_carbon_balance),
	OUT_MEMBER_MAPPING_INT(CAPEX_index), OUT_MEMBER_MAPPING_INT(annualised_index), OUT_MEMBER_MAPPING_INT(scenario_cost_balance_index), OUT_MEMBER_MAPPING_INT(payback_horizon_index), OUT_MEMBER_MAPPING_INT(scenario_carbon_balance_index),
	OUT_MEMBER_MAPPING_INT(scenario_index),
	OUT_MEMBER_MAPPING_INT(num_scenarios), OUT_MEMBER_MAPPING_FLOAT(est_hours), OUT_MEMBER_MAPPING_FLOAT(est_seconds)
};

std::vector<float> readCSVColumn(const std::filesystem::path& filename, int column) {
	std::ifstream file(filename);
	std::vector<float> columnValues;
	std::string line;
	bool columnHasValues = false;

	if (!file.is_open()) {
		std::cerr << "Could not open the file!" << std::endl;
		return columnValues; // Return empty vector
	}

	// Skip the header row
	std::getline(file, line);

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
			row.push_back(cell);
		}

		// If the row ends with a comma, add an empty string to the row (signifying an empty column)
		if (line.back() == ',') {
			row.push_back("");
		}

		// Convert the value from the specified column to float and store it in the vector
		int column_1 = column - 1;
		if (row.size() > column_1) {
			if (!row[column_1].empty()) {
				columnHasValues = true;
			}

			if (isValidFloat(row[column_1])) {
				try {
					columnValues.push_back(std::stof(row[column_1]));
				}
				catch (...) {
					std::cerr << "Unknown exception at line: " << line << '\n';
					columnValues.push_back(std::nanf(""));
				}
			}
			else {
				//std::cerr << "Warning: invalid data at line: " << line << '\n';
				columnValues.push_back(std::nanf(""));
			}
		}
		else {
			std::cerr << "Warning: insufficient columns at line: " << line << '\n';
			columnValues.push_back(std::nanf(""));
		}
	}

	if (!columnHasValues) {
		std::fill(columnValues.begin(), columnValues.end(), 0.0f);
	}

	return columnValues;
}

bool isValidFloat(const std::string& str) {
	std::stringstream sstr(str);
	float f;
	return !(sstr >> f).fail() && (sstr >> std::ws).eof();
}


void writeToCSV(std::filesystem::path absfilepath, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumns) {
	if (dataColumns.empty()) {
		std::cerr << "Data columns are empty!" << std::endl;
		return;
	}

	std::size_t numColumns = dataColumns.size();
	std::size_t numRows = dataColumns[0].second.size();

	// Check if all vectors are of the same length
	for (const auto& dataColumn : dataColumns) {
		if (dataColumn.second.size() != numRows) {
			std::cerr << "Data columns are not of the same length!" << std::endl;
			std::cerr << "Number of rows is:" << dataColumns[0].second.size() << std::endl;
			std::cerr << "Data column is:" << dataColumn.second.size() << std::endl;
			return;
		}
	}

	std::ofstream outFile(absfilepath);

	if (!outFile.is_open()) {
		std::cerr << "Failed to open the output file!" << std::endl;
		return;
	}

	// Write column names as the first row
	for (std::size_t i = 0; i < numColumns; ++i) {
		outFile << dataColumns[i].first;
		if (i < numColumns - 1) {
			outFile << ",";
		}
	}
	outFile << std::endl;

	// Write data rows
	for (std::size_t i = 0; i < numRows; ++i) {
		for (std::size_t j = 0; j < numColumns; ++j) {
			outFile << dataColumns[j].second[i];
			if (j < numColumns - 1) {
				outFile << ",";
			}
		}
		outFile << std::endl;
	}

	outFile.close();
}

void writeResultsToCSV(std::filesystem::path filepath, const std::vector<SimulationResult>& results)
{
	std::ofstream outFile(filepath);

	// TODO exception instead
	if (!outFile.is_open()) {
		std::cerr << "Failed to open the output file!" << std::endl;
		return;
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
		outFile << result.heatload << ",";
		outFile << result.scaled_heatload << ",";
		outFile << result.Electrical_load_scaled_heat_yield << ",";
		outFile << result.Heat_shortfall << ",";
		outFile << result.Heat_surplus;  // no comma
		outFile << '\n';
	}
}



void appendCSV(std::filesystem::path filepath, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumns) {
	if (dataColumns.empty()) {
		std::cerr << "Data columns are empty!" << std::endl;
		return;
	}

	std::size_t numColumns = dataColumns.size();
	std::size_t numRows = dataColumns[0].second.size();

	// Check if all vectors are of the same length
	for (const auto& dataColumn : dataColumns) {
		if (dataColumn.second.size() != numRows) {
			std::cerr << "Data columns are not of the same length!" << std::endl;
			std::cerr << "Number of rows is:" << dataColumns[0].second.size() << std::endl;
			std::cerr << "Data column is:" << dataColumn.second.size() << std::endl;
			return;
		}
	}

	// Open file in append mode
	std::ofstream outFile(filepath, std::ios::app);

	if (!outFile.is_open()) {
		std::cerr << "Failed to open the output file!" << std::endl;
		return;
	}

	// Check if the file is empty; if it is, write the headers
	outFile.seekp(0, std::ios::end);
	bool isEmpty = !outFile.tellp();
	if (isEmpty) {
		// Write column names as the first row
		for (std::size_t i = 0; i < numColumns; ++i) {
			outFile << dataColumns[i].first;
			if (i < numColumns - 1) {
				outFile << ",";
			}
		}
		outFile << std::endl;
	}

	// Write data rows
	for (std::size_t i = 0; i < numRows; ++i) {
		for (std::size_t j = 0; j < numColumns; ++j) {
			outFile << dataColumns[j].second[i];
			if (j < numColumns - 1) {
				outFile << ",";
			}
		}
		outFile << std::endl;
	}

	outFile.close();
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

nlohmann::json handleJsonConversion(const InputValues& inputValues, std::filesystem::path inputDir) {
	// Aim: to export 'inputvalues' to a json file that can be read e.g. as a Python dict, s.t. other EPL software can use this as an input

	nlohmann::json jsonObj = inputToJson(inputValues);
	std::filesystem::path paramPath = inputDir / "parameters.json";
	writeJsonToFile(jsonObj, paramPath);

	nlohmann::json converted_json = convert_to_ranges(jsonObj);
	std::filesystem::path paramGroupedPath = inputDir / "parameters_grouped.json";
	writeJsonToFile(converted_json, paramGroupedPath);

	std::cout << "JSON file written successfully!" << std::endl;

	return converted_json;

}

void writeJsonToFile(const nlohmann::json& jsonObj, std::filesystem::path filepath) {
	try {
		std::ofstream file(filepath);
		file << jsonObj.dump(4);  // The "4" argument adds pretty-printing with indentation
		file.close();
	}
	catch (const std::exception e) {
		std::cerr << "Error: " << e.what() << std::endl;
	}
}
	
