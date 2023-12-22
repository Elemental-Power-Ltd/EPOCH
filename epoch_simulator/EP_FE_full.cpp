// EP_FE_full.cpp : Defines the entry point for the application.
//
#include <iostream> 
#include <chrono> // this is run time profiler
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <utility>
#include <xmmintrin.h> 
#include <thread>
#include <future>
#include <numeric>
#include <algorithm>
#include <limits>
#define NOMINMAX
#include <windows.h>
#include <map>
#include <mutex>
#include <queue>
#include <condition_variable>
#include <optional>
#include "FileIO.h"
#include "Config.h"
#include "Timeseries.h" // this is the Timeseries.h header file that contains class declarations of the timeseries vector
#include "Assets.h" // this the Assets.h header file that contains class declarations of the assets
#include "Eload.h" // Electrical load data
#include "RGen.h" // Local renewable yield
#include "Grid.h" // Grid connection data and cals
#include "Hload.h" // Heat load data
#include "Costs.h"
//#include "optimisation.cpp"
//#include "EP_BE_body.cpp"
#include "framework.h"
#include "Threadsafe.h"
#include "EP_FE_full.h"


/* ==== JSM CODE HERE ======================================================================*/
#include <functional>
#include "json.hpp"
#include <regex>
/*==========================================================================================*/

#define MAX_LOADSTRING 100
#define ID_BUTTON0 0
#define ID_BUTTON1 1 
#define ID_BUTTON2 200

#define ID_TEXTBOX2 2
#define ID_TEXTBOX3 3
#define ID_TEXTBOX4 4
#define ID_TEXTBOX5 5
#define ID_TEXTBOX6 6
#define ID_TEXTBOX7 7
#define ID_TEXTBOX8 8
#define ID_TEXTBOX9 9
#define ID_TEXTBOX10 10
#define ID_TEXTBOX11 11 
#define ID_TEXTBOX12 12
#define ID_TEXTBOX13 13
#define ID_TEXTBOX14 14
#define ID_TEXTBOX15 15
#define ID_TEXTBOX16 16
#define ID_TEXTBOX17 17
#define ID_TEXTBOX18 18
#define ID_TEXTBOX19 19
#define ID_TEXTBOX20 20
#define ID_TEXTBOX21 21 
#define ID_TEXTBOX22 22
#define ID_TEXTBOX23 23
#define ID_TEXTBOX24 24
#define ID_TEXTBOX25 25
#define ID_TEXTBOX26 26
#define ID_TEXTBOX27 27
#define ID_TEXTBOX28 28
#define ID_TEXTBOX29 29
#define ID_TEXTBOX30 30
#define ID_TEXTBOX31 31 
#define ID_TEXTBOX32 32
#define ID_TEXTBOX33 33
#define ID_TEXTBOX34 34
#define ID_TEXTBOX35 35
#define ID_TEXTBOX36 36
#define ID_TEXTBOX37 37
#define ID_TEXTBOX38 38
#define ID_TEXTBOX39 39
#define ID_TEXTBOX40 40
#define ID_TEXTBOX41 41 
#define ID_TEXTBOX42 42
#define ID_TEXTBOX43 43
#define ID_TEXTBOX44 44
#define ID_TEXTBOX45 45
#define ID_TEXTBOX46 46
#define ID_TEXTBOX47 47
#define ID_TEXTBOX48 48
#define ID_TEXTBOX49 49
#define ID_TEXTBOX50 50
#define ID_TEXTBOX51 51 
#define ID_TEXTBOX52 52
#define ID_TEXTBOX53 53
#define ID_TEXTBOX54 54
#define ID_TEXTBOX55 55
#define ID_TEXTBOX56 56
#define ID_TEXTBOX57 57
#define ID_TEXTBOX58 58
#define ID_TEXTBOX59 59
#define ID_TEXTBOX60 60
#define ID_TEXTBOX61 61 
#define ID_TEXTBOX62 62
#define ID_TEXTBOX63 63
#define ID_TEXTBOX64 64
#define ID_TEXTBOX65 65
#define ID_TEXTBOX66 66
#define ID_TEXTBOX67 67
#define ID_TEXTBOX68 68
#define ID_TEXTBOX69 69
#define ID_TEXTBOX70 70
#define ID_TEXTBOX71 71
#define ID_TEXTBOX72 72
#define ID_TEXTBOX73 73
#define ID_TEXTBOX74 74
#define ID_TEXTBOX75 75
#define ID_TEXTBOX76 76
#define ID_TEXTBOX77 77
#define ID_TEXTBOX78 78
#define ID_TEXTBOX79 79
#define ID_TEXTBOX71 80
#define ID_TEXTBOX72 81
#define ID_TEXTBOX73 82
#define ID_TEXTBOX74 83
#define ID_TEXTBOX75 84
#define ID_TEXTBOX76 85
#define ID_TEXTBOX77 86
#define ID_TEXTBOX78 87
#define ID_TEXTBOX79 88
#define ID_TEXTBOX80 89
#define ID_TEXTBOX81 90
#define ID_TEXTBOX82 92
#define ID_TEXTBOX83 93
#define ID_TEXTBOX84 94
#define ID_TEXTBOX85 95
#define ID_TEXTBOX86 96
#define ID_TEXTBOX87 97
#define ID_TEXTBOX88 98
#define ID_TEXTBOX89 99

#define ID_TEXTBOX200 200

#define ID_OUTPUT1 99
#define ID_OUTPUT2 100
#define ID_OUTPUT3 101
#define ID_OUTPUT4 102
#define ID_OUTPUT5 103
#define ID_OUTPUT6 104
#define ID_OUTPUT7 105
#define ID_OUTPUT8 106
#define ID_OUTPUT9 107
#define ID_OUTPUT10 108
#define ID_OUTPUT11 109
#define ID_OUTPUT12 110
#define ID_OUTPUT13 111
#define ID_OUTPUT14 112
#define ID_OUTPUT15 113
#define ID_OUTPUT16 114
#define ID_OUTPUT17 115
#define ID_OUTPUT18 116
#define ID_OUTPUT19 117
#define ID_OUTPUT20 118
#define ID_OUTPUT21 119
#define ID_OUTPUT22 120
#define ID_OUTPUT23 121
#define ID_OUTPUT24 122
#define ID_OUTPUT25 123
#define ID_OUTPUT26 124
#define ID_OUTPUT27 125
#define ID_OUTPUT28 126
#define ID_OUTPUT29 127
#define ID_OUTPUT30 128
#define ID_OUTPUT31 129


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

// Define a struct that represents the mapping between member names and pointers
struct MemberMapping {
	const char* name;
	std::function<float(const InputValues&)> getFloat;
	std::function<int(const InputValues&)> getInt;
};

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

// Custom function to convert a struct to a JSON object
nlohmann::json structToJson(const InputValues& data, const MemberMapping mappings[], size_t Size) {
	nlohmann::json jsonObj;
	for (size_t i = 0; i < Size; ++i) {
		const auto& mapping = mappings[i];
		if (mapping.getFloat) {
			jsonObj[mapping.name] = mapping.getFloat(data);
		}
		else if (mapping.getInt) {
			jsonObj[mapping.name] = mapping.getInt(data);
		}
	}
	return jsonObj;
}

struct OutMemberMapping {
	const char* name;
	std::function<float(const OutputValues&)> getFloat;
	std::function<int(const OutputValues&)> getInt;
};

// Define macros to simplify creating the mapping for each struct member
#define OUT_MEMBER_MAPPING_FLOAT(member) {#member, [](const OutputValues& s) -> float { return s.member; }, nullptr}
#define OUT_MEMBER_MAPPING_INT(member) {#member, nullptr, [](const OutputValues& s) -> int { return s.member; }}

OutMemberMapping OutmemberMappings[] = {
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

// Custom function to convert a struct to a JSON object
nlohmann::json structToJsonOut(const OutputValues& data, const OutMemberMapping mappings[], size_t Size) {
	nlohmann::json jsonObj;
	for (size_t i = 0; i < Size; ++i) {
		const auto& mapping = mappings[i];
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


bool isValidFloat(const std::string& str);

std::vector<float> readCSVColumn(const std::string& filename, int column) {
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

// Define the isValidFloat function here or link to its definition
bool isValidFloat(const std::string& str) {
	std::stringstream sstr(str);
	float f;
	return !(sstr >> f).fail() && (sstr >> std::ws).eof();
}

// define static function to write in CSV.data with header as the names
void writeToCSV(std::string absfilepath, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumns) {
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

void appendCSV(std::string absfilepath, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumns) {
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
	std::ofstream outFile(absfilepath, std::ios::app);

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

void appendDataColumns(std::vector<std::pair<std::string, std::vector<float>>>& cumDataColumns,
	const std::vector<std::pair<std::string, std::vector<float>>>& dataColumnsN) {
	for (const auto& dataColumnN : dataColumnsN) {
		// Try to find the column in cumdataColumns
		auto it = std::find_if(cumDataColumns.begin(), cumDataColumns.end(),
			[&dataColumnN](const std::pair<std::string, std::vector<float>>& cumColumn) {
				return cumColumn.first == dataColumnN.first;
			});

		if (it != cumDataColumns.end()) {
			// If column exists, append the data
			it->second.insert(it->second.end(), dataColumnN.second.begin(), dataColumnN.second.end());
		}
		else {
			// If column doesn't exist, add the new column and its data
			cumDataColumns.push_back(dataColumnN);
		}
	}
}

std::tuple<float, float, float> getColumnStats(const std::vector<std::pair<std::string, std::vector<float>>>& CustomDataTable) {
	const std::string targetColumnName = "Calculative execution time (s)";

	// Find the target column
	auto it = std::find_if(CustomDataTable.begin(), CustomDataTable.end(),
		[&](const std::pair<std::string, std::vector<float>>& column) {
			return column.first == targetColumnName;
		});

	if (it == CustomDataTable.end()) {
		std::cerr << "Column not found!" << std::endl;
		return std::make_tuple(0.0f, 0.0f, 0.0f); // Return zeros if column not found
	}

	// Filter the non-zero values into a separate vector
	std::vector<float> nonZeroValues;
	std::copy_if(it->second.begin(), it->second.end(), std::back_inserter(nonZeroValues), [](float value) {
		return value != 0.0f;
		});

	// If there are no non-zero values, return zeros
	if (nonZeroValues.empty()) {
		return std::make_tuple(0.0f, 0.0f, 0.0f);
	}

	float maxVal = *std::max_element(nonZeroValues.begin(), nonZeroValues.end());
	float minVal = *std::min_element(nonZeroValues.begin(), nonZeroValues.end());
	float meanVal = std::accumulate(nonZeroValues.begin(), nonZeroValues.end(), 0.0f) / nonZeroValues.size();

	return std::make_tuple(maxVal, minVal, meanVal);
}

using CustomDataTable = std::vector<std::pair<std::string, std::vector<float>>>;

void appendSumToDataTable(CustomDataTable& outTable, CustomDataTable& singleTable) {
	for (auto& entry : singleTable) {
		// Find the matching key in outTable
		auto it = std::find_if(outTable.begin(), outTable.end(),
			[&entry](const std::pair<std::string, std::vector<float>>& outputPair) {
				return entry.first == outputPair.first;
			});

		// If the key is found, append the sum of the singleTable's vector to the matching outTable's vector
		if (it != outTable.end()) {
			float sum = std::accumulate(entry.second.begin(), entry.second.end(), 0.0f);
			it->second.push_back(sum);
		}
	}
}

CustomDataTable SumDataTable(const CustomDataTable& dataTable) {
	CustomDataTable result;
	result.reserve(dataTable.size()); // Preallocate memory

	//std::cout << "Input DataTable Size: " << dataTable.size() << std::endl;

	for (const auto& item : dataTable) {
		//std::cout << "Processing: " << item.first << ", Vector Size: " << item.second.size() << std::endl;
		float sum = std::accumulate(item.second.begin(), item.second.end(), 0.0f);
		//std::cout << "Sum: " << sum << std::endl;
		result.emplace_back(item.first, std::vector<float>{sum});
	}

	return result;
}

std::vector<float> getDataForKey(const CustomDataTable& table, const std::string& key) {
	for (const auto& entry : table) {
		if (entry.first == key) {
			return entry.second;
		}
	}
	// Return an empty vector if key not found
	return {};
}

struct paramRange {
	std::string name;
	float min, max, step;
};

void workerFunction(SafeQueue<std::map<std::string, float>>& taskQueue) {
	std::map<std::string, float> task;
	while (taskQueue.pop(task)) {
		// Process the task (param_slice)
		// ...

		// Check if there are more tasks to process
		if (taskQueue.empty()) {
			break;
		}
	}
}

int generateTasks(const std::vector<paramRange>& paramGrid, SafeQueue<std::vector<std::pair<std::string, float>>>& taskQueue) 

{
	int j = 0;
/* Use an iterative approach as follows */
	size_t numParameters = paramGrid.size();
	if (numParameters == 0) return j;

	// Vectors to keep track of the current indices and values for each parameter
	std::vector<size_t> indices(numParameters, 0);
	std::vector<float> current_values(numParameters, 0);

	// Initialize current values to the min values
	for (size_t i = 0; i < numParameters; ++i) {
		current_values[i] = paramGrid[i].min;
	}

	bool finished = false;

	while (!finished) {
		j++;
		//std::cout << j << " scenarios" << std::endl;

		// Create a new task with the current combination of parameters
		std::vector<std::pair<std::string, float>> currentTask;
		for (size_t i = 0; i < numParameters; ++i) {
			currentTask.emplace_back(paramGrid[i].name, current_values[i]);
		}
		// Add task index to currentTask, to keep track of ordering through parallelisation
		currentTask.emplace_back("Parameter index", j);
		// Push the new task onto the task queue
		taskQueue.push(currentTask);

		// Move to the next combination
		for (size_t i = 0; i < numParameters; ++i) {
			// If step is 0, default it to cover the entire range as one step
			float step = paramGrid[i].step != 0 ? paramGrid[i].step : (paramGrid[i].max - paramGrid[i].min);
			// Guard against non-positive step sizes
			if (step <= 0) {
				step = 1;
			}

			current_values[i] += step;

			if (current_values[i] > paramGrid[i].max) {
				if (i == numParameters - 1) {
					finished = true;
					break;
				}
				else {
					current_values[i] = paramGrid[i].min;  // Reset this parameter and carry '1' to the next
					// No need to break, continue to update the next parameter
				}
			}
			else {
				break; // Found the next combination, break out of the loop
			}
		}
	}
	return j;
}

std::vector<std::pair<std::string, float>> TaskRecall(const std::vector<paramRange>& paramGrid, int index)

{
	// CAUTION THIS SHOULD ONLY BE CALLED IN THE CONTEXT OF "RECALL" AS THE taskQueue is already written in the main optimisation using the generateTask function

	SafeQueue<std::vector<std::pair<std::string, float>>> taskQueue;

	std::vector<std::pair<std::string, float>> paramSlice;

	/* Use an iterative approach as follows */
	size_t numParameters = paramGrid.size();
	if (numParameters == 0) return paramSlice;

	// Vectors to keep track of the current indices and values for each parameter
	std::vector<size_t> indices(numParameters, 0);
	std::vector<float> current_values(numParameters, 0);

	// Initialize current values to the min values
	for (size_t i = 0; i < numParameters; ++i) {
		current_values[i] = paramGrid[i].min;
	}

	bool finished = false;

	int j = 0;

	while (!finished) {
		j++; // this set j = 1 to align with paramslice number

		// Create a new task with the current combination of parameters
		std::vector<std::pair<std::string, float>> currentTask;
		for (size_t i = 0; i < numParameters; ++i) {
			currentTask.emplace_back(paramGrid[i].name, current_values[i]);
		}

		// Add task index to currentTask, to keep track of ordering through parallelisation
		currentTask.emplace_back("Parameter index", j);

		// Push the new task onto the task queue
		taskQueue.push(currentTask);
		
		if (j == index)
		{
			paramSlice = currentTask;
			finished = true;
			return paramSlice;

		}
		// Move to the next combination
		for (size_t i = 0; i < numParameters; ++i) {
			// If step is 0, default it to cover the entire range as one step
			float step = paramGrid[i].step != 0 ? paramGrid[i].step : (paramGrid[i].max - paramGrid[i].min);
			// Guard against non-positive step sizes
			if (step <= 0) {
				step = 1;
			}

			current_values[i] += step;

			if (current_values[i] > paramGrid[i].max) {
				if (i == numParameters - 1) {
					finished = true;
					break;
				}
				else {
					current_values[i] = paramGrid[i].min;  // Reset this parameter and carry '1' to the next
					// No need to break, continue to update the next parameter
				}
			}
			else {
				break; // Found the next combination, break out of the loop
			}
		}
	}
	return paramSlice;
}

std::pair<float, float> findMinValueandIndex(const CustomDataTable& dataColumns, const std::string& columnName) {
	const std::vector<float>* targetColumn = nullptr;
	const std::vector<float>* paramIndexColumn = nullptr;

	// Find the target column and paramIndex column
	for (const auto& column : dataColumns) {
		if (column.first == columnName) {
			targetColumn = &column.second;
		}
		if (column.first == "Parameter index") {
			paramIndexColumn = &column.second;
		}
	}

	if (!targetColumn || !paramIndexColumn) {
		throw std::runtime_error("Specified column or Parameter index column not found");
	}

	if (targetColumn->size() != paramIndexColumn->size()) {
		throw std::runtime_error("Inconsistent data size between columns");
	}

	float minValue = std::numeric_limits<float>::max();
	float correspondingParamIndex = -1;

	for (size_t i = 0; i < targetColumn->size(); ++i) {
		if ((*targetColumn)[i] < minValue) {
			minValue = (*targetColumn)[i];
			correspondingParamIndex = (*paramIndexColumn)[i];
		}
	}

	return {minValue, correspondingParamIndex};
}

std::pair<float, float> findMaxValueandIndex(const CustomDataTable& dataColumns, const std::string& columnName) {
	const std::vector<float>* targetColumn = nullptr;
	const std::vector<float>* paramIndexColumn = nullptr;

	// Find the target column and paramIndex column
	for (const auto& column : dataColumns) {
		if (column.first == columnName) {
			targetColumn = &column.second;
		}
		if (column.first == "Parameter index") {
			paramIndexColumn = &column.second;
		}
	}

	if (!targetColumn || !paramIndexColumn) {
		throw std::runtime_error("Specified column or Parameter index column not found");
	}

	if (targetColumn->size() != paramIndexColumn->size()) {
		throw std::runtime_error("Inconsistent data size between columns");
	}

	// Initialize with the lowest possible float value
	float maxValue = std::numeric_limits<float>::lowest();
	float correspondingParamIndex = -1;

	for (size_t i = 0; i < targetColumn->size(); ++i) {
		// Compare to find the maximum value
		if ((*targetColumn)[i] > maxValue) {
			maxValue = (*targetColumn)[i];
			correspondingParamIndex = (*paramIndexColumn)[i];
		}
	}

	return { maxValue, correspondingParamIndex };
}


float findMinValue(const CustomDataTable& dataColumns, const std::string& columnName) {
	const std::vector<float>* targetColumn = nullptr;
	const std::vector<float>* paramIndexColumn = nullptr;

	// Find the target column and paramIndex column
	for (const auto& column : dataColumns) {
		if (column.first == columnName) {
			targetColumn = &column.second;
		}
		if (column.first == "Parameter index") {
			paramIndexColumn = &column.second;
		}
	}

	if (!targetColumn || !paramIndexColumn) {
		throw std::runtime_error("Specified column or Parameter index column not found");
	}

	if (targetColumn->size() != paramIndexColumn->size()) {
		throw std::runtime_error("Inconsistent data size between columns");
	}

	float minValue = std::numeric_limits<float>::max();
	float correspondingParamIndex = -1;

	for (size_t i = 0; i < targetColumn->size(); ++i) {
		if ((*targetColumn)[i] < minValue) {
			minValue = (*targetColumn)[i];
			correspondingParamIndex = (*paramIndexColumn)[i];
		}
	}

	return minValue;
}

float findMaxValue (const CustomDataTable& dataColumns, const std::string& columnName) {
	const std::vector<float>* targetColumn = nullptr;
	const std::vector<float>* paramIndexColumn = nullptr;

	// Find the target column and paramIndex column
	for (const auto& column : dataColumns) {
		if (column.first == columnName) {
			targetColumn = &column.second;
		}
		if (column.first == "Parameter index") {
			paramIndexColumn = &column.second;
		}
	}

	if (!targetColumn || !paramIndexColumn) {
		throw std::runtime_error("Specified column or Parameter index column not found");
	}

	if (targetColumn->size() != paramIndexColumn->size()) {
		throw std::runtime_error("Inconsistent data size between columns");
	}

	// Initialize with the lowest possible float value
	float maxValue = std::numeric_limits<float>::lowest();
	float correspondingParamIndex = -1;

	for (size_t i = 0; i < targetColumn->size(); ++i) {
		// Compare to find the maximum value
		if ((*targetColumn)[i] > maxValue) {
			maxValue = (*targetColumn)[i];
			correspondingParamIndex = (*paramIndexColumn)[i];
		}
	}

	return maxValue;
}


std::vector<std::pair<std::string, float>> ParamRecall(const std::vector<paramRange>& paramGrid, int index) { // now depreciated 11_12_2023
	std::vector<std::pair<std::string, float>> paramSlice;

	for (const auto& range : paramGrid) {
		int numValues = static_cast<int>((range.max - range.min) / range.step) + 1;
		int valueIndex = (index % numValues);
		float value = range.min + valueIndex * range.step;

		paramSlice.emplace_back(range.name, value);

		index /= numValues;
	}

	return paramSlice;
}

float computeMin(SafeQueue<CustomDataTable>& queue, const std::string& columnName) {
	float minValue = std::numeric_limits<float>::max();
	CustomDataTable dataTable;

	while (!queue.empty()) {
		if (queue.try_pop(dataTable)) {
			for (const auto& pair : dataTable) {
				if (pair.first == columnName) {
					for (float value : pair.second) {
						minValue = std::min(minValue, value);
					}
				}
			}
		}
		std::this_thread::sleep_for(std::chrono::seconds(1));
	}

	// Process the min and max values as needed
	return minValue;
}


float computeMax(SafeQueue<CustomDataTable>& queue, const std::string& columnName) {
	float maxValue = std::numeric_limits<float>::lowest();
	CustomDataTable dataTable;

	while (!queue.empty()) {
		if (queue.try_pop(dataTable)) {
			for (const auto& pair : dataTable) {
				if (pair.first == columnName) {
					for (float value : pair.second) {
						maxValue = std::max(maxValue, value);
					}
				}
			}
		}
		std::this_thread::sleep_for(std::chrono::seconds(1));// Optionally, add a small sleep here to reduce CPU usage
	}

	// Process the min and max values as needed
	return maxValue;
}

CustomDataTable scenario(CustomDataTable inputdata, std::vector<std::pair<std::string, float>> paramSlice)
{
	// REMOVE FOLLOWING LINES -- THESE ARE USED TO READ Eload DATA FROM CSV; THIS DATA IS INCLUDED IN inputdata THOUGH
	//FileIO myFileIO;
	//std::string testpath = myFileIO.getEloadfilepath(); 
	//std::string absfilepath = myFileIO.getEloadfilepath();

	/*CALCULATIVE SECTION - START PROFILING */
	auto start = std::chrono::high_resolution_clock::now(); //start runtime clock

	CustomDataTable initial_alocation;

	initial_alocation.push_back({ "place holder", {0.0f, 0.0f, 0.0f} });

	Config myConfig; // initialise a config object with default data

	// Change the config parameters to the current set of values in the parameter grid
	for (size_t i = 0; i < paramSlice.size(); ++i) {
		if (myConfig.param_map_float.find(paramSlice[i].first) != myConfig.param_map_float.end()) {
			myConfig.set_param_float(paramSlice[i].first, paramSlice[i].second);
			//			myConfig.print_param_float(paramSlice[i].first);
		}
		else {
			myConfig.set_param_int(paramSlice[i].first, paramSlice[i].second);
			//			myConfig.print_param_int(paramSlice[i].first);
		}

	}

	int hours = myConfig.calculate_timesteps(); // number of hours is a float in case we need sub-hourly timewindows

	Eload MountEload(myConfig.getESS_aux_load()); //create a Eload object called Mount_eload and pass the total ESS aux_load to it

	std::vector<float> hotel_eload_data = getDataForKey(inputdata, "hotel_eload_data");
	std::vector<float> ev_eload_data = getDataForKey(inputdata, "ev_eload_data");
	std::vector<float> heatload_data = getDataForKey(inputdata, "heatload_data");
	std::vector<float> RGen_data_1 = getDataForKey(inputdata, "RGen_data_1");
	std::vector<float> RGen_data_2 = getDataForKey(inputdata, "RGen_data_2");
	std::vector<float> RGen_data_3 = getDataForKey(inputdata, "RGen_data_3");
	std::vector<float> RGen_data_4 = getDataForKey(inputdata, "RGen_data_4");

	year_TS hotel_eload(hours);
	hotel_eload.setTSvalues(hotel_eload_data);
	hotel_eload.scaleTSvalues(myConfig.getFixed_load1_scalar()); // scale the data
	MountEload.writeTS_Fix_load_1(hotel_eload); // set the values with the imported hotel load data

	year_TS ev_eload(hours);
	ev_eload.setTSvalues(ev_eload_data);
	ev_eload.scaleTSvalues(myConfig.getFixed_load2_scalar());
	MountEload.writeTS_Fix_load_2(ev_eload); // set the values with the imported hotel load data
	MountEload.calculateTS_ESS_aux_load(); // calculate ESS aux load 
	MountEload.calculateTotal_fix_load(); // Calculate total fixed load by adding TS together

	//year_TS fixed_eload(hours);
	//fixed_eload = MountEload.getTS_Total_fix_load(); // create a new timeseries of total fixed load

	// check the Rgen data is all of the same size.
	if (RGen_data_1.size() != RGen_data_2.size() || RGen_data_1.size() != RGen_data_3.size() || RGen_data_1.size() != RGen_data_4.size()) {
		std::cerr << "R_Gen vectors are not of the same size!" << std::endl;
		return initial_alocation;
	}

	RGen MountRGen; // Create RGen object called MountRGen 

	year_TS RGen_1(hours); //create Rgen TS objects
	year_TS RGen_2(hours);
	year_TS RGen_3(hours);
	year_TS RGen_4(hours);

	RGen_1.setTSvalues(RGen_data_1); // set the values with the imported RGen data
	RGen_1.scaleTSvalues(myConfig.getScalarRG1()); // scale RGen with ScalarRG1 in config
	MountRGen.writeTS_RGen_1(RGen_1); //send scaled values to RGen1

	RGen_2.setTSvalues(RGen_data_2);
	RGen_2.scaleTSvalues(myConfig.getScalarRG2());
	MountRGen.writeTS_RGen_2(RGen_2);

	RGen_3.setTSvalues(RGen_data_3);
	RGen_3.scaleTSvalues(myConfig.getScalarRG3());
	MountRGen.writeTS_RGen_3(RGen_3);

	RGen_4.setTSvalues(RGen_data_4);
	RGen_4.scaleTSvalues(myConfig.getScalarRG4());
	MountRGen.writeTS_RGen_4(RGen_4); //send scaled values to RGen2

	MountRGen.calculateTS_RGen_total();

	std::vector<float> RGen_total_vect = MountRGen.getTS_RGen_total().getData(); // create vector of total RGen for output

	// ESUM tab begin 

	MountEload.calculateTS_Target_high_load(myConfig.getFlex_load_max()); 	// Timeseries for target high-flex load									

	MountEload.calculateTS_Total_target_load(); // Add high-flex target load to total fixed load

	MountEload.calculateTS_Total_load(); // Subtract timeseries for (small) parasitic load of ESS

	// Add ESS to total target load 
	year_TS ESUM = year_TS::subtract(MountEload.getTS_Total_load(), MountRGen.getTS_RGen_total()); // Final ESUM (electrical acitivity) is Total load minus Rgen 
	//[NOTE: For now it empircally PROVES 3x faster to Keep ESUM as a separate standalone TS (rather than store it in MountEload object, perhaps as it is continually referenced in the main ESS loop?) 
	std::vector<float> ESUM_vect = ESUM.getData(); // ESUM output vector for reporting
	// ESUM tab end

	// ESS tab begin
	ESS MountBESS(myConfig.getESS_charge_power(), myConfig.getESS_discharge_power(),
		myConfig.getESS_capacity(), myConfig.getESS_RTE(),
		myConfig.getESS_aux_load(), myConfig.getESS_start_SoC()); // Create an object of Battery class with config data... any parameter not passed to constructor will get default value

	MountBESS.initialise_chargekWh_TS(); // calculate BESS begining energy
	//std::cout << "Battery charge level begins at: " << TS1_chargekWh << "kWh... the game is afoot! \n"; //console progress update, can remove this output for speed

//These are steps on ESS tab for Opportunitic BESS alg # 1 (Charge mode from Rgen/ Discharge mode = Before grid) IMPORTANT: BELOW FORMULAE ONLY VALID FOR HOUR TIMESTEPS WHERE 1kWH = 1kW
//1. Calculate ESS available Discharge Power in TS1: DB4 = MIN(ESS_StartSoC,ESS_DisPwr)
//2. Calculate ESS available Charge Power in TS1: CB4 = MIN((ESS_Cap-ESS_StartSoC)/ESS_RTE,ESS_ChPwr)
//3. Calculate "Discharge mode = before grid" in TS1:  IB4=IF(ESum!B4>0,MIN(Esum!B4,ESS!DB4),0) NOTE: Dependency on Esum tab step 1, currently, ESUM[0]
//4. Calculate "Charge mode = Rgen only" in TS1: EB4=IF(ESum!B4<0,MIN(-Esum!B4,ESS!CB4),0) NOTE: Dependency on Esum tab step 1, currently, -ESUM[0]
//5. Calculate BESS actions in TS1 (Charge = B4 / Discharge = AB4 )
//6. Apply RTE, and update SoC in "ESS resulting state of charge (SoC)" TS1: BB4 = ESS_StartSoC-(AB4+B4*ESS_RTE)
//7. For TS2, Calculate ESS available Discharge Power for TS2 based on final SoC in TS1 and max discharge power DC4=MIN(BB4,ESS_DisPwr) 
//8. For TS2, Calculate ESS available Charge Power for TS2 based on final SoC in TS1 and max charge power CC4=MIN(ESS_Cap-BB4)/ESS_RTE,ESS_ChPwr)
//9. For TS2, Calculate "Discharge mode = before" in TS2: IC4 = IF(ESum!C4>0,MIN(ESum!C4,ESS!DC4),0) NOTE: Dependency on Esum tab step 2, currently, ESUM[1]
//10.For TS2, Calculate "Charge mode = Rgen only" EC4 = IF(Esum!C4<0,MIN(-ESum!C4,ESS!CC4),0) NOTE: Dependency on Esum tab step 2, currently, ESUM[1]
//11.Calculate BESS actions in TS1 (Charge = C4 / Discharge = AC4)
//12.For TS2, Caculate BESS actions and update SoC in "ESS resulting state of charge (SoC)" BC4 = BB4+C4*ESS_RTE-AC4
//13.Repeat actions 7-13 for remaining TS in time window

	//These are steps on ESS tab for Opportunitic BESS alg # 1 (Charge mode from Rgen/ Discharge mode = Before grid) IMPORTANT: BELOW FORMULAE ONLY VALID FOR HOUR TIMESTEPS WHERE 1kWH = 1kW
	//1. Calculate ESS available Discharge Power in TS1: DB4 = MIN(ESS_StartSoC,ESS_DisPwr)
	MountBESS.initialise_TS_ESS_available_discharge_power(myConfig.getTimeStep_hours());

	//2. Calculate ESS available Charge Power in TS1: CB4 = MIN((ESS_Cap-ESS_StartSoC)/ESS_RTE,ESS_ChPwr)
	MountBESS.initialise_TS_ESS_available_charge_power(myConfig.getTimeStep_hours());

	//3. Calculate "Discharge mode = before grid" in TS1:  IB4=IF(ESum!B4>0,MIN(Esum!B4,ESS!DB4),0) NOTE: Dependency on Esum tab step 1, currently, ESUM[0]
	MountBESS.initialise_TS_ESS_before_grid_discharge(ESUM.getValue(0), myConfig.getTimeStep_hours());

	//4. Calculate "Charge mode = Rgen only" in TS1: EB4=IF(ESum!B4<0,MIN(-Esum!B4,ESS!CB4),0) NOTE: Dependency on Esum tab step 1, currently, -ESUM[0]
	MountBESS.initialise_TS_ESS_Rgen_only_charge(ESUM.getValue(0), myConfig.getTimeStep_hours());

	//5. Calculate BESS actions in TS1 (Charge = B4 / Discharge = AB4 )
	MountBESS.initialise_TS_ESS_discharge(myConfig.getTimeStep_hours()); // flag that other charge mode engaged.

	MountBESS.initialise_TS_ESS_charge(myConfig.getTimeStep_hours()); // flag that other charge mode engaged.

	//6. Apply RTE, and update SoC in "ESS resulting state of charge (SoC)" TS1: BB4 = ESS_StartSoC-(AB4+B4*ESS_RTE)
	MountBESS.initialise_TS_ESS_resulting_SoC(myConfig.getTimeStep_hours());

	// main loop for ESS
	for (int timestep = 2; timestep < 8760; timestep++)
	{
		////7. For TS2+, Calculate ESS available Discharge Power for TS2 based on final SoC in TS1 and max discharge power DC4=MIN(BB4,ESS_DisPwr) 
		MountBESS.calculate_TS_ESS_available_discharge_power(myConfig.getTimeStep_hours(), timestep);

		////8. For TS2+, Calculate ESS available Charge Power for TS2 based on final SoC in TS1 and max charge power CC4=MIN(ESS_Cap-BB4)/ESS_RTE,ESS_ChPwr)
		MountBESS.calculate_TS_ESS_available_charge_power(myConfig.getTimeStep_hours(), timestep);

		////9. For TS2+, Calculate "Discharge mode = before" in TS2: IC4 = IF(ESum!C4>0,MIN(ESum!C4,ESS!DC4),0) NOTE: Dependency on Esum tab step 2, currently, ESUM[1]
		MountBESS.calculate_TS_ESS_before_grid_discharge(ESUM.getValue(timestep - 1), myConfig.getTimeStep_hours(), timestep);

		////10.For TS2+, Calculate "Charge mode = Rgen only" EC4 = IF(Esum!C4<0,MIN(-ESum!C4,ESS!CC4),0) NOTE: Dependency on Esum tab step 2, currently, ESUM[1]
		MountBESS.calculate_TS_ESS_Rgen_only_charge(ESUM.getValue(timestep - 1), myConfig.getTimeStep_hours(), timestep);

		////11.Calculate BESS actions in TS1 (Charge = C4 / Discharge = AC4)
		MountBESS.set_TS_ESS_discharge(myConfig.getTimeStep_hours(), timestep);

		MountBESS.set_TS_ESS_charge(myConfig.getTimeStep_hours(), timestep);

		////12.For TS2, Caculate BESS actions and update SoC in "ESS resulting state of charge (SoC)" BC4 = BB4+C4*ESS_RTE-AC4
		MountBESS.calculate_TS_ESS_resulting_SoC(timestep, myConfig.getTimeStep_hours());

		//13.Repeat actions 7-13 for remaining TS in time window
	}
	//Grid steps: have created the required vectors from ESUM and ESS, just need to add them etc here. Need a new class GRID to do functionality

	//Calculate Pre-grid balance = ESum!B4+ESS!B4-ESS!AB4
	Grid MountGrid(myConfig.getGridImport(), myConfig.getGridExport(), myConfig.getImport_headroom(), myConfig.getExport_headroom());

	MountGrid.writeTS_Pre_grid_balance(year_TS::subtract(ESUM, MountBESS.getTS_ESS_discharge())); // first subtract discharge, as in AB4
	//MountGrid.getTS_Pre_grid_balance().addto(MountBESS.getTS_ESS_charge()); // then add TS_ESScharge

	MountGrid.writeTS_Pre_grid_balance(year_TS::add(MountBESS.getTS_ESS_charge(),MountGrid.getTS_Pre_grid_balance()));
	//MountGrid.writeTS_Pre_grid_balance(Pre_grid_balance);

	//Calculate Grid Import = IF(BB4>0,MIN(BB4,Grid_imp),0)
	MountGrid.calculateGridImport(myConfig.calculate_timesteps());

	//Calculate Grid Export = IF(BB4<0,MIN(-BB4,Grid_exp),0)
	MountGrid.calculateGridExport(myConfig.calculate_timesteps());

	//Calculate Post-grid balance = BB4-B4+AB4
	MountGrid.writeTS_Post_grid_balance(year_TS::subtract(MountGrid.getTS_Pre_grid_balance(), MountGrid.getTS_GridImport()));
	//MountGrid.getTS_Post_grid_balance().addto(MountGrid.getTS_GridExport());

	MountGrid.writeTS_Post_grid_balance(year_TS::add(MountGrid.getTS_GridExport(), MountGrid.getTS_Post_grid_balance()));

	//Calulate Pre-Flex Import shortfall = IF(CB>0, CB4, 0)
	MountGrid.calculatePre_flex_import_shortfall(myConfig.calculate_timesteps());

	//Calculate Pre-Mop Curtailed Export = IF(CB<0,-CB4,0)
	MountGrid.calculatePre_Mop_curtailed_Export(myConfig.calculate_timesteps());

	//Actual Import shortfall (load curtailment) = IF(DB4>ESum!DB4,DB4-ESum!DB4,0)
	MountGrid.calculateActual_import_shortfall(myConfig.calculate_timesteps(), myConfig.getFlex_load_max());

	//Actual Curtailed Export = IF(EB>ESum!EB4,EB4-ESum!EB4,0)
	MountGrid.calculateActual_curtailed_export(myConfig.calculate_timesteps(), myConfig.getMop_load_max());

	//Finally need to pass actual flex Eload info for heat calculation

	//Hsum steps
	//Heat load: HSUM tab
	Hload MountHload;

	MountHload.writeTS_Heatload(heatload_data);

	std::vector<float> heatload_vect = MountHload.getTS_Heatload().getData();

	//(heatload_data); // set the values with the imported hotel load data

	//Heat load
	//=XLOOKUP(($A31-1)*24+B$3,HLoad!$A$2:$A$8761,HLoad!$D$2:$D$8761,0,0)*ScalarHL1 // Just a way of wrangling into 365*24 in excel
	MountHload.getTS_Heatload().scaleTSvalues(myConfig.getScalarHL1());// scale with the main heat load scalar

	//Electrical Load scaled heat yield
	//ESum!BB4*ScalarHYield1+ESum!CB4*ScalarHYield2+Esum!KB4*ScalarHYield3+ESum!LB4*ScalarHYield4
	//

	MountHload.writeTS_Scaled_electrical_fix_heat_load_1(hotel_eload.getData());
	MountHload.writeTS_Scaled_electrical_fix_heat_load_2(ev_eload.getData());

	MountHload.scaleTS_Scaled_electrical_fix_heat_load_1(myConfig.getScalarHYield1()); //scale to heat yield scalar    
	MountHload.scaleTS_Scaled_electrical_fix_heat_load_2(myConfig.getScalarHYield2());

	//Actual_mop_load;// needs to be actual high flex load, calculated from Grid 
	Eload MountFlex;

	MountFlex.calculateActual_high_priority_load(myConfig.calculate_timesteps(), myConfig.getFlex_load_max(), MountGrid.getTS_Pre_flex_import_shortfall());
	MountFlex.calculateActual_low_priority_load(myConfig.calculate_timesteps(), myConfig.getMop_load_max(), MountGrid.getTS_Pre_Mop_curtailed_Export());

	//year_TS scaled_high_flex_heat = MountFlex.getTS_Actual_high_priority_load().scaleTSvalues_newTS(myConfig.getScalarHYield3());
	//year_TS scaled_low_flex_heat = MountFlex.getTS_Actual_low_priority_load().scaleTSvalues_newTS(myConfig.getScalarHYield4());

	MountHload.calculateElectrical_load_scaled_heat_yield(MountFlex.getTS_Actual_high_priority_load(), MountFlex.getTS_Actual_low_priority_load(), myConfig.getScalarHYield3(), myConfig.getScalarHYield4());

	//Heat shortfall
	//IF(B4>AB4,B4-AB4,0)
	MountHload.calculateHeat_shortfall(myConfig.calculate_timesteps());

	//Heat surplus
	//IF(B4<AB4,AB3-B4,0)
	MountHload.calculateHeat_surplus(myConfig.calculate_timesteps());

	//Data reporting
	std::vector<float> Total_load_vect = MountEload.getTS_Total_load().getData();
	//std::vector<float> ESUM_vect = ESUM.getData(); // this is created earlier to align with spreadsheet

	std::vector<float> ESS_available_discharge_power_vect = MountBESS.getTS_ESS_available_discharge_power().getData();
	std::vector<float> ESS_available_charge_power_vect = MountBESS.getTS_ESS_available_charge_power().getData();
	std::vector<float> TS_ESS_Rgen_only_charge_vect = MountBESS.getTS_ESS_Rgen_only_charge().getData();
	std::vector<float> TS_ESS_discharge_vect = MountBESS.getTS_ESS_discharge().getData();
	std::vector<float> TS_ESS_charge_vect = MountBESS.getTS_ESS_charge().getData();
	std::vector<float> TS_ESS_resulting_SoC_vect = MountBESS.getTS_ESS_resulting_SoC().getData();
	std::vector<float> TS_Pre_grid_balance_vect = MountGrid.getTS_Pre_grid_balance().getData();
	std::vector<float> TS_Grid_Import_vect = MountGrid.getTS_GridImport().getData();
	std::vector<float> TS_Grid_Export_vect = MountGrid.getTS_GridExport().getData();
	std::vector<float> TS_Post_grid_balance_vect = MountGrid.getTS_Post_grid_balance().getData();
	std::vector<float> TS_Pre_flex_import_shortfall_vect = MountGrid.getTS_Pre_flex_import_shortfall().getData();
	std::vector<float> TS_Pre_Mop_curtailed_export_vect = MountGrid.getTS_Pre_Mop_curtailed_Export().getData();
	std::vector<float> TS_Actual_import_shortfall_vect = MountGrid.getTS_Actual_import_shortfall().getData();
	std::vector<float> TS_Actual_curtailed_export_vect = MountGrid.getTS_Actual_curtailed_export().getData();
	std::vector<float> TS_Actual_high_priority_load_vect = MountFlex.getTS_Actual_high_priority_load().getData();
	std::vector<float> TS_Actual_low_priority_load_vect = MountFlex.getTS_Actual_low_priority_load().getData();
	std::vector<float> scaled_heatload_vect = MountHload.getTS_Heatload().getData();
	std::vector<float> Electrical_load_scaled_heat_yield_vect = MountHload.getTS_Electrical_load_scaled_heat_yield().getData();
	std::vector<float> TS_Heat_shortfall_vect = MountHload.getTS_Heat_shortfall().getData();
	std::vector<float> TS_Heat_surplus_vect = MountHload.getTS_Heat_surplus().getData();

	year_TS Runtime;
	//std::chrono::duration<double> double = elapsed.count();

	// Get parameter index
	year_TS paramIndex;
	float paramIndex_float;
	for (const auto& kv : paramSlice) {
		if (kv.first == "Parameter index") {
			paramIndex_float = static_cast<float>(kv.second);
		}
	}
	paramIndex.setValue(0, paramIndex_float);
	std::vector<float> paramIndex_vect = paramIndex.getData();

	//  Calculate infrastructure costs section
	Costs myCost;

	float ESS_PCS_CAPEX = myCost.calculate_ESS_PCS_CAPEX(std::max(myConfig.getESS_charge_power(), myConfig.getESS_discharge_power()));
	//std::cout << "MyCost ESS_PCS_CAPEX " << ESS_PCS_CAPEX << std::endl;

	float ESS_PCS_OPEX = myCost.calculate_ESS_PCS_OPEX(std::max(myConfig.getESS_charge_power(), myConfig.getESS_discharge_power()));
	//std::cout << "MyCost ESS_PCS_OPEX " << ESS_PCS_OPEX << std::endl;

	float ESS_ENCLOSURE_CAPEX = myCost.calculate_ESS_ENCLOSURE_CAPEX(myConfig.getESS_capacity());
	//std::cout << "MyCost ENCLOSURE_CAPEX " << ESS_ENCLOSURE_CAPEX << std::endl;

	float ESS_ENCLOSURE_OPEX = myCost.calculate_ESS_ENCLOSURE_OPEX(myConfig.getESS_capacity());
	//std::cout << "MyCost ENCLOSURE_OPEX " << ESS_ENCLOSURE_OPEX << std::endl;

	float ESS_ENCLOSURE_DISPOSAL = myCost.calculate_ESS_ENCLOSURE_DISPOSAL(myConfig.getESS_capacity());
	//std::cout << "MyCost ENCLOSURE_DISPOSAL " << ESS_ENCLOSURE_DISPOSAL << std::endl;

	float PV_kWp_total = myConfig.getScalarRG1() + myConfig.getScalarRG2() + myConfig.getScalarRG3() + myConfig.getScalarRG4();

	float PVpanel_CAPEX = myCost.calculate_PVpanel_CAPEX(PV_kWp_total);
	//std::cout << "PVpanel_CAPEX " << PVpanel_CAPEX << std::endl;

	float PVBoP_CAPEX = myCost.calculate_PVBoP_CAPEX(PV_kWp_total);
	//std::cout << "PVBoP_CAPEX " << PVBoP_CAPEX << std::endl;

	float PVroof_CAPEX = myCost.calculate_PVroof_CAPEX(0); // there is no roof mount in the mount project example, need to add to input parameters
	//std::cout << "PVBoP_CAPEX " << PVroof_CAPEX << std::endl;

	float PVground_CAPEX = myCost.calculate_PVground_CAPEX(myConfig.getScalarRG1() + myConfig.getScalarRG2() + myConfig.getScalarRG3() + myConfig.getScalarRG4()); // there is no roof mount in the mount project example, need to add to input parameters
	//std::cout << "PVground_CAPEX " << PVground_CAPEX << std::endl;

	float PV_OPEX = myCost.calculate_PV_OPEX(PV_kWp_total);
	//std::cout << "PV_OPEX " << PV_OPEX << std::endl;

	float EV_CP_Cost = myCost.calculate_EV_CP_cost(0, 3, 0, 0); // need to add num EV charge points to Config
	//std::cout << "MyCost EV_CP_COST " << EV_CP_Cost << std::endl;

	float EV_CP_install = myCost.calculate_EV_CP_install(0, 3, 0, 0); // need to add num EV charge points to Config
	//std::cout << "MyCost EV_CP_Install " << EV_CP_install << std::endl;

	float Grid_CAPEX = myCost.calculate_Grid_CAPEX(std::max(0, 0)); // need to add aditional grid capacity max (imp/exp) and out to Config
	//std::cout << "MyCost Grid_CAPEX " << Grid_CAPEX << std::endl;

	float ASHP_CAPEX = myCost.calculate_ASHP_CAPEX(12.0); // need to add num HP capacity to Config
	//std::cout << "MyCost ASHP_CAPEX " << ASHP_CAPEX << std::endl;

	float ESS_kW = std::max(myConfig.getESS_charge_power(), myConfig.getESS_discharge_power());

	float annualised_project_cost = myCost.calculate_Project_annualised_cost(ESS_kW, myConfig.getESS_capacity(), PV_kWp_total, 0, 3, 0, 0, 0, 12.0);
	
	//std::cout << "MyCost total_project_annualised_cost " << annualised_project_cost << std::endl;

	float total_annualised_cost = myCost.calculate_total_annualised_cost(ESS_kW, myConfig.getESS_capacity(), PV_kWp_total, 0, 3, 0, 0, 0, 12.0);

	year_TS import_elec_prices;
	import_elec_prices.setallTSvalues(myConfig.getImport_kWh_price()); // for now, simply fix import price
	year_TS export_elec_prices;
	export_elec_prices.setallTSvalues(myConfig.getExport_kWh_price()); // for now, simply fix import price


	year_TS baseline_elec_load_no_HPL = year_TS::add(MountEload.getTS_Fix_load_1(), MountEload.getTS_Fix_load_2());
	//std::cout << "MyCost fix load 1 plus fix load 2 " << baseline_elec_load << std::endl;

	year_TS baseline_elec_load = year_TS::add(baseline_elec_load_no_HPL, MountFlex.getTS_Actual_high_priority_load());
	//std::cout << "Adding Actual high priority load " << baseline_elec_load << std::endl;

	//	myCost.calculate_baseline_elec_cost(baseline_elec_load_no_HPL, import_elec_prices);
	myCost.calculate_baseline_elec_cost(baseline_elec_load, import_elec_prices);

	year_TS baseline_heat_load = year_TS::add(MountHload.getTS_Heatload(), MountFlex.getTS_Actual_low_priority_load());
	year_TS import_fuel_prices;
	import_fuel_prices.setallTSvalues(12.2); // need to add a new config parameter here
	float boiler_efficiency = 0.9;

	myCost.calculate_baseline_fuel_cost(baseline_heat_load, import_fuel_prices, boiler_efficiency);

	myCost.calculate_scenario_elec_cost(MountGrid.getTS_GridImport(), import_elec_prices);

	myCost.calculate_scenario_fuel_cost(MountHload.getTS_Heat_shortfall(), import_fuel_prices);

	myCost.calculate_scenario_export_cost(MountGrid.getTS_GridExport(), export_elec_prices);

	myCost.calculate_scenario_cost_balance(total_annualised_cost);

	//========================================

	myCost.calculate_Project_CAPEX(ESS_kW, myConfig.getESS_capacity(), PV_kWp_total, 0, 3, 0, 0, 0, 12.0);

	//========================================

	myCost.calculate_payback_horizon();

	//========================================

	// Calculate time_dependent CO2e operational emissions section

	myCost.calculate_baseline_elec_CO2e(baseline_elec_load);

	myCost.calculate_baseline_fuel_CO2e(baseline_heat_load);

	myCost.calculate_scenario_elec_CO2e(MountGrid.getTS_GridImport());

	myCost.calculate_scenario_fuel_CO2e(MountHload.getTS_Heat_shortfall());

	myCost.calculate_scenario_export_CO2e(MountGrid.getTS_GridExport());

	myCost.calculate_scenario_carbon_balance();

	//========================================

	/*WRITE DATA SECTION - AFTER PROFILING CLOCK STOPPED*/

	//End profiling
	auto end = std::chrono::high_resolution_clock::now();
	std::chrono::duration<double> elapsed = end - start;  // calculate elaspsed run time
	std::cout << "Runtime: " << elapsed.count() << " seconds" << std::endl; // print elapsed run time
	float runtime_float = static_cast<float>(elapsed.count());
	Runtime.setValue(0, runtime_float);
	std::vector<float> runtime_vect = Runtime.getData();

	// USE ACCESSOR FUNCTIONS TO GET THE COST OUTPUTS FROM Costs.h

	year_TS Annualised_cost;
	Annualised_cost.setValue(0, total_annualised_cost);
	std::vector<float> total_annualised_cost_vect = Annualised_cost.getData();
	//std::vector<float> TS_annualised_cost = myCost.getTS_annualised_cost().getData();

	//year_TS Project_CAPEX;
	//Project_CAPEX.setValue(0, project_CAPEX);
	//std::vector<float> Project_CAPEX_vect = Project_CAPEX.getData();
	std::vector<float> TS_project_CAPEX = myCost.getTS_project_CAPEX().getData();

	//year_TS Scenario_cost_balance;
	//Scenario_cost_balance.setValue(0, scenario_cost_balance);
	//std::vector<float> Scenario_cost_balance_vect = Scenario_cost_balance.getData();
	std::vector<float> TS_scenario_cost_balance = myCost.getTS_scenario_cost_balance().getData();

	//year_TS Payback_horizon_years;
	//Payback_horizon_years.setValue(0, payback_horizon_years);
	//std::vector<float> Payback_horizon_years_vect = Payback_horizon_years.getData();
	std::vector<float> TS_payback_horizon_years = myCost.getTS_payback_horizon_years().getData();

	//year_TS Scenario_carbon_balance;
	//Scenario_carbon_balance.setValue(0, scenario_carbon_balance); 
	//std::vector<float> Scenario_carbon_balance_vect = Scenario_carbon_balance.getData();
	std::vector<float> TS_scenario_carbon_balance = myCost.getTS_scenario_carbon_balance().getData();

	CustomDataTable dataColumns = {
		{"Scaled RGen_total", RGen_total_vect},
		{"Total_scaled_target_load", Total_load_vect},
		{"Total load minus Rgen (ESUM)", ESUM_vect},
		{"ESS_available_discharge_power", ESS_available_discharge_power_vect},
		{"ESS_available_charge_power ", ESS_available_charge_power_vect},
		{"TS_ESS_Rgen_only_charge_vect ", TS_ESS_Rgen_only_charge_vect},
		{"TS_ESS_discharge_vect ", TS_ESS_discharge_vect},
		{"TS_ESS_charge_vect ", TS_ESS_charge_vect},
		{"TS_ESS_Rgen_only_charge ", TS_ESS_Rgen_only_charge_vect},
		{"TS_ESS_resulting_SoC ", TS_ESS_resulting_SoC_vect},
		{"Pre_grid_balance", TS_Pre_grid_balance_vect},
		{"Grid Import", TS_Grid_Import_vect},
		{"Grid Export", TS_Grid_Export_vect},
		{"Post_grid_balance", TS_Post_grid_balance_vect},
		{"Pre_flex_import_shortfall", TS_Pre_flex_import_shortfall_vect},
		{"Pre_mop_curtailed Export", TS_Pre_Mop_curtailed_export_vect},
		{"Actual import shortfall", TS_Actual_import_shortfall_vect},
		{"Actual curtailed export", TS_Actual_curtailed_export_vect},
		{"Actual high priority load", TS_Actual_high_priority_load_vect},
		{"Actual low priority load", TS_Actual_low_priority_load_vect},
		{"Heat load", heatload_vect},
		{"Scaled Heat load", scaled_heatload_vect},
		{"Electrical load scaled heat", Electrical_load_scaled_heat_yield_vect},
		{"Heat shortfall", TS_Heat_shortfall_vect},
		{"Heat surplus", TS_Heat_surplus_vect},
		{"Calculative execution time (s)", runtime_vect},
		{"Parameter index", paramIndex_vect},
		{"Annualised cost", total_annualised_cost_vect},
		{"Project CAPEX", TS_project_CAPEX},
		{"Scenario Balance (£)", TS_scenario_cost_balance},
		{"Payback horizon (yrs)", TS_payback_horizon_years},
		{"Scenario Carbon Balance (kgC02e)", TS_scenario_carbon_balance}
	};

	//CustomDataTable sumDataColumns;

    //appendSumToDataTable(sumDataColumns, dataColumns);

	//sumDataColumns = SumDataTable(dataColumns);

	return dataColumns;

	//return sumDataColumns;
}

OutputValues InitialiseOptimisation(nlohmann::json inputJson) {

	OutputValues output;
	output.maxVal = 0;
	output.minVal = 0;
	output.meanVal = 0;
	output.num_scenarios = 0;
	output.est_hours = 0;
	output.est_seconds = 0;

	std::cout << "EP_BE: Elemental Power Back End" << std::endl; // here we are in main() function...!

	/*DEFINE PARAMETER GRID TO ITERATE THROUGH*/
	// initialise empty parameter grid
	std::vector<paramRange> paramGrid;

	// input argument should be a JSON object containing a dictionary of key-tuple pairs
	// each key should be the name of a parameter to be iterated over; the tuple should provide the range and step size of the iterator
	// fill the parameter grid using the JSON input
	try {
		// Loop through all key-value/key-tuple pairs
		for (const auto& item : inputJson.items()) {
			if (item.value().is_array()) {
				// the item is a key-tuple pair
				paramGrid.push_back({ item.key(), item.value()[0], item.value()[1], item.value()[2] });
				std::cout << "(" << item.key() << "," << item.value()[0] << ":" << item.value()[1] << ":" << item.value()[2] << ")" << std::endl;
			}
			else {
				// the item is a key-value pair
				paramGrid.push_back({ item.key(), item.value(), item.value(), 0.0 });
			}
		}
	}
	catch (const std::exception& e) {
		std::cerr << "Error: " << e.what() << std::endl;
		return output;
	}

	if (paramGrid.empty()) return output;

	/*NEED SOME NULL ACTION HERE - EXECUTE WITH DEFAULT CONFIG PARAMETERS*/

	/*READ DATA SECTION - START PROFILING AFTER SECTION*/

	FileIO myFileIO;
	//std::string testpath = myFileIO.getEloadfilepath(); // REMOVE -- testpath not used again
	std::string absfilepath = myFileIO.getEloadfilepath();

	//read the electric load data
	std::vector<float> hotel_eload_data = readCSVColumn(absfilepath, 4); // read the column of the CSV data and store in vector data
	std::vector<float> ev_eload_data = readCSVColumn(absfilepath, 5); // read the column of the CSV data and store in vector data

	//read the heat load data
	absfilepath = myFileIO.getHloadfilepath();
	std::vector<float> heatload_data = readCSVColumn(absfilepath, 4); // read the column of the CSV data and store in vector data

	//read the renewable generation data
	absfilepath = myFileIO.getRgenfilepath();
	std::vector<float> RGen_data_1 = readCSVColumn(absfilepath, 4); // read the column of the CSV data and store in vector data
	std::vector<float> RGen_data_2 = readCSVColumn(absfilepath, 5);
	std::vector<float> RGen_data_3 = readCSVColumn(absfilepath, 6);
	std::vector<float> RGen_data_4 = readCSVColumn(absfilepath, 7);

	CustomDataTable inputdata = {
	   {"hotel_eload_data", hotel_eload_data},
	   {"ev_eload_data", ev_eload_data},
	   {"heatload_data", heatload_data},
	   {"RGen_data_1", RGen_data_1},
	   {"RGen_data_2", RGen_data_2},
	   {"RGen_data_3", RGen_data_3},
	   {"RGen_data_4", RGen_data_4}
	};

	absfilepath = myFileIO.getOutfilepath();

	int numWorkers = std::thread::hardware_concurrency(); // interrogate the hardware to find number of logical cores, base concurrency loop on that

	if (numWorkers == 0) {
		std::cerr << "Unable to determine the number of logical cores." << std::endl;
		return output;
	}

	std::cout << "Number of logical cores found is " << numWorkers << std::endl;

	CustomDataTable cumDataColumns;

	SafeQueue<std::vector<std::pair<std::string, float>>> taskQueue;
	SafeQueue<CustomDataTable> resultsQueue;

	//std::cout << "Profiler pause: waiting for 10 seconds..." << std::endl;
	//std::this_thread::sleep_for(std::chrono::seconds(10));

	int number = 0;

	//number = get_number_of_scenarios(paramGrid); // get 
	number = generateTasks(paramGrid, taskQueue);

	std::cout << "Total number of scenarios is: " << number << std::endl;

	//std::cout << "Profiler pause: waiting for 10 seconds..." << std::endl;
	//std::this_thread::sleep_for(std::chrono::seconds(10));
	std::vector<std::thread> workers;
	std::atomic<bool> tasksCompleted(false);

	std::mutex scenario_call_mutex;
	int scenario_call = 1;

	for (int i = 0; i < numWorkers-1; ++i) { // keep one worker back for the queues
		workers.emplace_back([&taskQueue, &resultsQueue, &inputdata, &tasksCompleted, &scenario_call, &scenario_call_mutex, i]() {
			std::vector<std::pair<std::string, float>> paramSlice;
			while (scenario_call < 100) {
				if (taskQueue.pop(paramSlice)) {
					CustomDataTable result = scenario(inputdata, paramSlice);
					resultsQueue.push(result);
					{
						std::lock_guard<std::mutex> lock(scenario_call_mutex);
						std::cout << "scenario called " << scenario_call << " times" << std::endl;
						scenario_call++;
					}
				}
				else {
					std::this_thread::sleep_for(std::chrono::milliseconds(10)); // Short sleep
					if (tasksCompleted.load()) {
						std::cout << "Worker " << i << ": no more tasks, exiting." << std::endl;
						break;
					}
				}
			}
			});
	}
	// ***** any points at which this hangs? check transcript

		// After all tasks are generated
	tasksCompleted.store(true);
	std::cout << "tasksCompleted" << std::endl;

	for (auto& worker : workers) {
		if (worker.joinable()) {
			worker.join();
		}
	}
	std::cout << "workers joined" << std::endl;

	//// Retrieve and process results
	CustomDataTable result;
	CustomDataTable resultSum;

	bool isResultAvailable = false;
	do {
		isResultAvailable = resultsQueue.pop(result);
		if (isResultAvailable) {
			/* if you want to store all data columns from each calculative step:- */
			appendDataColumns(cumDataColumns, result);

			/* if you want to store e.g. the column sums */
			// If resultSum has not yet been initialised, do so now...
			if (resultSum.size() == 0) {
				// initialize resultSum with the same keys as result but with empty vectors
				resultSum.reserve(result.size()); // Reserve space for efficiency
				for (const auto& pair : result) {
					resultSum.emplace_back(pair.first, std::vector<float>{}); // Use the key with an empty vector
				}
			}
			// ...then append sums for each result
			appendSumToDataTable(resultSum, result);
		}
	} while (isResultAvailable);


	std::tie(output.maxVal, output.minVal, output.meanVal) = getColumnStats(cumDataColumns); //do this in window handle
	std::cout << "Max: " << output.maxVal << ", Min: " << output.minVal << ", Mean: " << output.meanVal << std::endl;

	float float_numWorkers = float(numWorkers);

	output.num_scenarios = number;
	output.est_seconds = (output.num_scenarios * output.meanVal)/(float_numWorkers-1.0);
	output.est_hours = (output.num_scenarios * output.meanVal) / (3600*(float_numWorkers - 1.0));

	std::cout << "Number of scenarios: " << output.num_scenarios << ", Hours: " << output.est_hours << ", Seconds: " << output.est_seconds << std::endl;

	return output;

}

OutputValues RunMainOptimisation(nlohmann::json inputJson) {

	OutputValues output;
	output.maxVal = 0;
	output.minVal = 0;
	output.meanVal = 0;
	std::cout << "EP_BE: Elemental Power Back End" << std::endl; // here we are in main() function...!

	/*DEFINE PARAMETER GRID TO ITERATE THROUGH*/
	// initialise empty parameter grid
	std::vector<paramRange> paramGrid;

	// input argument should be a JSON object containing a dictionary of key-tuple pairs
	// each key should be the name of a parameter to be iterated over; the tuple should provide the range and step size of the iterator
	// fill the parameter grid using the JSON input
	try {
		// Loop through all key-value/key-tuple pairs
		for (const auto& item : inputJson.items()) {
			if (item.value().is_array()) {
				// the item is a key-tuple pair
				paramGrid.push_back({ item.key(), item.value()[0], item.value()[1], item.value()[2] });
				std::cout << "(" << item.key() << "," << item.value()[0] << ":" << item.value()[1] << ":" << item.value()[2] << ")" << std::endl;
			}
			else {
				// the item is a key-value pair
				paramGrid.push_back({ item.key(), item.value(), item.value(), 0.0 });
			}
		}
	}
	catch (const std::exception& e) {
		std::cerr << "Error: " << e.what() << std::endl;
		return output;
	}

	if (paramGrid.empty()) return output;

	/*NEED SOME NULL ACTION HERE - EXECUTE WITH DEFAULT CONFIG PARAMETERS*/

	/*READ DATA SECTION - START PROFILING AFTER SECTION*/

	FileIO myFileIO;
	//std::string testpath = myFileIO.getEloadfilepath(); // REMOVE -- testpath not used again
	std::string absfilepath = myFileIO.getEloadfilepath();

	//read the electric load data
	std::vector<float> hotel_eload_data = readCSVColumn(absfilepath, 4); // read the column of the CSV data and store in vector data
	std::vector<float> ev_eload_data = readCSVColumn(absfilepath, 5); // read the column of the CSV data and store in vector data

	//read the heat load data
	absfilepath = myFileIO.getHloadfilepath();
	std::vector<float> heatload_data = readCSVColumn(absfilepath, 4); // read the column of the CSV data and store in vector data

	//read the renewable generation data
	absfilepath = myFileIO.getRgenfilepath();
	std::vector<float> RGen_data_1 = readCSVColumn(absfilepath, 4); // read the column of the CSV data and store in vector data
	std::vector<float> RGen_data_2 = readCSVColumn(absfilepath, 5);
	std::vector<float> RGen_data_3 = readCSVColumn(absfilepath, 6);
	std::vector<float> RGen_data_4 = readCSVColumn(absfilepath, 7);

	CustomDataTable inputdata = {
	   {"hotel_eload_data", hotel_eload_data},
	   {"ev_eload_data", ev_eload_data},
	   {"heatload_data", heatload_data},
	   {"RGen_data_1", RGen_data_1 },
	   {"RGen_data_2", RGen_data_2},
	   {"RGen_data_3", RGen_data_3},
	   {"RGen_data_4", RGen_data_4}
	};

	absfilepath = myFileIO.getOutfilepath();

	int numWorkers = std::thread::hardware_concurrency(); // interrogate the hardware to find number of logical cores, base concurrency loop on that

	if (numWorkers == 0) {
		std::cerr << "Unable to determine the number of logical cores." << std::endl;
		return output;
	}

	std::cout << "Number of logical cores found is " << numWorkers << std::endl;

	CustomDataTable cumDataColumns;

	SafeQueue<std::vector<std::pair<std::string, float>>> taskQueue;
	SafeQueue<CustomDataTable> resultsQueue;

	int number = 0;

	number = generateTasks(paramGrid, taskQueue);

	std::cout << "Total number of scenarios is: " << number << std::endl;

	std::vector<std::thread> workers;

	//std::thread minMaxThread(computeMin, std::ref(resultsQueue), "Scenario Balance (£)");


	std::atomic<bool> tasksCompleted(false);

	std::mutex scenario_call_mutex;
	int scenario_call = 1;

	for (int i = 0; i < (numWorkers - 1); ++i) { //keep one worker back for the main thread - need to do A/B test on whether this is performant
		workers.emplace_back([&taskQueue, &resultsQueue, &inputdata, &tasksCompleted, &scenario_call, &scenario_call_mutex, i]() {
			std::vector<std::pair<std::string, float>> paramSlice;
			while (true) {
				if (taskQueue.pop(paramSlice)) {
					CustomDataTable result = scenario(inputdata, paramSlice);// this is the call to scenario 
					//std::optional<std::pair<float, float>> MinMax = resultsQueue.minMaxInColumn("Scenario Balance(£)");
					//std::cout << "MinMax pair " << MinMax << std::endl;
					// add running statistics here 
					//auto [currentMin, currentMax] = resultsQueue.getMinMax();
					resultsQueue.push(result); // this pushes the result to the results queue. Need to only do this if it's a worthy result  
					{
						std::lock_guard<std::mutex> lock(scenario_call_mutex);
						std::cout << "scenario called " << scenario_call << " times" << std::endl;
						scenario_call++;
					}
				}
				else {
					std::cout << "sleeping for 10 ms" << std::endl;
					std::this_thread::sleep_for(std::chrono::milliseconds(10)); // Short sleep
					if (tasksCompleted.load()) {
						std::cout << "Worker " << i << ": no more tasks, exiting." << std::endl;
						break;
					}
				}
			}
			});
	}

	// After all tasks are generated
	tasksCompleted.store(true);
	std::cout << "tasksCompleted" << std::endl;

	for (auto& worker : workers) {
		if (worker.joinable()) {
			worker.join();
		}
	}
	std::cout << "workers joined" << std::endl;
	std::cout << "workers joined" << std::endl;
	//// Retrieve and process results
	CustomDataTable result;
	CustomDataTable resultSum;

	bool isResultAvailable = false;
	do {
		isResultAvailable = resultsQueue.pop(result);
		if (isResultAvailable) {
			/* if you want to store all data columns from each calculative step:- */
			//appendDataColumns(cumDataColumns, result);

			/* if you want to store e.g. the column sums */
			// If resultSum has not yet been initialised, do so now...
			if (cumDataColumns.size() == 0) {
				// initialize resultSum with the same keys as result but with empty vectors
				cumDataColumns.reserve(result.size()); // Reserve space for efficiency
				for (const auto& pair : result) {
					cumDataColumns.emplace_back(pair.first, std::vector<float>{}); // Use the key with an empty vector
				}
			}
			// ...then append sums for each result
			appendSumToDataTable(cumDataColumns, result);
		}
	} while (isResultAvailable);


	writeToCSV(absfilepath, cumDataColumns);// comment out if you don't want a smaller CSV file of summed output that takes a few seconds to write

	float CAPEX, scenario_index = 0;

	std::pair<float, float> valandindex = findMinValueandIndex(cumDataColumns, "Project CAPEX");
	output.CAPEX = valandindex.first;
	output.CAPEX_index = valandindex.second;

	valandindex = findMinValueandIndex(cumDataColumns, "Annualised cost");
	output.annualised = valandindex.first;
	output.annualised_index = valandindex.second;

	valandindex = findMaxValueandIndex(cumDataColumns, "Scenario Balance (£)"); // larger is better!
	output.scenario_cost_balance = valandindex.first;
	output.scenario_cost_balance_index = valandindex.second;

	valandindex = findMinValueandIndex(cumDataColumns, "Payback horizon (yrs)");
	output.payback_horizon = valandindex.first;
	output.payback_horizon_index = valandindex.second;

	valandindex = findMinValueandIndex(cumDataColumns, "Scenario Carbon Balance (kgC02e)");
	output.scenario_carbon_balance = valandindex.first;
	output.scenario_carbon_balance_index = valandindex.second;

	//	std::tie(output.maxVal, output.minVal, output.meanVal) = getColumnStats(resultSum); //do this in window handle

	std::tie(output.maxVal, output.minVal, output.meanVal) = getColumnStats(cumDataColumns);

	std::cout << "Max: " << output.maxVal << ", Min: " << output.minVal << ", Mean: " << output.meanVal << std::endl;

	/* DUMMY OUTPUT -- NEEDS REPLACED WITH SENSIBLE OUTPUT */

	std::vector<float> dummyvec = getDataForKey(cumDataColumns, "Calculative execution time (s)");

	//output.time_taken = dummyvec[0]; // should be total time over all iterations

	output.Fixed_load1_scalar = 1.0;
	output.Fixed_load2_scalar = 2.0;
	output.Flex_load_max = 3.0;
	output.Mop_load_max = 4.0;
	output.ScalarRG1 = 5.0;
	output.ScalarRG2 = 6.0;
	output.ScalarRG3 = 7.0;
	output.ScalarRG4 = 8.0;
	output.ScalarHL1 = 9.0;
	output.ScalarHYield1 = 10.0;
	output.ScalarHYield2 = 11.0;
	output.ScalarHYield3 = 12.0;
	output.ScalarHYield4 = 13.0;
	output.GridImport = 14.0;
	output.GridExport = 15.0;
	output.Import_headroom = 16.0;
	output.Export_headroom = 17.0;
	output.ESS_charge_power = 18.0;
	output.ESS_discharge_power = 19.0;
	output.ESS_capacity = 20.0;
	output.ESS_RTE = 21.0;
	output.ESS_aux_load = 22.0;
	output.ESS_start_SoC = 23.0;
	output.ESS_charge_mode = 24.0;
	output.ESS_discharge_mode = 25.0;
	//output.CAPEX = 26.0;
	//output.annualised = 27.0;
	//output.scenario_cost_balance = 28.0;
	//output.payback_horizon = 30.0;
	//output.scenario_carbon_balance = 29.0;
	//output.scenario_index = 30.0;
	return output;
}

OutputValues RecallIndex(nlohmann::json inputJson, int recallindex) {

	OutputValues output;

	output.maxVal = 0;

	std::vector<paramRange> paramGrid;

	try {
		// Loop through all key-value/key-tuple pairs
		for (const auto& item : inputJson.items()) {
			if (item.value().is_array()) {
				// the item is a key-tuple pair
				paramGrid.push_back({ item.key(), item.value()[0], item.value()[1], item.value()[2] });
				std::cout << "(" << item.key() << "," << item.value()[0] << ":" << item.value()[1] << ":" << item.value()[2] << ")" << std::endl;
			}
			else {
				// the item is a key-value pair
				paramGrid.push_back({ item.key(), item.value(), item.value(), 0.0 });
			}
		}
	}
	catch (const std::exception& e) {
		std::cerr << "Error: " << e.what() << std::endl;
		return output;
	}

	if (paramGrid.empty()) return output;

	//auto paramSlice = ParamRecall(paramGrid, recallindex);

	auto paramSlice = TaskRecall(paramGrid, recallindex);

	for (const auto& p : paramSlice) {
		std::cout << p.first << ": " << p.second << std::endl;
	}

	std::string target = "Fixed_load1_scalar"; // Replace with the string you're looking for
	float value = 0.0f;
	bool found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.Fixed_load1_scalar = value;
	}

	target = "Fixed_load2_scalar"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.Fixed_load2_scalar = value;
	}
	target = "Flex_load_max"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.Flex_load_max = value;
	}
	target = "Mop_load_max"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.Mop_load_max = value;
	}
	target = "ScalarRG1"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarRG1 = value;
	}
	target = "ScalarRG2"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarRG2 = value;
	}

	target = "ScalarRG3"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarRG3 = value;
	}
	target = "ScalarRG4"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarRG4 = value;
	}

	target = "ScalarHL1"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarHL1 = value;
	}
	target = "ScalarHYield1"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarHYield1 = value;
	}
	target = "ScalarHYield2"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarHYield2 = value;
	}
	target = "ScalarHYield3"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarHYield3 = value;
	}
	target = "ScalarHYield4"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarHYield4 = value;
	}
	target = "GridImport"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.GridImport = value;
	}
	target = "GridExport"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.GridExport = value;
	}
	target = "Import_headroom"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.Import_headroom = value;
	}
	target = "Export_headroom"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.Export_headroom = value;
	}
	target = "ESS_charge_power"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_charge_power = value;
	}
	target = "ESS_discharge_power"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_discharge_power = value;
	}
	target = "ESS_capacity"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_capacity = value;
	}

	target = "ESS_RTE"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_RTE = value;
	}

	target = "ESS_aux_load"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_aux_load = value;
	}
	target = "ESS_start_SoC"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_start_SoC = value;
	}
	target = "ESS_charge_mode"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_charge_mode = value;
	}

	target = "ESS_discharge_mode"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_discharge_mode = value;
	}
	
	target = "import_kWh_price"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.import_kWh_price = value;
	}

	target = "export_kWh_price"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
		for (const auto& element : paramSlice) {
			if (element.first == target) {
				value = element.second;
				found = true;
				break; // Stop the loop once you've found the element
			}
		}
	if (found) {
		output.export_kWh_price = value;
	}


	return output;

}

//Visual Form based stuff
// Global Variables:
HINSTANCE hInst;                                // current instance
WCHAR szTitle[MAX_LOADSTRING];                  // The title bar text
WCHAR szWindowClass[MAX_LOADSTRING];            // the main window class name

// Forward declarations of functions included in this code module:
ATOM                MyRegisterClass(HINSTANCE hInstance);
BOOL                InitInstance(HINSTANCE, int);
LRESULT CALLBACK    WndProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK    About(HWND, UINT, WPARAM, LPARAM);

// window scrolling:
//SCROLLINFO si = { 0 };
//si.cbSize = sizeof(si);
//si.fMask = SIF_RANGE | SIF_PAGE;
//si.nMin = 0;
//si.nMax = 100;
//si.nPage = 10;

HWND hTextbox1; HWND hTextbox2; HWND hTextbox3; HWND hTextbox4; HWND hTextbox5; HWND hTextbox6; HWND hTextbox7; HWND hTextbox8; HWND hTextbox9; HWND hTextbox10;
HWND hTextbox11; HWND hTextbox12; HWND hTextbox13; HWND hTextbox14; HWND hTextbox15; HWND hTextbox16; HWND hTextbox17; HWND hTextbox18; HWND hTextbox19; HWND hTextbox20;
HWND hTextbox21; HWND hTextbox22; HWND hTextbox23; HWND hTextbox24; HWND hTextbox25; HWND hTextbox26; HWND hTextbox27; HWND hTextbox28; HWND hTextbox29; HWND hTextbox30;
HWND hTextbox31; HWND hTextbox32; HWND hTextbox33; HWND hTextbox34; HWND hTextbox35; HWND hTextbox36; HWND hTextbox37; HWND hTextbox38; HWND hTextbox39; HWND hTextbox40;
HWND hTextbox41; HWND hTextbox42; HWND hTextbox43; HWND hTextbox44; HWND hTextbox45; HWND hTextbox46; HWND hTextbox47; HWND hTextbox48; HWND hTextbox49; HWND hTextbox50;
HWND hTextbox51; HWND hTextbox52; HWND hTextbox53; HWND hTextbox54; HWND hTextbox55; HWND hTextbox56; HWND hTextbox57; HWND hTextbox58; HWND hTextbox59; HWND hTextbox60;
HWND hTextbox61; HWND hTextbox62; HWND hTextbox63; HWND hTextbox64; HWND hTextbox65; HWND hTextbox66; HWND hTextbox67; HWND hTextbox68; HWND hTextbox69; HWND hTextbox70;
HWND hTextbox71; HWND hTextbox72; HWND hTextbox73; HWND hTextbox74; HWND hTextbox75; HWND hTextbox76; HWND hTextbox77; HWND hTextbox78; HWND hTextbox79; HWND hTextbox80;
HWND hTextbox81; HWND hTextbox82; HWND hTextbox83; HWND hTextbox84; HWND hTextbox85; HWND hTextbox86; HWND hTextbox87; HWND hTextbox88; HWND hTextbox89;

HWND hTextbox200;

HWND hOutput1; HWND hOutput2; HWND hOutput3; HWND hOutput4; HWND hOutput5; HWND hOutput6; HWND hOutput7; HWND hOutput8; HWND hOutput9; HWND hOutput10;
HWND hOutput11; HWND hOutput12; HWND hOutput13; HWND hOutput14; HWND hOutput15; HWND hOutput16; HWND hOutput17; HWND hOutput18; HWND hOutput19; HWND hOutput20;
HWND hOutput21; HWND hOutput22; HWND hOutput23; HWND hOutput24; HWND hOutput25; HWND hOutput26; HWND hOutput27; HWND hOutput28; HWND hOutput29; HWND hOutput30;
HWND hOutput31; HWND hOutput32; HWND hOutput33; HWND hOutput34; HWND hOutput35; HWND hOutput36;
	

int APIENTRY wWinMain(_In_ HINSTANCE hInstance,
                     _In_opt_ HINSTANCE hPrevInstance,
                     _In_ LPWSTR    lpCmdLine,
                     _In_ int       nCmdShow)
{
    UNREFERENCED_PARAMETER(hPrevInstance);
    UNREFERENCED_PARAMETER(lpCmdLine);

    // TODO: Place code here.


    // Initialize global strings
    LoadStringW(hInstance, IDS_APP_TITLE, szTitle, MAX_LOADSTRING);
    LoadStringW(hInstance, IDC_EPFEFULL, szWindowClass, MAX_LOADSTRING);
    MyRegisterClass(hInstance);

    // Perform application initialization:
    if (!InitInstance (hInstance, nCmdShow))
    {
        return FALSE;
    }

    HACCEL hAccelTable = LoadAccelerators(hInstance, MAKEINTRESOURCE(IDC_EPFEFULL));

    MSG msg;

    // Main message loop:
    while (GetMessage(&msg, nullptr, 0, 0))
    {
        if (!TranslateAccelerator(msg.hwnd, hAccelTable, &msg))
        {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
    }

    return (int) msg.wParam;
}



//
//  FUNCTION: MyRegisterClass()
//
//  PURPOSE: Registers the window class.
//
ATOM MyRegisterClass(HINSTANCE hInstance)
{
    WNDCLASSEXW wcex;

    wcex.cbSize = sizeof(WNDCLASSEX);

    wcex.style          = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc    = WndProc;
    wcex.cbClsExtra     = 0;
    wcex.cbWndExtra     = 0;
    wcex.hInstance      = hInstance;
    wcex.hIcon          = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_EPFEFULL));
    wcex.hCursor        = LoadCursor(nullptr, IDC_ARROW);
    wcex.hbrBackground  = (HBRUSH)(COLOR_WINDOW+1);
    wcex.lpszMenuName   = MAKEINTRESOURCEW(IDC_EPFEFULL);
    wcex.lpszClassName  = szWindowClass;
    wcex.hIconSm        = LoadIcon(wcex.hInstance, MAKEINTRESOURCE(IDI_SMALL));

    return RegisterClassExW(&wcex);
}

//
//   FUNCTION: InitInstance(HINSTANCE, int)
//
//   PURPOSE: Saves instance handle and creates main window
//
//   COMMENTS:
//
//        In this function, we save the instance handle in a global variable and
//        create and display the main program window.
//

BOOL InitConsole()
{
	if (!AllocConsole()) {
		return FALSE;
	}

	FILE* pCout;
	freopen_s(&pCout, "CONOUT$", "w", stdout);

	//std::cout << "Console initialized!\n";

	return TRUE;
}

BOOL CloseConsole() {
	// Close the standard output stream
	fclose(stdout);

	// Detach and destroy the console
	if (!FreeConsole()) {
		return FALSE;
	}

	//std::cout << "Console closed!\n"; // This won't be shown in the console

	return TRUE;
}


BOOL InitInstance(HINSTANCE hInstance, int nCmdShow)
{
   hInst = hInstance; // Store instance handle in our global variable

   DWORD windowStyle = WS_OVERLAPPEDWINDOW | WS_HSCROLL | WS_VSCROLL;

   HWND hWnd = CreateWindowW(szWindowClass, 
	   szTitle, 
	   windowStyle, CW_USEDEFAULT, 0,
	   2500, //width
	   2000, // height
	   nullptr, nullptr, hInstance, nullptr);

   HWND hButton0 = CreateWindow(
	   L"BUTTON",  // Predefined class; Unicode assumed.
	   L"INITIALISE",      // Button text.
	   WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,  // Styles.
	   10,         // x position.
	   10,         // y position.
	   100,        // Button width.
	   30,         // Button height.
	   hWnd,       // Parent window.
	   (HMENU)ID_BUTTON0,       // No menu.
	   (HINSTANCE)GetWindowLongPtr(hWnd, GWLP_HINSTANCE),
	   NULL);      // Pointer not needed.
   // ... add more textboxes as needed

   HWND hButton1 = CreateWindow(
       L"BUTTON",  // Predefined class; Unicode assumed.
       L"RUN",      // Button text.
       WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,  // Styles.
       10,         // x position.
       80,         // y position.
       100,        // Button width.
       30,         // Button height.
       hWnd,       // Parent window.
       (HMENU)ID_BUTTON1,       // No menu.
       (HINSTANCE)GetWindowLongPtr(hWnd, GWLP_HINSTANCE),
       NULL);      // Pointer not needed.
  
   HWND hButton2 = CreateWindow(
	   L"BUTTON",  // Predefined class; Unicode assumed.
	   L"RECALL",      // Button text.
	   WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,  // Styles.
	   10,         // x position.
	   150,         // y position.
	   100,        // Button width.
	   30,         // Button height.
	   hWnd,       // Parent window.
	   (HMENU)ID_BUTTON2,       // No menu.
	   (HINSTANCE)GetWindowLongPtr(hWnd, GWLP_HINSTANCE),
	   NULL);      // Pointer not needed.

   HWND hLabelout18 = CreateWindowW(
	   L"STATIC",
	   L"INDEX",
	   WS_VISIBLE | WS_CHILD,
	   10,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   30,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox200 = CreateWindowW(
	   L"EDIT",
	   L"",  // initial text
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
	   10,   // x position
	   210,  // y position
	   100,  // width
	   30,   // height
	   hWnd,
	   (HMENU)ID_TEXTBOX200,
	   hInstance,
	   NULL);


   // ... add more textboxes as needed
   
   HWND hLabel00 = CreateWindowW(
	   L"STATIC",
	   L"ESTIMATED TIME",
	   WS_VISIBLE | WS_CHILD,
	   120,         // x position.
	   10,         // y position.
	   100,       //width
	   50,		//height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   HWND hLabel1 = CreateWindowW(
	   L"STATIC",
	   L"# Scenarios",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   10,  // y position (above the text box)
	   100, // width
	   20,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   //hTextbox1 = CreateWindowW(  now used for output box in initialsise
	  // L"EDIT",
	  // L"",  // Enter default value
	  // WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	  // 240,
	  // 30,
	  // 100,
	  // 30,
	  // hWnd,
	  // (HMENU)ID_TEXTBOX2,  // ID for the textbox
	  // hInstance,
	  // NULL);  

   HWND hLabel2 = CreateWindowW(
	   L"STATIC",
	   L"Hours",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   10,  // y position (above the text box)
	   100, // width
	   20,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   //hTextbox2 = CreateWindowW(
	  // L"EDIT",
	  // L"",  // No text initially.
	  // WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	  // 360,
	  // 30,
	  // 100,
	  // 30,
	  // hWnd,
	  // (HMENU)ID_TEXTBOX3,  // ID for the textbox
	  // hInstance,
	  // NULL);

   HWND hLabel3 = CreateWindowW(
	   L"STATIC",
	   L"Seconds",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   10,  // y position (above the text box)
	   100, // width
	   20,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   //hTextbox3 = CreateWindowW(
	  // L"EDIT",
	  // L"",  // No text initially.
	  // WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	  // 480,
	  // 30,
	  // 100,
	  // 30,
	  // hWnd,
	  // (HMENU)ID_TEXTBOX3,  // ID for the textbox
	  // hInstance,
	  // NULL);


   HWND hLabel0 = CreateWindowW(
	   L"STATIC",
	   L"INPUTS (overwrite default values)",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   80,  // y position (above the text box)
	   100, // width
	   80,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

  

   HWND hLabel4 = CreateWindowW(
	   L"STATIC",
	   L"Timestep, Minutes",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   80,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox4 = CreateWindowW(
	   L"EDIT",
	   L"60",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   130,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX4,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel5 = CreateWindowW(
	   L"STATIC",
	   L"Timestep, Hours",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   80,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox5 = CreateWindowW(
	   L"EDIT",
	   L"1",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   130,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX5,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel6 = CreateWindowW(
	   L"STATIC",
	   L"Time window, hours",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   80,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox6 = CreateWindowW(
	   L"EDIT",
	   L"8760",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   130,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX6,  // ID for the textbox
	   hInstance,
	   NULL);
  
   // new button row 

   HWND hLabel7 = CreateWindowW(
	   L"STATIC",
	   L"Fixed load1 scalar lower",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox7 = CreateWindowW(
	   L"EDIT",
	   L"1",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX7,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel8 = CreateWindowW(
	   L"STATIC",
	   L"Fixed load1 scalar upper",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox8 = CreateWindowW(
	   L"EDIT",
	   L"1",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX8,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel9 = CreateWindowW(
	   L"STATIC",
	   L"Fixed load1 scalar step",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox9 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX9,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel10 = CreateWindowW(
	   L"STATIC",
	   L"Fixed load2 scalar lower",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox10 = CreateWindowW(
	   L"EDIT",
	   L"3",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX10,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel11 = CreateWindowW(
	   L"STATIC",
	   L"Fixed load2 scalar upper",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox11 = CreateWindowW(
	   L"EDIT",
	   L"3",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX11,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel12 = CreateWindowW(
	   L"STATIC",
	   L"Fixed load2 scalar step",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox12 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX12,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel13 = CreateWindowW(
	   L"STATIC",
	   L"Flex max lower",
	   WS_VISIBLE | WS_CHILD,
	   840,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox13 = CreateWindowW(
	   L"EDIT",
	   L"50.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   840,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX13,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel14 = CreateWindowW(
	   L"STATIC",
	   L"Flex max lower upper",
	   WS_VISIBLE | WS_CHILD,
	   960,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox14 = CreateWindowW(
	   L"EDIT",
	   L"50.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   960,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX14,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel15 = CreateWindowW(
	   L"STATIC",
	   L"Flex max lower step",
	   WS_VISIBLE | WS_CHILD,
	   1080,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox15 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1080,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX15,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel16 = CreateWindowW(
	   L"STATIC",
	   L"Mop load max lower",
	   WS_VISIBLE | WS_CHILD,
	   1200,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox16 = CreateWindowW(
	   L"EDIT",
	   L"300.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1200,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX16,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel17 = CreateWindowW(
	   L"STATIC",
	   L"Mop load max upper",
	   WS_VISIBLE | WS_CHILD,
	   1320,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox17 = CreateWindowW(
	   L"EDIT",
	   L"300.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1320,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX17,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel18 = CreateWindowW(
	   L"STATIC",
	   L"Mop load max step",
	   WS_VISIBLE | WS_CHILD,
	   1440,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox18 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1440,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX18,  // ID for the textbox
	   hInstance,
	   NULL);

   // new GUI row 

   HWND hLabel19 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG1 lower",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox19 = CreateWindowW(
	   L"EDIT",
	   L"599.2",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX19,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel20 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG1 upper",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox20 = CreateWindowW(
	   L"EDIT",
	   L"599.2",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX20,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel21 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG1 step",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox21 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX21,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel22 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG2 lower",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox22 = CreateWindowW(
	   L"EDIT",
	   L"75.6",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX22,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel23 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG2 upper",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox23 = CreateWindowW(
	   L"EDIT",
	   L"75.6",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX23,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel24 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG2 step",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox24 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX24,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel25 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG3 lower",
	   WS_VISIBLE | WS_CHILD,
	   840,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox25 = CreateWindowW(
	   L"EDIT",
	   L"60.48",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   840,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX25,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel26 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG3 upper",
	   WS_VISIBLE | WS_CHILD,
	   960,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox26 = CreateWindowW(
	   L"EDIT",
	   L"60.48",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   960,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX26,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel27 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG3 step",
	   WS_VISIBLE | WS_CHILD,
	   1080,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox27 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1080,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX27,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel28 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG4 lower",
	   WS_VISIBLE | WS_CHILD,
	   1200,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox28 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1200,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX28,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel29 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG4 upper",
	   WS_VISIBLE | WS_CHILD,
	   1320,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox29 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1320,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX29,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel30 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG4 step",
	   WS_VISIBLE | WS_CHILD,
	   1440,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox30 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1440,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX30,  // ID for the textbox
	   hInstance,
	   NULL);

   // New GUI row

   HWND hLabel31 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HL1 lower",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox31 = CreateWindowW(
	   L"EDIT",
	   L"1.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX31,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel32 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HL1 upper",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox32 = CreateWindowW(
	   L"EDIT",
	   L"1.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX32,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel33 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HL1 step",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox33 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX33,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel34 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield1 lower",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox34 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX34,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel35 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield1 upper",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox35 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX35,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel36 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield1 step",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox36 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX36,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel37 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield2 lower",
	   WS_VISIBLE | WS_CHILD,
	   840,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox37 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   840,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX37,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel38 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield2 upper",
	   WS_VISIBLE | WS_CHILD,
	   960,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox38 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   960,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX38,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel39 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield2 step",
	   WS_VISIBLE | WS_CHILD,
	   1080,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox39 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1080,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX39,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel40 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield3 lower",
	   WS_VISIBLE | WS_CHILD,
	   1200,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox40 = CreateWindowW(
	   L"EDIT",
	   L"0.75",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1200,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX40,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel41 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield3 upper",
	   WS_VISIBLE | WS_CHILD,
	   1320,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox41 = CreateWindowW(
	   L"EDIT",
	   L"0.75",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1320,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX41,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel42 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield3 step",
	   WS_VISIBLE | WS_CHILD,
	   1440,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox42 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1440,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX42,  // ID for the textbox
	   hInstance,
	   NULL);


   HWND hLabel43 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield4 lower",
	   WS_VISIBLE | WS_CHILD,
	   1560,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox43 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1560,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX43,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel44 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield4 upper",
	   WS_VISIBLE | WS_CHILD,
	   1680,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox44 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1680,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX44,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel45 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield4 step",
	   WS_VISIBLE | WS_CHILD,
	   1800,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox45 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1800,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX45,  // ID for the textbox
	   hInstance,
	   NULL);


   HWND hLabel46 = CreateWindowW(
	   L"STATIC",
	   L"Grid import lower",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox46 = CreateWindowW(
	   L"EDIT",
	   L"98.29",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX46,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel47 = CreateWindowW(
	   L"STATIC",
	   L"Grid import upper",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox47 = CreateWindowW(
	   L"EDIT",
	   L"98.29",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX47,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel48 = CreateWindowW(
	   L"STATIC",
	   L"Grid import step",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox48 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX48,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel49 = CreateWindowW(
	   L"STATIC",
	   L"Grid export lower",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox49 = CreateWindowW(
	   L"EDIT",
	   L"95.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX49,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel50 = CreateWindowW(
	   L"STATIC",
	   L"Grid export upper",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox50 = CreateWindowW(
	   L"EDIT",
	   L"95.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX50,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel51 = CreateWindowW(
	   L"STATIC",
	   L"Grid export step",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox51 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX51,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel52 = CreateWindowW(
	   L"STATIC",
	   L"Import headroom lower",
	   WS_VISIBLE | WS_CHILD,
	   840,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox52 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   840,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX52,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel53 = CreateWindowW(
	   L"STATIC",
	   L"Import headroom upper",
	   WS_VISIBLE | WS_CHILD,
	   960,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox53 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   960,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX53,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel54 = CreateWindowW(
	   L"STATIC",
	   L"Import headroom step",
	   WS_VISIBLE | WS_CHILD,
	   1080,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox54 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1080,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX54,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel55 = CreateWindowW(
	   L"STATIC",
	   L"Export headroom lower",
	   WS_VISIBLE | WS_CHILD,
	   1200,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox55 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1200,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX55,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel56 = CreateWindowW(
	   L"STATIC",
	   L"Export headroom upper",
	   WS_VISIBLE | WS_CHILD,
	   1320,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox56 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1320,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX56,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel57 = CreateWindowW(
	   L"STATIC",
	   L"Export headroom step",
	   WS_VISIBLE | WS_CHILD,
	   1440,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox57 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1440,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX57,  // ID for the textbox
	   hInstance,
	   NULL);


   HWND hLabel58 = CreateWindowW(
	   L"STATIC",
	   L"ESS charge power lower",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox58 = CreateWindowW(
	   L"EDIT",
	   L"300.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX58,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel59 = CreateWindowW(
	   L"STATIC",
	   L"ESS charge power upper",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox59 = CreateWindowW(
	   L"EDIT",
	   L"600.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX59,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel60 = CreateWindowW(
	   L"STATIC",
	   L"ESS charge power step",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox60 = CreateWindowW(
	   L"EDIT",
	   L"300.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX60,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel61 = CreateWindowW(
	   L"STATIC",
	   L"ESS discharge power lower",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox61 = CreateWindowW(
	   L"EDIT",
	   L"300.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX61,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel62 = CreateWindowW(
	   L"STATIC",
	   L"ESS discharge power upper",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox62 = CreateWindowW(
	   L"EDIT",
	   L"600.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX62,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel63 = CreateWindowW(
	   L"STATIC",
	   L"ESS discharge power step",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox63 = CreateWindowW(
	   L"EDIT",
	   L"300.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX63,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel64 = CreateWindowW(
	   L"STATIC",
	   L"ESS capacity lower",
	   WS_VISIBLE | WS_CHILD,
	   840,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox64 = CreateWindowW(
	   L"EDIT",
	   L"800.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   840,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX64,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel65 = CreateWindowW(
	   L"STATIC",
	   L"ESS capacity upper",
	   WS_VISIBLE | WS_CHILD,
	   960,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox65 = CreateWindowW(
	   L"EDIT",
	   L"900.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   960,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX65,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel66 = CreateWindowW(
	   L"STATIC",
	   L"ESS capacity step",
	   WS_VISIBLE | WS_CHILD,
	   1080,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox66 = CreateWindowW(
	   L"EDIT",
	   L"20",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1080,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX66,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel67 = CreateWindowW(
	   L"STATIC",
	   L"ESS RTE lower",
	   WS_VISIBLE | WS_CHILD,
	   1200,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox67 = CreateWindowW(
	   L"EDIT",
	   L"0.86",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1200,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX16,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel68 = CreateWindowW(
	   L"STATIC",
	   L"ESS RTE upper",
	   WS_VISIBLE | WS_CHILD,
	   1320,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox68 = CreateWindowW(
	   L"EDIT",
	   L"0.86",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1320,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX68,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel69 = CreateWindowW(
	   L"STATIC",
	   L"ESS RTE step",
	   WS_VISIBLE | WS_CHILD,
	   1440,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox69 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1440,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX69,  // ID for the textbox
	   hInstance,
	   NULL);

   // new GUI row 

   HWND hLabel70 = CreateWindowW(
	   L"STATIC",
	   L"ESS aux load lower",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox70 = CreateWindowW(
	   L"EDIT",
	   L"0.75",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX70,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel71 = CreateWindowW(
	   L"STATIC",
	   L"ESS aux load upper",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox71 = CreateWindowW(
	   L"EDIT",
	   L"0.75",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX71,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel72 = CreateWindowW(
	   L"STATIC",
	   L"ESS aux load step",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox72 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX72,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel73= CreateWindowW(
	   L"STATIC",
	   L"ESS start SoC lower",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox73 = CreateWindowW(
	   L"EDIT",
	   L"0.5",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX73,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel74 = CreateWindowW(
	   L"STATIC",
	   L"ESS start SoC Upper",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox74 = CreateWindowW(
	   L"EDIT",
	   L"0.5",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX74,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel75 = CreateWindowW(
	   L"STATIC",
	   L"ESS start SoC step",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox75 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX75,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel76 = CreateWindowW(
	   L"STATIC",
	   L"ESS charge mode lower",
	   WS_VISIBLE | WS_CHILD,
	   840,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox76 = CreateWindowW(
	   L"EDIT",
	   L"1",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   840,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX76,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel77 = CreateWindowW(
	   L"STATIC",
	   L"ESS charge mode upper",
	   WS_VISIBLE | WS_CHILD,
	   960,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox77 = CreateWindowW(
	   L"EDIT",
	   L"1",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   960,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX77,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel78 = CreateWindowW(
	   L"STATIC",
	   L"ESS discharge mode lower",
	   WS_VISIBLE | WS_CHILD,
	   1080,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox78 = CreateWindowW(
	   L"EDIT",
	   L"1",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1080,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX78,  // ID for the textbox
	   hInstance,
	   NULL);
   
   HWND hLabel79 = CreateWindowW(
	   L"STATIC",
	   L"ESS discharge mode upper",
	   WS_VISIBLE | WS_CHILD,
	   1200,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox79= CreateWindowW(
	   L"EDIT",
	   L"1",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1200,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX79,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel80 = CreateWindowW(
	   L"STATIC",
	   L"Import Price p/kWh",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   780,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox80 = CreateWindowW(
	   L"EDIT",
	   L"30",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   830,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX80,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel81 = CreateWindowW(
	   L"STATIC",
	   L"Export Price p/kWh",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   780,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox81 = CreateWindowW(
	   L"EDIT",
	   L"5",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   830,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX81,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel82 = CreateWindowW(
	   L"STATIC",
	   L"Time budget, minutes",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   780,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox82 = CreateWindowW(
	   L"EDIT",
	   L"1.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   830,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX85,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel83 = CreateWindowW(
	   L"STATIC",
	   L"Target Max Concurrency",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   780,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox83 = CreateWindowW(
	   L"EDIT",
	   L"44",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   830,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX86,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel84 = CreateWindowW(
	   L"STATIC",
	   L"CAPEX limit, £k",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   780,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox84 = CreateWindowW(
	   L"EDIT",
	   L"500",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   830,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX87,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel85 = CreateWindowW(
	   L"STATIC",
	   L"OPEX limit, £k",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   780,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox85 = CreateWindowW(
	   L"EDIT",
	   L"20",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   830,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX88,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabelout0 = CreateWindowW(
	   L"STATIC",
	   L"OUTPUTS",
	   WS_VISIBLE | WS_CHILD,
	   10,  // x position
	   890,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   HWND hLabelout1 = CreateWindowW(
	   L"STATIC",
	   L"Scenario Max Time, s",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   890,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

    hOutput1 = CreateWindowW(
	   L"EDIT",
	   L"",  // initial text
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
	   120,   // x position
	   950,  // y position
	   100,  // width
	   30,   // height
	   hWnd,
	   (HMENU)ID_OUTPUT1,
	   hInstance,
	   NULL);

	HWND hLabelout2 = CreateWindowW(
		L"STATIC",
		L"Scenario Min Time, s",
		WS_VISIBLE | WS_CHILD,
		240,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

    hOutput2 = CreateWindowW(
	   L"EDIT",
	   L"",  // initial text
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
	   240,  // x position
	   950,  // y position
	   100,  // width
	   30,   // height
	   hWnd,
	   (HMENU)ID_OUTPUT2,
	   hInstance,
	   NULL);

	HWND hLabelout3 = CreateWindowW(
		L"STATIC",
		L"Scenario Mean Time, s",
		WS_VISIBLE | WS_CHILD,
		360,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput3 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		360,  // x position
		950,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT3,
		hInstance,
		NULL);

	HWND hLabelout4 = CreateWindowW(
		L"STATIC",
		L"Total time taken, s",
		WS_VISIBLE | WS_CHILD,
		480,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

    hOutput4 = CreateWindowW(
	   L"EDIT",
	   L"",  // initial text
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
	   480,  // x position
	   950,  // y position
	   100,  // width
	   30,   // height
	   hWnd,
	   (HMENU)ID_OUTPUT4,
	   hInstance,
	   NULL);

	HWND hLabelout5 = CreateWindowW(
		L"STATIC",
		L"CAPEX, £",
		WS_VISIBLE | WS_CHILD,
		600,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput5 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		600,   // x position
		950,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT5,
		hInstance,
		NULL);

	HWND hLabelout6 = CreateWindowW(
		L"STATIC",
		L"Annualised, £",
		WS_VISIBLE | WS_CHILD,
		720,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput6 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		720,  // x position
		950,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT6,
		hInstance,
		NULL);

	HWND hLabelout7 = CreateWindowW(
		L"STATIC",
		L"Cost balance, £",
		WS_VISIBLE | WS_CHILD,
		840,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput7 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		840,  // x position
		950,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT7,
		hInstance,
		NULL);


	HWND hLabelout8 = CreateWindowW(
		L"STATIC",
		L"Breakeven years",
		WS_VISIBLE | WS_CHILD,
		960,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput8 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		960,  // x position
		950,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT8,
		hInstance,
		NULL);

	HWND hLabelout9 = CreateWindowW(
		L"STATIC",
		L"Carbon balance, kgC02e",
		WS_VISIBLE | WS_CHILD,
		1080,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput9 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		1080,  // x position
		950,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT9,
		hInstance,
		NULL);


	hOutput10 = CreateWindowW(
		L"EDIT",
		L"",  // Enter default value
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
		240,
		30,
		100,
		30,
		hWnd,
		(HMENU)ID_OUTPUT10,  // ID for the textbox
		hInstance,
		NULL);

	hOutput11 = CreateWindowW(
		L"EDIT",
		L"",  // No text initially.
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
		360,
		30,
		100,
		30,
		hWnd,
		(HMENU)ID_OUTPUT11,  // ID for the textbox
		hInstance,
		NULL);

	hOutput12 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		480,
		30,
		100,
		30,
		hWnd,
		(HMENU)ID_OUTPUT12,
		hInstance,
		NULL);

	HWND hLabelout13 = CreateWindowW(
		L"STATIC",
		L"INDEX",
		WS_VISIBLE | WS_CHILD,
		480,  // x position
		1010,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput13 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		600,   // x position
		1010,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT13,
		hInstance,
		NULL);

	hOutput14 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		720,  // x position
		1010,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT14,
		hInstance,
		NULL);

	hOutput15= CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		840,  // x position
		1010,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT15,
		hInstance,
		NULL);

	hOutput16 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		960,  // x position
		1010,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT16,
		hInstance,
		NULL);

	hOutput17 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		1080,  // x position
		1010,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT17,
		hInstance,
		NULL);


   // ... add more textboxes as needed

   if (!hWnd)
   {
      return FALSE;
   }

   ShowWindow(hWnd, nCmdShow);
   UpdateWindow(hWnd);

   return TRUE;
}

//handle scrolling

//
//  FUNCTION: WndProc(HWND, UINT, WPARAM, LPARAM)
//
//  PURPOSE: Processes messages for the main window.
//
//  WM_COMMAND  - process the application menu
//  WM_PAINT    - Paint the main window
//  WM_DESTROY  - post a quit message and return
//
//
LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam)
{
	int wmID, wmEvent;

	SCROLLINFO si = { sizeof(si), SIF_ALL };

	switch (message)
	{
	case WM_CREATE:
	{
		// Vertical Scroll Initialization
		SCROLLINFO siVert = { sizeof(siVert), SIF_RANGE | SIF_PAGE, 0, 400, 20 }; // Doubled the range
		SetScrollInfo(hWnd, SB_VERT, &siVert, TRUE);

		// Horizontal Scroll Initialization
		SCROLLINFO siHorz = { sizeof(siHorz), SIF_RANGE | SIF_PAGE, 0, 400, 20 }; // Doubled the range
		SetScrollInfo(hWnd, SB_HORZ, &siHorz, TRUE);
	}
	break;
	// ... other cases ..

	case WM_VSCROLL:
	{
		// First, get the current scroll info.
		si.fMask = SIF_ALL;
		GetScrollInfo(hWnd, SB_VERT, &si);
		int yPos = si.nPos;
		int yDelta;

		switch (LOWORD(wParam))
		{
		case SB_LINEUP:
			yPos--;
			break;
		case SB_LINEDOWN:
			yPos++;
			break;
		case SB_PAGEUP:
			yPos -= si.nPage;
			break;
		case SB_PAGEDOWN:
			yPos += si.nPage;
			break;
		case SB_THUMBTRACK:
			yPos = HIWORD(wParam);
			break;
		default:
			break;
		}

		// After modifications, set the new position and then re-display the thumb
		yPos = std::max(si.nMin, std::min(yPos, si.nMax - (int)si.nPage + 1));
		yDelta = si.nPos - yPos;

		if (yDelta != 0)
		{
			si.fMask = SIF_POS;
			si.nPos = yPos;
			SetScrollInfo(hWnd, SB_VERT, &si, TRUE);
			// Scroll the window accordingly
			ScrollWindow(hWnd, 0, yDelta, NULL, NULL);
			// Update the window
			UpdateWindow(hWnd);
		}
	}
	break;

	case WM_HSCROLL:
	{
		// First, get the current scroll info for horizontal scrolling.
		si.fMask = SIF_ALL;
		GetScrollInfo(hWnd, SB_HORZ, &si);
		int xPos = si.nPos;
		int xDelta;

		switch (LOWORD(wParam))
		{
		case SB_LINELEFT:
			xPos--;
			break;
		case SB_LINERIGHT:
			xPos++;
			break;
		case SB_PAGELEFT:
			xPos -= si.nPage;
			break;
		case SB_PAGERIGHT:
			xPos += si.nPage;
			break;
		case SB_THUMBTRACK:
			xPos = HIWORD(wParam);
			break;
		default:
			break;
		}

		xPos = std::max(si.nMin, std::min(xPos, si.nMax - (int)si.nPage + 1));
		xDelta = si.nPos - xPos;

		if (xDelta != 0)
		{
			si.fMask = SIF_POS;
			si.nPos = xPos;
			SetScrollInfo(hWnd, SB_HORZ, &si, TRUE);
			ScrollWindow(hWnd, xDelta, 0, NULL, NULL);
			UpdateWindow(hWnd);
		}
	}
	break;

	case WM_COMMAND:
	{
		auto start_long = std::chrono::high_resolution_clock::now();
		int wmId = LOWORD(wParam);
		int wmEvent = HIWORD(wParam);
		// Parse the menu selections:
		switch (wmId)
		{
		case ID_BUTTON1: // this the RUN button for main otpimisation
			if (wmEvent == BN_CLICKED) {
				wchar_t buffer1[100];
				wchar_t buffer2[100];
				wchar_t buffer3[100];
				wchar_t buffer4[100];
				wchar_t buffer5[100];
				wchar_t buffer6[100];
				wchar_t buffer7[100];
				wchar_t buffer8[100];
				wchar_t buffer9[100];
				wchar_t buffer10[100];
				wchar_t buffer11[100];
				wchar_t buffer12[100];
				wchar_t buffer13[100];
				wchar_t buffer14[100];
				wchar_t buffer15[100];
				wchar_t buffer16[100];
				wchar_t buffer17[100];
				wchar_t buffer18[100];
				wchar_t buffer19[100];
				wchar_t buffer20[100];
				wchar_t buffer21[100];
				wchar_t buffer22[100];
				wchar_t buffer23[100];
				wchar_t buffer24[100];
				wchar_t buffer25[100];
				wchar_t buffer26[100];
				wchar_t buffer27[100];
				wchar_t buffer28[100];
				wchar_t buffer29[100];
				wchar_t buffer30[100];
				wchar_t buffer31[100];
				wchar_t buffer32[100];
				wchar_t buffer33[100];
				wchar_t buffer34[100];
				wchar_t buffer35[100];
				wchar_t buffer36[100];
				wchar_t buffer37[100];
				wchar_t buffer38[100];
				wchar_t buffer39[100];
				wchar_t buffer40[100];
				wchar_t buffer41[100];
				wchar_t buffer42[100];
				wchar_t buffer43[100];
				wchar_t buffer44[100];
				wchar_t buffer45[100];
				wchar_t buffer46[100];
				wchar_t buffer47[100];
				wchar_t buffer48[100];
				wchar_t buffer49[100];
				wchar_t buffer50[100];
				wchar_t buffer51[100];
				wchar_t buffer52[100];
				wchar_t buffer53[100];
				wchar_t buffer54[100];
				wchar_t buffer55[100];
				wchar_t buffer56[100];
				wchar_t buffer57[100];
				wchar_t buffer58[100];
				wchar_t buffer59[100];
				wchar_t buffer60[100];
				wchar_t buffer61[100];
				wchar_t buffer62[100];
				wchar_t buffer63[100];
				wchar_t buffer64[100];
				wchar_t buffer65[100];
				wchar_t buffer66[100];
				wchar_t buffer67[100];
				wchar_t buffer68[100];
				wchar_t buffer69[100];
				wchar_t buffer70[100];
				wchar_t buffer71[100];
				wchar_t buffer72[100];
				wchar_t buffer73[100];
				wchar_t buffer74[100];
				wchar_t buffer75[100];
				wchar_t buffer76[100];
				wchar_t buffer77[100];
				wchar_t buffer78[100];
				wchar_t buffer79[100];
				wchar_t buffer80[100];
				wchar_t buffer81[100];
				wchar_t buffer82[100];
				wchar_t buffer83[100];
				wchar_t buffer84[100];
				wchar_t buffer85[100];

				GetWindowText(hTextbox1, buffer1, 100);
				GetWindowText(hTextbox2, buffer2, 100);
				GetWindowText(hTextbox3, buffer3, 100);
				GetWindowText(hTextbox4, buffer4, 100);
				GetWindowText(hTextbox5, buffer5, 100);
				GetWindowText(hTextbox6, buffer6, 100);
				GetWindowText(hTextbox7, buffer7, 100);
				GetWindowText(hTextbox8, buffer8, 100);
				GetWindowText(hTextbox9, buffer9, 100);
				GetWindowText(hTextbox10, buffer10, 100);
				GetWindowText(hTextbox11, buffer11, 100);
				GetWindowText(hTextbox12, buffer12, 100);
				GetWindowText(hTextbox13, buffer13, 100);
				GetWindowText(hTextbox14, buffer14, 100);
				GetWindowText(hTextbox15, buffer15, 100);
				GetWindowText(hTextbox16, buffer16, 100);
				GetWindowText(hTextbox17, buffer17, 100);
				GetWindowText(hTextbox18, buffer18, 100);
				GetWindowText(hTextbox19, buffer19, 100);
				GetWindowText(hTextbox20, buffer20, 100);
				GetWindowText(hTextbox21, buffer21, 100);
				GetWindowText(hTextbox22, buffer22, 100);
				GetWindowText(hTextbox23, buffer23, 100);
				GetWindowText(hTextbox24, buffer24, 100);
				GetWindowText(hTextbox25, buffer25, 100);
				GetWindowText(hTextbox26, buffer26, 100);
				GetWindowText(hTextbox27, buffer27, 100);
				GetWindowText(hTextbox28, buffer28, 100);
				GetWindowText(hTextbox29, buffer29, 100);
				GetWindowText(hTextbox30, buffer30, 100);
				GetWindowText(hTextbox31, buffer31, 100);
				GetWindowText(hTextbox32, buffer32, 100);
				GetWindowText(hTextbox33, buffer33, 100);
				GetWindowText(hTextbox34, buffer34, 100);
				GetWindowText(hTextbox35, buffer35, 100);
				GetWindowText(hTextbox36, buffer36, 100);
				GetWindowText(hTextbox37, buffer37, 100);
				GetWindowText(hTextbox38, buffer38, 100);
				GetWindowText(hTextbox39, buffer39, 100);
				GetWindowText(hTextbox40, buffer40, 100);
				GetWindowText(hTextbox41, buffer41, 100);
				GetWindowText(hTextbox42, buffer42, 100);
				GetWindowText(hTextbox43, buffer43, 100);
				GetWindowText(hTextbox44, buffer44, 100);
				GetWindowText(hTextbox45, buffer45, 100);
				GetWindowText(hTextbox46, buffer46, 100);
				GetWindowText(hTextbox47, buffer47, 100);
				GetWindowText(hTextbox48, buffer48, 100);
				GetWindowText(hTextbox49, buffer49, 100);
				GetWindowText(hTextbox50, buffer50, 100);
				GetWindowText(hTextbox51, buffer51, 100);
				GetWindowText(hTextbox52, buffer52, 100);
				GetWindowText(hTextbox53, buffer53, 100);
				GetWindowText(hTextbox54, buffer54, 100);
				GetWindowText(hTextbox55, buffer55, 100);
				GetWindowText(hTextbox56, buffer56, 100);
				GetWindowText(hTextbox57, buffer57, 100);
				GetWindowText(hTextbox58, buffer58, 100);
				GetWindowText(hTextbox59, buffer59, 100);
				GetWindowText(hTextbox60, buffer60, 100);
				GetWindowText(hTextbox61, buffer61, 100);
				GetWindowText(hTextbox62, buffer62, 100);
				GetWindowText(hTextbox63, buffer63, 100);
				GetWindowText(hTextbox64, buffer64, 100);
				GetWindowText(hTextbox65, buffer65, 100);
				GetWindowText(hTextbox66, buffer66, 100);
				GetWindowText(hTextbox67, buffer67, 100);
				GetWindowText(hTextbox68, buffer68, 100);
				GetWindowText(hTextbox69, buffer69, 100);
				GetWindowText(hTextbox70, buffer70, 100);
				GetWindowText(hTextbox71, buffer71, 100);
				GetWindowText(hTextbox72, buffer72, 100);
				GetWindowText(hTextbox73, buffer73, 100);
				GetWindowText(hTextbox74, buffer74, 100);
				GetWindowText(hTextbox75, buffer75, 100);
				GetWindowText(hTextbox76, buffer76, 100);
				GetWindowText(hTextbox77, buffer77, 100);
				GetWindowText(hTextbox78, buffer78, 100);
				GetWindowText(hTextbox79, buffer79, 100);
				GetWindowText(hTextbox80, buffer80, 100);
				GetWindowText(hTextbox81, buffer81, 100);
				GetWindowText(hTextbox82, buffer82, 100);
				GetWindowText(hTextbox83, buffer83, 100);
				GetWindowText(hTextbox84, buffer84, 100);
				GetWindowText(hTextbox85, buffer85, 100);

				// ... retrieve text from more textboxes as needed

				//InputValues inputvalues =

				/*float BESS_Energy_lower = _wtof(buffer1);
				float BESS_Energy_upper = _wtof(buffer2);
				float BESS_Energy_step = _wtof(buffer3); */

				float timestep_minutes = static_cast<float>(_wtof(buffer4));
				
				float timestep_hours = static_cast<float>(_wtof(buffer5));
				float timewindow = static_cast<float>(_wtof(buffer6));

				float Fixed_load1_scalar_lower = static_cast<float>(_wtof(buffer7));
				float Fixed_load1_scalar_upper = static_cast<float>(_wtof(buffer8));
				float Fixed_load1_scalar_step = static_cast<float>(_wtof(buffer9));

				float Fixed_load2_scalar_lower = static_cast<float>(_wtof(buffer10));
				float Fixed_load2_scalar_upper = static_cast<float>(_wtof(buffer11));
				float Fixed_load2_scalar_step = static_cast<float>(_wtof(buffer12));

				float Flex_load_max_lower = static_cast<float>(_wtof(buffer13));
				float Flex_load_max_upper = static_cast<float>(_wtof(buffer14));
				float Flex_load_max_step = static_cast<float>(_wtof(buffer15));

				float Mop_load_max_lower = static_cast<float>(_wtof(buffer16));
				float Mop_load_max_upper = static_cast<float>(_wtof(buffer17));
				float Mop_load_max_step = static_cast<float>(_wtof(buffer18));

				float ScalarRG1_lower = static_cast<float>(_wtof(buffer19));
				float ScalarRG1_upper = static_cast<float>(_wtof(buffer20));
				float ScalarRG1_step = static_cast<float>(_wtof(buffer21));

				float ScalarRG2_lower = static_cast<float>(_wtof(buffer22));
				float ScalarRG2_upper = static_cast<float>(_wtof(buffer23));
				float ScalarRG2_step = static_cast<float>(_wtof(buffer24));

				float ScalarRG3_lower = static_cast<float>(_wtof(buffer25));
				float ScalarRG3_upper = static_cast<float>(_wtof(buffer26));
				float ScalarRG3_step = static_cast<float>(_wtof(buffer27));

				float ScalarRG4_lower = static_cast<float>(_wtof(buffer28));
				float ScalarRG4_upper = static_cast<float>(_wtof(buffer29));
				float ScalarRG4_step = static_cast<float>(_wtof(buffer30));

				float ScalarHL1_lower = static_cast<float>(_wtof(buffer31));
				float ScalarHL1_upper = static_cast<float>(_wtof(buffer32));
				float ScalarHL1_step = static_cast<float>(_wtof(buffer33));

				float ScalarHYield1_lower = static_cast<float>(_wtof(buffer34));
				float ScalarHYield1_upper = static_cast<float>(_wtof(buffer35));
				float ScalarHYield1_step = static_cast<float>(_wtof(buffer36));

				float ScalarHYield2_lower = static_cast<float>(_wtof(buffer37));
				float ScalarHYield2_upper = static_cast<float>(_wtof(buffer38));
				float ScalarHYield2_step = static_cast<float>(_wtof(buffer39));

				float ScalarHYield3_lower = static_cast<float>(_wtof(buffer40));
				float ScalarHYield3_upper = static_cast<float>(_wtof(buffer41));
				float ScalarHYield3_step = static_cast<float>(_wtof(buffer42));

				float ScalarHYield4_lower = static_cast<float>(_wtof(buffer43));
				float ScalarHYield4_upper = static_cast<float>(_wtof(buffer44));
				float ScalarHYield4_step = static_cast<float>(_wtof(buffer45));

				float GridImport_lower = static_cast<float>(_wtof(buffer46));
				float GridImport_upper = static_cast<float>(_wtof(buffer47));
				float GridImport_step = static_cast<float>(_wtof(buffer48));

				float GridExport_lower = static_cast<float>(_wtof(buffer49));
				float GridExport_upper = static_cast<float>(_wtof(buffer50));
				float GridExport_step = static_cast<float>(_wtof(buffer51));

				float Import_headroom_lower = static_cast<float>(_wtof(buffer52));
				float Import_headroom_upper = static_cast<float>(_wtof(buffer53));
				float Import_headroom_step = static_cast<float>(_wtof(buffer54));

				float Export_headroom_lower = static_cast<float>(_wtof(buffer55));
				float Export_headroom_upper = static_cast<float>(_wtof(buffer56));
				float Export_headroom_step = static_cast<float>(_wtof(buffer57));

				float ESS_charge_power_lower = static_cast<float>(_wtof(buffer58));
				float ESS_charge_power_upper = static_cast<float>(_wtof(buffer59));
				float ESS_charge_power_step = static_cast<float>(_wtof(buffer60));

				float ESS_discharge_power_lower = static_cast<float>(_wtof(buffer61));
				float ESS_discharge_power_upper = static_cast<float>(_wtof(buffer62));
				float ESS_discharge_power_step = static_cast<float>(_wtof(buffer63));

				float ESS_capacity_lower = static_cast<float>(_wtof(buffer64));
				float ESS_capacity_upper = static_cast<float>(_wtof(buffer65));
				float ESS_capacity_step = static_cast<float>(_wtof(buffer66));

				float ESS_RTE_lower = static_cast<float>(_wtof(buffer67));
				float ESS_RTE_upper = static_cast<float>(_wtof(buffer68));
				float ESS_RTE_step = static_cast<float>(_wtof(buffer69));

				float ESS_aux_load_lower = static_cast<float>(_wtof(buffer70));
				float ESS_aux_load_upper = static_cast<float>(_wtof(buffer71));
				float ESS_aux_load_step = static_cast<float>(_wtof(buffer72)); // JSM changed ESS_aux_step to ESS_aux_load_step

				float ESS_start_SoC_lower = static_cast<float>(_wtof(buffer73));
				float ESS_start_SoC_upper = static_cast<float>(_wtof(buffer74));
				float ESS_start_SoC_step = static_cast<float>(_wtof(buffer75));

				int ESS_charge_mode_lower = static_cast<int>(_wtoi(buffer76));
				int ESS_charge_mode_upper = static_cast<int>(_wtoi(buffer77));

				int ESS_discharge_mode_lower = static_cast<int>(_wtoi(buffer78));
				int ESS_discharge_mode_upper = static_cast<int>(_wtoi(buffer79));

				float import_kWh_price = static_cast<float>(_wtof(buffer80));
				float export_kWh_price = static_cast<float>(_wtof(buffer81));

				float time_budget_min = static_cast<float>(_wtof(buffer82));

				int target_max_concurrency = static_cast<float>(_wtoi(buffer83));

				float CAPEX_limit = static_cast<float>(_wtof(buffer84));
				float OPEX_limit = static_cast<float>(_wtof(buffer85));

				InitConsole();

				InputValues inputvalues = {
	timestep_minutes, timestep_hours, timewindow,
	Fixed_load1_scalar_lower, Fixed_load1_scalar_upper, Fixed_load1_scalar_step,
	Fixed_load2_scalar_lower, Fixed_load2_scalar_upper, Fixed_load2_scalar_step,
	Flex_load_max_lower, Flex_load_max_upper, Flex_load_max_step,
	Mop_load_max_lower, Mop_load_max_upper, Mop_load_max_step,
	ScalarRG1_lower, ScalarRG1_upper, ScalarRG1_step,
	ScalarRG2_lower, ScalarRG2_upper, ScalarRG2_step,
	ScalarRG3_lower, ScalarRG3_upper, ScalarRG3_step,
	ScalarRG4_lower, ScalarRG4_upper, ScalarRG4_step,
	ScalarHL1_lower, ScalarHL1_upper, ScalarHL1_step,
	ScalarHYield1_lower, ScalarHYield1_upper, ScalarHYield1_step,
	ScalarHYield2_lower, ScalarHYield2_upper, ScalarHYield2_step,
	ScalarHYield3_lower, ScalarHYield3_upper, ScalarHYield3_step,
	ScalarHYield4_lower, ScalarHYield4_upper, ScalarHYield4_step,
	GridImport_lower, GridImport_upper, GridImport_step,
	GridExport_lower, GridExport_upper, GridExport_step,
	Import_headroom_lower, Import_headroom_upper, Import_headroom_step,
	Export_headroom_lower, Export_headroom_upper, Export_headroom_step,
	ESS_charge_power_lower, ESS_charge_power_upper, ESS_charge_power_step,
	ESS_discharge_power_lower, ESS_discharge_power_upper, ESS_discharge_power_step,
	ESS_capacity_lower, ESS_capacity_upper, ESS_capacity_step,
	ESS_RTE_lower, ESS_RTE_upper, ESS_RTE_step,
	ESS_aux_load_lower, ESS_aux_load_upper, ESS_aux_load_step,
	ESS_start_SoC_lower, ESS_start_SoC_upper, ESS_start_SoC_step,
	ESS_charge_mode_lower, ESS_charge_mode_upper,
	ESS_discharge_mode_lower, ESS_discharge_mode_upper,
	import_kWh_price, export_kWh_price,
	time_budget_min, target_max_concurrency,
	CAPEX_limit, OPEX_limit
				};

				/* ==== JSM CODE HERE ==================================================================== */
				// Aim: to export 'inputvalues' to a json file that can be read e.g. as a Python dict, s.t. other EPL software can use this as an input
				// These are 2 lines to produce debug output -- not functionally important!
				//std::cout << "Hello. We are here now." << std::endl;
				//std::cout << inputvalues.ESS_aux_load_lower << std::endl;

				// Convert the InputValues struct to a JSON object using the mapping
				nlohmann::json jsonObj = structToJson(inputvalues, memberMappings, std::size(memberMappings));

				// Write the JSON to a file
				std::ofstream file("parameters.json");
				file << jsonObj.dump(4); // The "4" argument adds pretty-printing with indentation
				file.close();

				nlohmann::json converted_json = convert_to_ranges(jsonObj);
				std::ofstream file3("parameters_grouped.json");
				file3 << converted_json.dump(4); // The "4" argument adds pretty-printing with indentation
				file3.close();

				std::cout << "JSON file written successfully!" << std::endl;
				/* ======================================================================================== */

				OutputValues output = RunMainOptimisation(converted_json);
				std::cout << "Output.Max: " << output.maxVal << ", Output.Min: " << output.minVal << ", Output.Mean: " << output.meanVal << std::endl;
				wchar_t buffer[300];
				swprintf_s(buffer, 300, L"%f", output.maxVal);
				SetWindowText(hOutput1, buffer);
				swprintf_s(buffer, 300, L"%f", output.minVal);
				SetWindowText(hOutput2, buffer);
				swprintf_s(buffer, 300, L"%f", output.meanVal);
				SetWindowText(hOutput3, buffer);

				swprintf_s(buffer, 300, L"%f", output.CAPEX);
				SetWindowText(hOutput5, buffer);
				swprintf_s(buffer, 300, L"%f", output.annualised);
				SetWindowText(hOutput6, buffer);
				swprintf_s(buffer, 300, L"%f", output.scenario_cost_balance);
				SetWindowText(hOutput7, buffer);

				swprintf_s(buffer, 300, L"%f", output.payback_horizon);
				SetWindowText(hOutput8, buffer);
				swprintf_s(buffer, 300, L"%f", output.scenario_carbon_balance);
				SetWindowText(hOutput9, buffer);
				
				swprintf_s(buffer, 300, L"%d", output.CAPEX_index);
				SetWindowText(hOutput13, buffer);
				swprintf_s(buffer, 300, L"%d", output.annualised_index);
				SetWindowText(hOutput14, buffer);
				swprintf_s(buffer, 300, L"%d", output.scenario_cost_balance_index);
				SetWindowText(hOutput15, buffer);
				swprintf_s(buffer, 300, L"%d", output.payback_horizon_index);
				SetWindowText(hOutput16, buffer);
				swprintf_s(buffer, 300, L"%d", output.scenario_carbon_balance_index);
				SetWindowText(hOutput17, buffer);


				// Convert the InputValues struct to a JSON object using the mapping
				nlohmann::json jsonObj2 = structToJsonOut(output, OutmemberMappings, std::size(OutmemberMappings));

				// Write the JSON to a file
				std::ofstream file2("outputparameters.json");
				file2 << jsonObj2.dump(4); // The "4" argument adds pretty-printing with indentation
				file2.close();

				std::cout << "JSON file written successfully!" << std::endl;

				auto end_long = std::chrono::high_resolution_clock::now();
				std::chrono::duration<double> total_elapsed = end_long - start_long;  // calculate total elaspsed run time
				std::cout << "Total Runtime: " << total_elapsed.count() << " seconds" << std::endl; // print elapsed run time
				float elapsed_float = static_cast<float>(total_elapsed.count());
				swprintf_s(buffer, 300, L"%f", elapsed_float);
				SetWindowText(hOutput4, buffer);

				std::cout << "Sleeping for 5 seconds..."; // this allows time to read the console if needed. Adjust if needed
				//std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n'); // Clear the input buffer
				//std::cin.get(); // Wait for keystroke

				std::this_thread::sleep_for(std::chrono::seconds(5));


			}
			CloseConsole();
			break;

		case ID_BUTTON0: // this is the INITIALISE button to estimate the optimisation time
			if (wmEvent == BN_CLICKED) {
				wchar_t buffer1[100];
				wchar_t buffer2[100];
				wchar_t buffer3[100];
				wchar_t buffer4[100];
				wchar_t buffer5[100];
				wchar_t buffer6[100];
				wchar_t buffer7[100];
				wchar_t buffer8[100];
				wchar_t buffer9[100];
				wchar_t buffer10[100];
				wchar_t buffer11[100];
				wchar_t buffer12[100];
				wchar_t buffer13[100];
				wchar_t buffer14[100];
				wchar_t buffer15[100];
				wchar_t buffer16[100];
				wchar_t buffer17[100];
				wchar_t buffer18[100];
				wchar_t buffer19[100];
				wchar_t buffer20[100];
				wchar_t buffer21[100];
				wchar_t buffer22[100];
				wchar_t buffer23[100];
				wchar_t buffer24[100];
				wchar_t buffer25[100];
				wchar_t buffer26[100];
				wchar_t buffer27[100];
				wchar_t buffer28[100];
				wchar_t buffer29[100];
				wchar_t buffer30[100];
				wchar_t buffer31[100];
				wchar_t buffer32[100];
				wchar_t buffer33[100];
				wchar_t buffer34[100];
				wchar_t buffer35[100];
				wchar_t buffer36[100];
				wchar_t buffer37[100];
				wchar_t buffer38[100];
				wchar_t buffer39[100];
				wchar_t buffer40[100];
				wchar_t buffer41[100];
				wchar_t buffer42[100];
				wchar_t buffer43[100];
				wchar_t buffer44[100];
				wchar_t buffer45[100];
				wchar_t buffer46[100];
				wchar_t buffer47[100];
				wchar_t buffer48[100];
				wchar_t buffer49[100];
				wchar_t buffer50[100];
				wchar_t buffer51[100];
				wchar_t buffer52[100];
				wchar_t buffer53[100];
				wchar_t buffer54[100];
				wchar_t buffer55[100];
				wchar_t buffer56[100];
				wchar_t buffer57[100];
				wchar_t buffer58[100];
				wchar_t buffer59[100];
				wchar_t buffer60[100];
				wchar_t buffer61[100];
				wchar_t buffer62[100];
				wchar_t buffer63[100];
				wchar_t buffer64[100];
				wchar_t buffer65[100];
				wchar_t buffer66[100];
				wchar_t buffer67[100];
				wchar_t buffer68[100];
				wchar_t buffer69[100];
				wchar_t buffer70[100];
				wchar_t buffer71[100];
				wchar_t buffer72[100];
				wchar_t buffer73[100];
				wchar_t buffer74[100];
				wchar_t buffer75[100];
				wchar_t buffer76[100];
				wchar_t buffer77[100];
				wchar_t buffer78[100];
				wchar_t buffer79[100];
				wchar_t buffer80[100];
				wchar_t buffer81[100];
				wchar_t buffer82[100];
				wchar_t buffer83[100];
				wchar_t buffer84[100];
				wchar_t buffer85[100];

				GetWindowText(hTextbox1, buffer1, 100);
				GetWindowText(hTextbox2, buffer2, 100);
				GetWindowText(hTextbox3, buffer3, 100);
				GetWindowText(hTextbox4, buffer4, 100);
				GetWindowText(hTextbox5, buffer5, 100);
				GetWindowText(hTextbox6, buffer6, 100);
				GetWindowText(hTextbox7, buffer7, 100);
				GetWindowText(hTextbox8, buffer8, 100);
				GetWindowText(hTextbox9, buffer9, 100);
				GetWindowText(hTextbox10, buffer10, 100);
				GetWindowText(hTextbox11, buffer11, 100);
				GetWindowText(hTextbox12, buffer12, 100);
				GetWindowText(hTextbox13, buffer13, 100);
				GetWindowText(hTextbox14, buffer14, 100);
				GetWindowText(hTextbox15, buffer15, 100);
				GetWindowText(hTextbox16, buffer16, 100);
				GetWindowText(hTextbox17, buffer17, 100);
				GetWindowText(hTextbox18, buffer18, 100);
				GetWindowText(hTextbox19, buffer19, 100);
				GetWindowText(hTextbox20, buffer20, 100);
				GetWindowText(hTextbox21, buffer21, 100);
				GetWindowText(hTextbox22, buffer22, 100);
				GetWindowText(hTextbox23, buffer23, 100);
				GetWindowText(hTextbox24, buffer24, 100);
				GetWindowText(hTextbox25, buffer25, 100);
				GetWindowText(hTextbox26, buffer26, 100);
				GetWindowText(hTextbox27, buffer27, 100);
				GetWindowText(hTextbox28, buffer28, 100);
				GetWindowText(hTextbox29, buffer29, 100);
				GetWindowText(hTextbox30, buffer30, 100);
				GetWindowText(hTextbox31, buffer31, 100);
				GetWindowText(hTextbox32, buffer32, 100);
				GetWindowText(hTextbox33, buffer33, 100);
				GetWindowText(hTextbox34, buffer34, 100);
				GetWindowText(hTextbox35, buffer35, 100);
				GetWindowText(hTextbox36, buffer36, 100);
				GetWindowText(hTextbox37, buffer37, 100);
				GetWindowText(hTextbox38, buffer38, 100);
				GetWindowText(hTextbox39, buffer39, 100);
				GetWindowText(hTextbox40, buffer40, 100);
				GetWindowText(hTextbox41, buffer41, 100);
				GetWindowText(hTextbox42, buffer42, 100);
				GetWindowText(hTextbox43, buffer43, 100);
				GetWindowText(hTextbox44, buffer44, 100);
				GetWindowText(hTextbox45, buffer45, 100);
				GetWindowText(hTextbox46, buffer46, 100);
				GetWindowText(hTextbox47, buffer47, 100);
				GetWindowText(hTextbox48, buffer48, 100);
				GetWindowText(hTextbox49, buffer49, 100);
				GetWindowText(hTextbox50, buffer50, 100);
				GetWindowText(hTextbox51, buffer51, 100);
				GetWindowText(hTextbox52, buffer52, 100);
				GetWindowText(hTextbox53, buffer53, 100);
				GetWindowText(hTextbox54, buffer54, 100);
				GetWindowText(hTextbox55, buffer55, 100);
				GetWindowText(hTextbox56, buffer56, 100);
				GetWindowText(hTextbox57, buffer57, 100);
				GetWindowText(hTextbox58, buffer58, 100);
				GetWindowText(hTextbox59, buffer59, 100);
				GetWindowText(hTextbox60, buffer60, 100);
				GetWindowText(hTextbox61, buffer61, 100);
				GetWindowText(hTextbox62, buffer62, 100);
				GetWindowText(hTextbox63, buffer63, 100);
				GetWindowText(hTextbox64, buffer64, 100);
				GetWindowText(hTextbox65, buffer65, 100);
				GetWindowText(hTextbox66, buffer66, 100);
				GetWindowText(hTextbox67, buffer67, 100);
				GetWindowText(hTextbox68, buffer68, 100);
				GetWindowText(hTextbox69, buffer69, 100);
				GetWindowText(hTextbox70, buffer70, 100);
				GetWindowText(hTextbox71, buffer71, 100);
				GetWindowText(hTextbox72, buffer72, 100);
				GetWindowText(hTextbox73, buffer73, 100);
				GetWindowText(hTextbox74, buffer74, 100);
				GetWindowText(hTextbox75, buffer75, 100);
				GetWindowText(hTextbox76, buffer76, 100);
				GetWindowText(hTextbox77, buffer77, 100);
				GetWindowText(hTextbox78, buffer78, 100);
				GetWindowText(hTextbox79, buffer79, 100);
				GetWindowText(hTextbox80, buffer80, 100);
				GetWindowText(hTextbox81, buffer81, 100);
				GetWindowText(hTextbox82, buffer82, 100);
				GetWindowText(hTextbox83, buffer83, 100);
				GetWindowText(hTextbox84, buffer84, 100);
				GetWindowText(hTextbox85, buffer85, 100);

				// ... retrieve text from more textboxes as needed

				//InputValues inputvalues =

				/*float BESS_Energy_lower = _wtof(buffer1);
				float BESS_Energy_upper = _wtof(buffer2);
				float BESS_Energy_step = _wtof(buffer3); */

				float timestep_minutes = static_cast<float>(_wtof(buffer4));

				float timestep_hours = static_cast<float>(_wtof(buffer5));
				float timewindow = static_cast<float>(_wtof(buffer6));

				float Fixed_load1_scalar_lower = static_cast<float>(_wtof(buffer7));
				float Fixed_load1_scalar_upper = static_cast<float>(_wtof(buffer8));
				float Fixed_load1_scalar_step = static_cast<float>(_wtof(buffer9));

				float Fixed_load2_scalar_lower = static_cast<float>(_wtof(buffer10));
				float Fixed_load2_scalar_upper = static_cast<float>(_wtof(buffer11));
				float Fixed_load2_scalar_step = static_cast<float>(_wtof(buffer12));

				float Flex_load_max_lower = static_cast<float>(_wtof(buffer13));
				float Flex_load_max_upper = static_cast<float>(_wtof(buffer14));
				float Flex_load_max_step = static_cast<float>(_wtof(buffer15));

				float Mop_load_max_lower = static_cast<float>(_wtof(buffer16));
				float Mop_load_max_upper = static_cast<float>(_wtof(buffer17));
				float Mop_load_max_step = static_cast<float>(_wtof(buffer18));

				float ScalarRG1_lower = static_cast<float>(_wtof(buffer19));
				float ScalarRG1_upper = static_cast<float>(_wtof(buffer20));
				float ScalarRG1_step = static_cast<float>(_wtof(buffer21));

				float ScalarRG2_lower = static_cast<float>(_wtof(buffer22));
				float ScalarRG2_upper = static_cast<float>(_wtof(buffer23));
				float ScalarRG2_step = static_cast<float>(_wtof(buffer24));

				float ScalarRG3_lower = static_cast<float>(_wtof(buffer25));
				float ScalarRG3_upper = static_cast<float>(_wtof(buffer26));
				float ScalarRG3_step = static_cast<float>(_wtof(buffer27));

				float ScalarRG4_lower = static_cast<float>(_wtof(buffer28));
				float ScalarRG4_upper = static_cast<float>(_wtof(buffer29));
				float ScalarRG4_step = static_cast<float>(_wtof(buffer30));

				float ScalarHL1_lower = static_cast<float>(_wtof(buffer31));
				float ScalarHL1_upper = static_cast<float>(_wtof(buffer32));
				float ScalarHL1_step = static_cast<float>(_wtof(buffer33));

				float ScalarHYield1_lower = static_cast<float>(_wtof(buffer34));
				float ScalarHYield1_upper = static_cast<float>(_wtof(buffer35));
				float ScalarHYield1_step = static_cast<float>(_wtof(buffer36));

				float ScalarHYield2_lower = static_cast<float>(_wtof(buffer37));
				float ScalarHYield2_upper = static_cast<float>(_wtof(buffer38));
				float ScalarHYield2_step = static_cast<float>(_wtof(buffer39));

				float ScalarHYield3_lower = static_cast<float>(_wtof(buffer40));
				float ScalarHYield3_upper = static_cast<float>(_wtof(buffer41));
				float ScalarHYield3_step = static_cast<float>(_wtof(buffer42));

				float ScalarHYield4_lower = static_cast<float>(_wtof(buffer43));
				float ScalarHYield4_upper = static_cast<float>(_wtof(buffer44));
				float ScalarHYield4_step = static_cast<float>(_wtof(buffer45));

				float GridImport_lower = static_cast<float>(_wtof(buffer46));
				float GridImport_upper = static_cast<float>(_wtof(buffer47));
				float GridImport_step = static_cast<float>(_wtof(buffer48));

				float GridExport_lower = static_cast<float>(_wtof(buffer49));
				float GridExport_upper = static_cast<float>(_wtof(buffer50));
				float GridExport_step = static_cast<float>(_wtof(buffer51));

				float Import_headroom_lower = static_cast<float>(_wtof(buffer52));
				float Import_headroom_upper = static_cast<float>(_wtof(buffer53));
				float Import_headroom_step = static_cast<float>(_wtof(buffer54));

				float Export_headroom_lower = static_cast<float>(_wtof(buffer55));
				float Export_headroom_upper = static_cast<float>(_wtof(buffer56));
				float Export_headroom_step = static_cast<float>(_wtof(buffer57));

				float ESS_charge_power_lower = static_cast<float>(_wtof(buffer58));
				float ESS_charge_power_upper = static_cast<float>(_wtof(buffer59));
				float ESS_charge_power_step = static_cast<float>(_wtof(buffer60));

				float ESS_discharge_power_lower = static_cast<float>(_wtof(buffer61));
				float ESS_discharge_power_upper = static_cast<float>(_wtof(buffer62));
				float ESS_discharge_power_step = static_cast<float>(_wtof(buffer63));

				float ESS_capacity_lower = static_cast<float>(_wtof(buffer64));
				float ESS_capacity_upper = static_cast<float>(_wtof(buffer65));
				float ESS_capacity_step = static_cast<float>(_wtof(buffer66));

				float ESS_RTE_lower = static_cast<float>(_wtof(buffer67));
				float ESS_RTE_upper = static_cast<float>(_wtof(buffer68));
				float ESS_RTE_step = static_cast<float>(_wtof(buffer69));

				float ESS_aux_load_lower = static_cast<float>(_wtof(buffer70));
				float ESS_aux_load_upper = static_cast<float>(_wtof(buffer71));
				float ESS_aux_load_step = static_cast<float>(_wtof(buffer72)); // JSM changed ESS_aux_step to ESS_aux_load_step

				float ESS_start_SoC_lower = static_cast<float>(_wtof(buffer73));
				float ESS_start_SoC_upper = static_cast<float>(_wtof(buffer74));
				float ESS_start_SoC_step = static_cast<float>(_wtof(buffer75));

				int ESS_charge_mode_lower = static_cast<int>(_wtoi(buffer76));
				int ESS_charge_mode_upper = static_cast<int>(_wtoi(buffer77));

				int ESS_discharge_mode_lower = static_cast<int>(_wtoi(buffer78));
				int ESS_discharge_mode_upper = static_cast<int>(_wtoi(buffer79));

				float import_kWh_price = static_cast<float>(_wtof(buffer80));
				float export_kWh_price = static_cast<float>(_wtof(buffer81));

				float time_budget_min = static_cast<float>(_wtof(buffer82));

				int target_max_concurrency = static_cast<float>(_wtoi(buffer83));

				float CAPEX_limit = static_cast<float>(_wtof(buffer84));
				float OPEX_limit = static_cast<float>(_wtof(buffer85));

				InitConsole();

				InputValues inputvalues = {
	timestep_minutes, timestep_hours, timewindow,
	Fixed_load1_scalar_lower, Fixed_load1_scalar_upper, Fixed_load1_scalar_step,
	Fixed_load2_scalar_lower, Fixed_load2_scalar_upper, Fixed_load2_scalar_step,
	Flex_load_max_lower, Flex_load_max_upper, Flex_load_max_step,
	Mop_load_max_lower, Mop_load_max_upper, Mop_load_max_step,
	ScalarRG1_lower, ScalarRG1_upper, ScalarRG1_step,
	ScalarRG2_lower, ScalarRG2_upper, ScalarRG2_step,
	ScalarRG3_lower, ScalarRG3_upper, ScalarRG3_step,
	ScalarRG4_lower, ScalarRG4_upper, ScalarRG4_step,
	ScalarHL1_lower, ScalarHL1_upper, ScalarHL1_step,
	ScalarHYield1_lower, ScalarHYield1_upper, ScalarHYield1_step,
	ScalarHYield2_lower, ScalarHYield2_upper, ScalarHYield2_step,
	ScalarHYield3_lower, ScalarHYield3_upper, ScalarHYield3_step,
	ScalarHYield4_lower, ScalarHYield4_upper, ScalarHYield4_step,
	GridImport_lower, GridImport_upper, GridImport_step,
	GridExport_lower, GridExport_upper, GridExport_step,
	Import_headroom_lower, Import_headroom_upper, Import_headroom_step,
	Export_headroom_lower, Export_headroom_upper, Export_headroom_step,
	ESS_charge_power_lower, ESS_charge_power_upper, ESS_charge_power_step,
	ESS_discharge_power_lower, ESS_discharge_power_upper, ESS_discharge_power_step,
	ESS_capacity_lower, ESS_capacity_upper, ESS_capacity_step,
	ESS_RTE_lower, ESS_RTE_upper, ESS_RTE_step,
	ESS_aux_load_lower, ESS_aux_load_upper, ESS_aux_load_step,
	ESS_start_SoC_lower, ESS_start_SoC_upper, ESS_start_SoC_step,
	ESS_charge_mode_lower, ESS_charge_mode_upper,
	ESS_discharge_mode_lower, ESS_discharge_mode_upper,
	import_kWh_price, export_kWh_price,
	time_budget_min, target_max_concurrency,
	CAPEX_limit, OPEX_limit
				};

				/* ==== JSM CODE HERE ==================================================================== */
				// Aim: to export 'inputvalues' to a json file that can be read e.g. as a Python dict, s.t. other EPL software can use this as an input
				// These are 2 lines to produce debug output -- not functionally important!
				//std::cout << "Hello. We are here now." << std::endl;
				//std::cout << inputvalues.ESS_aux_load_lower << std::endl;

				// Convert the InputValues struct to a JSON object using the mapping
				nlohmann::json jsonObj = structToJson(inputvalues, memberMappings, std::size(memberMappings));

				// Write the JSON to a file
				std::ofstream file("parameters.json");
				file << jsonObj.dump(4); // The "4" argument adds pretty-printing with indentation
				file.close();

				nlohmann::json converted_json = convert_to_ranges(jsonObj);
				std::ofstream file3("parameters_grouped.json");
				file3 << converted_json.dump(4); // The "4" argument adds pretty-printing with indentation
				file3.close();

				std::cout << "JSON file written successfully!" << std::endl;
				/* ======================================================================================== */

				//OutputValues output = RunMainOptimisation(converted_json);

				OutputValues output = InitialiseOptimisation(converted_json);

				//std::cout << "Output.Max: " << output.maxVal << ", Output.Min: " << output.minVal << ", Output.Mean: " << output.meanVal << std::endl;
				wchar_t buffer[300];
				swprintf_s(buffer, 300, L"%i", output.num_scenarios);
				SetWindowText(hOutput10, buffer);
				swprintf_s(buffer, 300, L"%f", output.est_hours);
				SetWindowText(hOutput11, buffer);
				swprintf_s(buffer, 300, L"%f", output.est_seconds);
				SetWindowText(hOutput12, buffer);

				// Convert the InputValues struct to a JSON object using the mapping
				nlohmann::json jsonObj2 = structToJsonOut(output, OutmemberMappings, std::size(OutmemberMappings));

				// Write the JSON to a file
				std::ofstream file2("outputparameters_init.json");
				file2 << jsonObj2.dump(4); // The "4" argument adds pretty-printing with indentation
				file2.close();

				std::cout << "JSON file written successfully!" << std::endl;


				auto end_long = std::chrono::high_resolution_clock::now();
				std::chrono::duration<double> total_elapsed = end_long - start_long;  // calculate total elaspsed run time
				std::cout << "Total Runtime: " << total_elapsed.count() << " seconds" << std::endl; // print elapsed run time
				float elapsed_float = static_cast<float>(total_elapsed.count());
				swprintf_s(buffer, 300, L"%f", elapsed_float);
				SetWindowText(hOutput4, buffer);

				std::cout << "Sleeping for 1 seconds..."; // this allows time to read the console if needed. Adjust if needed
				//std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n'); // Clear the input buffer
				//std::cin.get(); // Wait for keystroke

				std::this_thread::sleep_for(std::chrono::seconds(1));

			}
			CloseConsole();
			break;

		case ID_BUTTON2: // this is the RECALL button to recall a parameter slice by index
			if (wmEvent == BN_CLICKED) {
				{
					wchar_t buffer1[100];
					wchar_t buffer2[100];
					wchar_t buffer3[100];
					wchar_t buffer4[100];
					wchar_t buffer5[100];
					wchar_t buffer6[100];
					wchar_t buffer7[100];
					wchar_t buffer8[100];
					wchar_t buffer9[100];
					wchar_t buffer10[100];
					wchar_t buffer11[100];
					wchar_t buffer12[100];
					wchar_t buffer13[100];
					wchar_t buffer14[100];
					wchar_t buffer15[100];
					wchar_t buffer16[100];
					wchar_t buffer17[100];
					wchar_t buffer18[100];
					wchar_t buffer19[100];
					wchar_t buffer20[100];
					wchar_t buffer21[100];
					wchar_t buffer22[100];
					wchar_t buffer23[100];
					wchar_t buffer24[100];
					wchar_t buffer25[100];
					wchar_t buffer26[100];
					wchar_t buffer27[100];
					wchar_t buffer28[100];
					wchar_t buffer29[100];
					wchar_t buffer30[100];
					wchar_t buffer31[100];
					wchar_t buffer32[100];
					wchar_t buffer33[100];
					wchar_t buffer34[100];
					wchar_t buffer35[100];
					wchar_t buffer36[100];
					wchar_t buffer37[100];
					wchar_t buffer38[100];
					wchar_t buffer39[100];
					wchar_t buffer40[100];
					wchar_t buffer41[100];
					wchar_t buffer42[100];
					wchar_t buffer43[100];
					wchar_t buffer44[100];
					wchar_t buffer45[100];
					wchar_t buffer46[100];
					wchar_t buffer47[100];
					wchar_t buffer48[100];
					wchar_t buffer49[100];
					wchar_t buffer50[100];
					wchar_t buffer51[100];
					wchar_t buffer52[100];
					wchar_t buffer53[100];
					wchar_t buffer54[100];
					wchar_t buffer55[100];
					wchar_t buffer56[100];
					wchar_t buffer57[100];
					wchar_t buffer58[100];
					wchar_t buffer59[100];
					wchar_t buffer60[100];
					wchar_t buffer61[100];
					wchar_t buffer62[100];
					wchar_t buffer63[100];
					wchar_t buffer64[100];
					wchar_t buffer65[100];
					wchar_t buffer66[100];
					wchar_t buffer67[100];
					wchar_t buffer68[100];
					wchar_t buffer69[100];
					wchar_t buffer70[100];
					wchar_t buffer71[100];
					wchar_t buffer72[100];
					wchar_t buffer73[100];
					wchar_t buffer74[100];
					wchar_t buffer75[100];
					wchar_t buffer76[100];
					wchar_t buffer77[100];
					wchar_t buffer78[100];
					wchar_t buffer79[100];
					wchar_t buffer80[100];
					wchar_t buffer81[100];
					wchar_t buffer82[100];
					wchar_t buffer83[100];
					wchar_t buffer84[100];
					wchar_t buffer85[100];

					GetWindowText(hTextbox1, buffer1, 100);
					GetWindowText(hTextbox2, buffer2, 100);
					GetWindowText(hTextbox3, buffer3, 100);
					GetWindowText(hTextbox4, buffer4, 100);
					GetWindowText(hTextbox5, buffer5, 100);
					GetWindowText(hTextbox6, buffer6, 100);
					GetWindowText(hTextbox7, buffer7, 100);
					GetWindowText(hTextbox8, buffer8, 100);
					GetWindowText(hTextbox9, buffer9, 100);
					GetWindowText(hTextbox10, buffer10, 100);
					GetWindowText(hTextbox11, buffer11, 100);
					GetWindowText(hTextbox12, buffer12, 100);
					GetWindowText(hTextbox13, buffer13, 100);
					GetWindowText(hTextbox14, buffer14, 100);
					GetWindowText(hTextbox15, buffer15, 100);
					GetWindowText(hTextbox16, buffer16, 100);
					GetWindowText(hTextbox17, buffer17, 100);
					GetWindowText(hTextbox18, buffer18, 100);
					GetWindowText(hTextbox19, buffer19, 100);
					GetWindowText(hTextbox20, buffer20, 100);
					GetWindowText(hTextbox21, buffer21, 100);
					GetWindowText(hTextbox22, buffer22, 100);
					GetWindowText(hTextbox23, buffer23, 100);
					GetWindowText(hTextbox24, buffer24, 100);
					GetWindowText(hTextbox25, buffer25, 100);
					GetWindowText(hTextbox26, buffer26, 100);
					GetWindowText(hTextbox27, buffer27, 100);
					GetWindowText(hTextbox28, buffer28, 100);
					GetWindowText(hTextbox29, buffer29, 100);
					GetWindowText(hTextbox30, buffer30, 100);
					GetWindowText(hTextbox31, buffer31, 100);
					GetWindowText(hTextbox32, buffer32, 100);
					GetWindowText(hTextbox33, buffer33, 100);
					GetWindowText(hTextbox34, buffer34, 100);
					GetWindowText(hTextbox35, buffer35, 100);
					GetWindowText(hTextbox36, buffer36, 100);
					GetWindowText(hTextbox37, buffer37, 100);
					GetWindowText(hTextbox38, buffer38, 100);
					GetWindowText(hTextbox39, buffer39, 100);
					GetWindowText(hTextbox40, buffer40, 100);
					GetWindowText(hTextbox41, buffer41, 100);
					GetWindowText(hTextbox42, buffer42, 100);
					GetWindowText(hTextbox43, buffer43, 100);
					GetWindowText(hTextbox44, buffer44, 100);
					GetWindowText(hTextbox45, buffer45, 100);
					GetWindowText(hTextbox46, buffer46, 100);
					GetWindowText(hTextbox47, buffer47, 100);
					GetWindowText(hTextbox48, buffer48, 100);
					GetWindowText(hTextbox49, buffer49, 100);
					GetWindowText(hTextbox50, buffer50, 100);
					GetWindowText(hTextbox51, buffer51, 100);
					GetWindowText(hTextbox52, buffer52, 100);
					GetWindowText(hTextbox53, buffer53, 100);
					GetWindowText(hTextbox54, buffer54, 100);
					GetWindowText(hTextbox55, buffer55, 100);
					GetWindowText(hTextbox56, buffer56, 100);
					GetWindowText(hTextbox57, buffer57, 100);
					GetWindowText(hTextbox58, buffer58, 100);
					GetWindowText(hTextbox59, buffer59, 100);
					GetWindowText(hTextbox60, buffer60, 100);
					GetWindowText(hTextbox61, buffer61, 100);
					GetWindowText(hTextbox62, buffer62, 100);
					GetWindowText(hTextbox63, buffer63, 100);
					GetWindowText(hTextbox64, buffer64, 100);
					GetWindowText(hTextbox65, buffer65, 100);
					GetWindowText(hTextbox66, buffer66, 100);
					GetWindowText(hTextbox67, buffer67, 100);
					GetWindowText(hTextbox68, buffer68, 100);
					GetWindowText(hTextbox69, buffer69, 100);
					GetWindowText(hTextbox70, buffer70, 100);
					GetWindowText(hTextbox71, buffer71, 100);
					GetWindowText(hTextbox72, buffer72, 100);
					GetWindowText(hTextbox73, buffer73, 100);
					GetWindowText(hTextbox74, buffer74, 100);
					GetWindowText(hTextbox75, buffer75, 100);
					GetWindowText(hTextbox76, buffer76, 100);
					GetWindowText(hTextbox77, buffer77, 100);
					GetWindowText(hTextbox78, buffer78, 100);
					GetWindowText(hTextbox79, buffer79, 100);
					GetWindowText(hTextbox80, buffer80, 100);
					GetWindowText(hTextbox81, buffer81, 100);
					GetWindowText(hTextbox82, buffer82, 100);
					GetWindowText(hTextbox83, buffer83, 100);
					GetWindowText(hTextbox84, buffer84, 100);
					GetWindowText(hTextbox85, buffer85, 100);

					// ... retrieve text from more textboxes as needed

					//InputValues inputvalues =

					/*float BESS_Energy_lower = _wtof(buffer1);
					float BESS_Energy_upper = _wtof(buffer2);
					float BESS_Energy_step = _wtof(buffer3); */

					float timestep_minutes = static_cast<float>(_wtof(buffer4));

					float timestep_hours = static_cast<float>(_wtof(buffer5));
					float timewindow = static_cast<float>(_wtof(buffer6));

					float Fixed_load1_scalar_lower = static_cast<float>(_wtof(buffer7));
					float Fixed_load1_scalar_upper = static_cast<float>(_wtof(buffer8));
					float Fixed_load1_scalar_step = static_cast<float>(_wtof(buffer9));

					float Fixed_load2_scalar_lower = static_cast<float>(_wtof(buffer10));
					float Fixed_load2_scalar_upper = static_cast<float>(_wtof(buffer11));
					float Fixed_load2_scalar_step = static_cast<float>(_wtof(buffer12));

					float Flex_load_max_lower = static_cast<float>(_wtof(buffer13));
					float Flex_load_max_upper = static_cast<float>(_wtof(buffer14));
					float Flex_load_max_step = static_cast<float>(_wtof(buffer15));

					float Mop_load_max_lower = static_cast<float>(_wtof(buffer16));
					float Mop_load_max_upper = static_cast<float>(_wtof(buffer17));
					float Mop_load_max_step = static_cast<float>(_wtof(buffer18));

					float ScalarRG1_lower = static_cast<float>(_wtof(buffer19));
					float ScalarRG1_upper = static_cast<float>(_wtof(buffer20));
					float ScalarRG1_step = static_cast<float>(_wtof(buffer21));

					float ScalarRG2_lower = static_cast<float>(_wtof(buffer22));
					float ScalarRG2_upper = static_cast<float>(_wtof(buffer23));
					float ScalarRG2_step = static_cast<float>(_wtof(buffer24));

					float ScalarRG3_lower = static_cast<float>(_wtof(buffer25));
					float ScalarRG3_upper = static_cast<float>(_wtof(buffer26));
					float ScalarRG3_step = static_cast<float>(_wtof(buffer27));

					float ScalarRG4_lower = static_cast<float>(_wtof(buffer28));
					float ScalarRG4_upper = static_cast<float>(_wtof(buffer29));
					float ScalarRG4_step = static_cast<float>(_wtof(buffer30));

					float ScalarHL1_lower = static_cast<float>(_wtof(buffer31));
					float ScalarHL1_upper = static_cast<float>(_wtof(buffer32));
					float ScalarHL1_step = static_cast<float>(_wtof(buffer33));

					float ScalarHYield1_lower = static_cast<float>(_wtof(buffer34));
					float ScalarHYield1_upper = static_cast<float>(_wtof(buffer35));
					float ScalarHYield1_step = static_cast<float>(_wtof(buffer36));

					float ScalarHYield2_lower = static_cast<float>(_wtof(buffer37));
					float ScalarHYield2_upper = static_cast<float>(_wtof(buffer38));
					float ScalarHYield2_step = static_cast<float>(_wtof(buffer39));

					float ScalarHYield3_lower = static_cast<float>(_wtof(buffer40));
					float ScalarHYield3_upper = static_cast<float>(_wtof(buffer41));
					float ScalarHYield3_step = static_cast<float>(_wtof(buffer42));

					float ScalarHYield4_lower = static_cast<float>(_wtof(buffer43));
					float ScalarHYield4_upper = static_cast<float>(_wtof(buffer44));
					float ScalarHYield4_step = static_cast<float>(_wtof(buffer45));

					float GridImport_lower = static_cast<float>(_wtof(buffer46));
					float GridImport_upper = static_cast<float>(_wtof(buffer47));
					float GridImport_step = static_cast<float>(_wtof(buffer48));

					float GridExport_lower = static_cast<float>(_wtof(buffer49));
					float GridExport_upper = static_cast<float>(_wtof(buffer50));
					float GridExport_step = static_cast<float>(_wtof(buffer51));

					float Import_headroom_lower = static_cast<float>(_wtof(buffer52));
					float Import_headroom_upper = static_cast<float>(_wtof(buffer53));
					float Import_headroom_step = static_cast<float>(_wtof(buffer54));

					float Export_headroom_lower = static_cast<float>(_wtof(buffer55));
					float Export_headroom_upper = static_cast<float>(_wtof(buffer56));
					float Export_headroom_step = static_cast<float>(_wtof(buffer57));

					float ESS_charge_power_lower = static_cast<float>(_wtof(buffer58));
					float ESS_charge_power_upper = static_cast<float>(_wtof(buffer59));
					float ESS_charge_power_step = static_cast<float>(_wtof(buffer60));

					float ESS_discharge_power_lower = static_cast<float>(_wtof(buffer61));
					float ESS_discharge_power_upper = static_cast<float>(_wtof(buffer62));
					float ESS_discharge_power_step = static_cast<float>(_wtof(buffer63));

					float ESS_capacity_lower = static_cast<float>(_wtof(buffer64));
					float ESS_capacity_upper = static_cast<float>(_wtof(buffer65));
					float ESS_capacity_step = static_cast<float>(_wtof(buffer66));

					float ESS_RTE_lower = static_cast<float>(_wtof(buffer67));
					float ESS_RTE_upper = static_cast<float>(_wtof(buffer68));
					float ESS_RTE_step = static_cast<float>(_wtof(buffer69));

					float ESS_aux_load_lower = static_cast<float>(_wtof(buffer70));
					float ESS_aux_load_upper = static_cast<float>(_wtof(buffer71));
					float ESS_aux_load_step = static_cast<float>(_wtof(buffer72)); // JSM changed ESS_aux_step to ESS_aux_load_step

					float ESS_start_SoC_lower = static_cast<float>(_wtof(buffer73));
					float ESS_start_SoC_upper = static_cast<float>(_wtof(buffer74));
					float ESS_start_SoC_step = static_cast<float>(_wtof(buffer75));

					int ESS_charge_mode_lower = static_cast<int>(_wtoi(buffer76));
					int ESS_charge_mode_upper = static_cast<int>(_wtoi(buffer77));

					int ESS_discharge_mode_lower = static_cast<int>(_wtoi(buffer78));
					int ESS_discharge_mode_upper = static_cast<int>(_wtoi(buffer79));

					float import_kWh_price = static_cast<float>(_wtof(buffer80));
					float export_kWh_price = static_cast<float>(_wtof(buffer81));

					float time_budget_min = static_cast<float>(_wtof(buffer82));

					int target_max_concurrency = static_cast<float>(_wtoi(buffer83));

					float CAPEX_limit = static_cast<float>(_wtof(buffer84));
					float OPEX_limit = static_cast<float>(_wtof(buffer85));

					InitConsole();

					InputValues inputvalues = {
		timestep_minutes, timestep_hours, timewindow,
		Fixed_load1_scalar_lower, Fixed_load1_scalar_upper, Fixed_load1_scalar_step,
		Fixed_load2_scalar_lower, Fixed_load2_scalar_upper, Fixed_load2_scalar_step,
		Flex_load_max_lower, Flex_load_max_upper, Flex_load_max_step,
		Mop_load_max_lower, Mop_load_max_upper, Mop_load_max_step,
		ScalarRG1_lower, ScalarRG1_upper, ScalarRG1_step,
		ScalarRG2_lower, ScalarRG2_upper, ScalarRG2_step,
		ScalarRG3_lower, ScalarRG3_upper, ScalarRG3_step,
		ScalarRG4_lower, ScalarRG4_upper, ScalarRG4_step,
		ScalarHL1_lower, ScalarHL1_upper, ScalarHL1_step,
		ScalarHYield1_lower, ScalarHYield1_upper, ScalarHYield1_step,
		ScalarHYield2_lower, ScalarHYield2_upper, ScalarHYield2_step,
		ScalarHYield3_lower, ScalarHYield3_upper, ScalarHYield3_step,
		ScalarHYield4_lower, ScalarHYield4_upper, ScalarHYield4_step,
		GridImport_lower, GridImport_upper, GridImport_step,
		GridExport_lower, GridExport_upper, GridExport_step,
		Import_headroom_lower, Import_headroom_upper, Import_headroom_step,
		Export_headroom_lower, Export_headroom_upper, Export_headroom_step,
		ESS_charge_power_lower, ESS_charge_power_upper, ESS_charge_power_step,
		ESS_discharge_power_lower, ESS_discharge_power_upper, ESS_discharge_power_step,
		ESS_capacity_lower, ESS_capacity_upper, ESS_capacity_step,
		ESS_RTE_lower, ESS_RTE_upper, ESS_RTE_step,
		ESS_aux_load_lower, ESS_aux_load_upper, ESS_aux_load_step,
		ESS_start_SoC_lower, ESS_start_SoC_upper, ESS_start_SoC_step,
		ESS_charge_mode_lower, ESS_charge_mode_upper,
		ESS_discharge_mode_lower, ESS_discharge_mode_upper,
		import_kWh_price, export_kWh_price,
		time_budget_min, target_max_concurrency,
		CAPEX_limit, OPEX_limit
					};

					/* ==== JSM CODE HERE ==================================================================== */
					// Aim: to export 'inputvalues' to a json file that can be read e.g. as a Python dict, s.t. other EPL software can use this as an input
					// These are 2 lines to produce debug output -- not functionally important!
					//std::cout << "Hello. We are here now." << std::endl;
					//std::cout << inputvalues.ESS_aux_load_lower << std::endl;

					// Convert the InputValues struct to a JSON object using the mapping
					nlohmann::json jsonObj = structToJson(inputvalues, memberMappings, std::size(memberMappings));

					// Write the JSON to a file
					std::ofstream file("parameters.json");
					file << jsonObj.dump(4); // The "4" argument adds pretty-printing with indentation
					file.close();

					nlohmann::json converted_json = convert_to_ranges(jsonObj);
					std::ofstream file3("parameters_grouped.json");
					file3 << converted_json.dump(4); // The "4" argument adds pretty-printing with indentation
					file3.close();

					std::cout << "JSON file written successfully!" << std::endl;
					/* ======================================================================================== */

				wchar_t buffer100[100];
				
				GetWindowText(hTextbox200, buffer100, 100);

				int recall_index = _wtof(buffer100);
			
				SetWindowText(hTextbox4, buffer1);

				OutputValues output = RecallIndex(converted_json, recall_index);

				wchar_t buffer[300];
				swprintf_s(buffer, 300, L"%f", output.Fixed_load1_scalar);
				SetWindowText(hTextbox7, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox8, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox9, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.Fixed_load2_scalar);
				SetWindowText(hTextbox10, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox11, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox12, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.Flex_load_max);
				SetWindowText(hTextbox13, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox14, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox15, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.Mop_load_max);
				SetWindowText(hTextbox16, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox17, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox18, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ScalarRG1);
				SetWindowText(hTextbox19, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox20, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox21, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ScalarRG2);
				SetWindowText(hTextbox22, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox23, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox24, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ScalarRG3);
				SetWindowText(hTextbox25, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox26, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox27, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ScalarRG4);
				SetWindowText(hTextbox28, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox29, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox30, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ScalarHL1);
				SetWindowText(hTextbox31, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox32, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox33, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ScalarHYield1);
				SetWindowText(hTextbox34, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox35, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox36, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ScalarHYield2);
				SetWindowText(hTextbox37, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox38, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox39, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ScalarHYield3);
				SetWindowText(hTextbox40, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox41, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox42, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ScalarHYield4);
				SetWindowText(hTextbox43, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox44, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox45, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.GridImport);
				SetWindowText(hTextbox46, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox47, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox48, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.GridExport);
				SetWindowText(hTextbox49, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox50, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox51, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.Import_headroom);
				SetWindowText(hTextbox52, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox53, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox54, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.Export_headroom);
				SetWindowText(hTextbox55, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox56, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox57, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ESS_charge_power);
				SetWindowText(hTextbox58, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox59, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox60, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ESS_discharge_power);
				SetWindowText(hTextbox61, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox62, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox63, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ESS_capacity);
				SetWindowText(hTextbox64, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox65, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox66, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ESS_RTE);
				SetWindowText(hTextbox67, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox68, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox69, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ESS_aux_load);
				SetWindowText(hTextbox70, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox71, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox72, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.ESS_start_SoC);
				SetWindowText(hTextbox73, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox74, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox75, buffer);

				 
				swprintf_s(buffer, 300, L"%d", output.ESS_charge_mode);
				SetWindowText(hTextbox76, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox77, buffer);

				 
				swprintf_s(buffer, 300, L"%d", output.ESS_discharge_mode);
				SetWindowText(hTextbox78, buffer);

				 
				swprintf_s(buffer, 300, L"%s", L"_");
				SetWindowText(hTextbox79, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.import_kWh_price);
				SetWindowText(hTextbox80, buffer);

				 
				swprintf_s(buffer, 300, L"%f", output.export_kWh_price);
				SetWindowText(hTextbox81, buffer);

			}
			CloseConsole();
			break;

		}
		}
	}


	case WM_PAINT:
	{
		PAINTSTRUCT ps;
		HDC hdc = BeginPaint(hWnd, &ps);
		// TODO: Add any drawing code that uses hdc here...
		EndPaint(hWnd, &ps);
	}
	break;

	case WM_DESTROY:
	{
		PostQuitMessage(0);
		break;
	default:
		return DefWindowProc(hWnd, message, wParam, lParam);
	}
	return 0;

	}
}

// Message handler for about box.
INT_PTR CALLBACK About(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    UNREFERENCED_PARAMETER(lParam);
    switch (message)
    {
    case WM_INITDIALOG:
        return (INT_PTR)TRUE;

    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK || LOWORD(wParam) == IDCANCEL)
        {
            EndDialog(hDlg, LOWORD(wParam));
            return (INT_PTR)TRUE;
        }
        break;
    }
    return (INT_PTR)FALSE;
}
