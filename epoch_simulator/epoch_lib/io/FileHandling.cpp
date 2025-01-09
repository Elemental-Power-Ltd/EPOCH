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
#include "EnumToString.hpp"

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
	OUT_MEMBER_MAPPING_FLOAT(ScalarHL1), OUT_MEMBER_MAPPING_FLOAT(ASHP_HPower), OUT_MEMBER_MAPPING_INT(ASHP_HSource), OUT_MEMBER_MAPPING_FLOAT(ASHP_RadTemp), OUT_MEMBER_MAPPING_FLOAT(ASHP_HotTemp),
	OUT_MEMBER_MAPPING_FLOAT(ESS_charge_power), OUT_MEMBER_MAPPING_FLOAT(ESS_discharge_power), OUT_MEMBER_MAPPING_FLOAT(ESS_capacity), OUT_MEMBER_MAPPING_FLOAT(ESS_start_SoC),
	OUT_MEMBER_MAPPING_INT(ESS_charge_mode), OUT_MEMBER_MAPPING_INT(ESS_discharge_mode), OUT_MEMBER_MAPPING_FLOAT(DHW_cylinder_volume),
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
		size_t column_1 = column - 1;

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
			rowData.push_back(std::stof(cell));
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
				rowData.push_back(std::stof(cell));
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
	outFile << "annualised_cost" << ",";
	outFile << "capex" << ",";
	outFile << "cost_balance" << ",";
	outFile << "payback_horizon" << ",";
	outFile << "carbon_balance_scope_1" << ",";
	outFile << "carbon_balance_scope_2" << ",";

	// building
	outFile << "building_scalar_heat_load" << ",";
	outFile << "building_scalar_electrical_load" << ",";
	outFile << "fabric_intervention_index" << ",";
	
	// data centre
	outFile << "data_centre_maximum_load" << ",";
	outFile << "hotroom_temp" << ",";
	
	// dhw
	outFile << "dhw_cylinder_volume" << ",";
	
	// ev
	outFile << "ev_flexible_load_ratio" << ",";
	outFile << "small_chargers" << ",";
	outFile << "fast_chargers" << ",";
	outFile << "rapid_chargers" << ",";
	outFile << "ultra_chargers" << ",";
	outFile << "ev_scalar_electrical_load" << ",";

	// ess
	outFile << "ess_capacity" << ",";
	outFile << "ess_charge_power" << ",";
	outFile << "ess_discharge_power" << ",";
	outFile << "battery_mode" << ",";
	outFile << "ess_initial_charge" << ",";

	// grid
	outFile << "export_headroom" << ",";
	outFile << "grid_export" << ",";
	outFile << "grid_import" << ",";
	outFile << "import_headroon" << ",";
	outFile << "min_power_factor" << ",";
	outFile << "tariff_index" << ",";

	// heatpump
	outFile << "heat_power" << ",";
	outFile << "heat_source" << ",";
	outFile << "send_temp" << ",";

	// mop
	outFile << "mop_maximum_load" << ",";

	// FIXME
	// skip renewables for now because their arbitrary size makes it hard to know how many columns we want
	
	// Config
	outFile << "capex_limit";  // no trailing comma

	outFile << "\n";
}

void writeObjectiveResultRow(std::ofstream& outFile, const ObjectiveResult& result) {
	// These must be written in exactly the same order as the header
	outFile << result.total_annualised_cost << ",";
	outFile << result.project_CAPEX << ",";
	outFile << result.scenario_cost_balance << ",";
	outFile << result.payback_horizon_years << ",";
	outFile << result.scenario_carbon_balance_scope_1 << ",";
	outFile << result.scenario_carbon_balance_scope_2 << ",";

	const TaskData& taskData = result.taskData;

	// We chose to write empty columns when the components are not present

	if (taskData.building) {
		outFile << taskData.building->scalar_heat_load << ",";
		outFile << taskData.building->scalar_heat_load << ",";
		outFile << taskData.building->scalar_heat_load << ",";
	}
	else {
		outFile << ",,,";
	}

	if (taskData.data_centre) {
		outFile << taskData.data_centre->maximum_load << ",";
		outFile << taskData.data_centre->hotroom_temp << ",";
	}
	else {
		outFile << ",,";
	}

	if (taskData.domestic_hot_water) {
		outFile << taskData.domestic_hot_water->cylinder_volume << ",";
	}
	else {
		outFile << ",";
	}

	if (taskData.electric_vehicles) {
		outFile << taskData.electric_vehicles->flexible_load_ratio << ",";
		outFile << taskData.electric_vehicles->small_chargers << ",";
		outFile << taskData.electric_vehicles->fast_chargers << ",";
		outFile << taskData.electric_vehicles->rapid_chargers << ",";
		outFile << taskData.electric_vehicles->ultra_chargers << ",";
		outFile << taskData.electric_vehicles->scalar_electrical_load << ",";
	}
	else {
		outFile << ",,,,,,";
	}

	if (taskData.energy_storage_system) {
		outFile << taskData.energy_storage_system->capacity << ",";
		outFile << taskData.energy_storage_system->charge_power << ",";
		outFile << taskData.energy_storage_system->discharge_power << ",";
		outFile << enumToString(taskData.energy_storage_system->battery_mode) << ",";
		outFile << taskData.energy_storage_system->initial_charge << ",";
	}
	else {
		outFile << ",,,,,";
	}

	if (taskData.grid) {
		outFile << taskData.grid->export_headroom << ",";
		outFile << taskData.grid->grid_export << ",";
		outFile << taskData.grid->grid_import << ",";
		outFile << taskData.grid->import_headroom << ",";
		outFile << taskData.grid->min_power_factor << ",";
		outFile << taskData.grid->tariff_index << ",";
	}
	else {
		outFile << ",,,,,,";
	}

	if (taskData.heat_pump) {
		outFile << taskData.heat_pump->heat_power << ",";
		outFile << enumToString(taskData.heat_pump->heat_source) << ",";
		outFile << taskData.heat_pump->send_temp << ",";
	}
	else {
		outFile << ",,,";
	}

	if (taskData.mop) {
		outFile << taskData.mop->maximum_load << ",";
	}
	else {
		outFile << ",";
	}

	// FIXME
	// renewables skipped as dynamic sized

	outFile << taskData.config.capex_limit; // no trailing comma
	
	outFile << "\n";
}

// Utility method for writing cells in a CSV
// Return the string value if safe, otherwise the empty string
std::string valueOrEmpty(const year_TS& vec, Eigen::Index i) {
	if (vec.size() > i) {
		return std::to_string(vec[i]);
	}
	return "";
}

void writeTimeSeriesToCSV(std::filesystem::path filepath, const ReportData& reportData)
{
	std::ofstream outFile(filepath);

	if (!outFile.is_open()) {
		spdlog::error("Failed to open the output file!");
		throw FileReadException(filepath.filename().string());
	}

	// Write the column headers
	outFile << "Actual_import_shortfall" << ",";
	outFile << "Actual_curtailed_export" << ",";
	outFile << "Heat_shortfall" << ",";
	outFile << "Heat_surplus" << ",";
	outFile << "Hotel_load" << ",";
	outFile << "Heatload" << ",";
	outFile << "PVdcGen" << ",";
	outFile << "PVacGen" << ",";
	outFile << "EV_targetload" << ",";
	outFile << "EV_actualload" << ",";
	outFile << "ESS_charge" << ",";
	outFile << "ESS_discharge" << ",";
	outFile << "ESS_resulting_SoC" << ",";
	outFile << "ESS_AuxLoad" << ",";
	outFile << "ESS_RTL" << ",";
	outFile << "Data_centre_target_load" << ",";
	outFile << "Data_centre_actual_load" << ",";
	outFile << "Data_centre_target_heat" << ",";
	outFile << "Data_centre_available_hot_heat" << ",";
	outFile << "Grid_Import" << ",";
	outFile << "Grid_Export" << ",";
	outFile << "MOP_load" << ",";
	outFile << "GasCH_load" << ",";
	outFile << "DHW_load" << ",";
	outFile << "DHW_charging" << ",";
	outFile << "DHW_SoC" << ",";
	outFile << "DHW_Standby_loss" << ",";
	outFile << "DHW_ave_temperature" << ",";
	outFile << "DHW_Shortfall";  // no trailing comma
	outFile << "\n"; // newline

	// Actual import shortfall is derived from TempSum so should always be present
	Eigen::Index timesteps = reportData.Actual_import_shortfall.size();

	// Write the values, handling empty vectors
	for (Eigen::Index i = 0; i < timesteps; ++i) {
		outFile << valueOrEmpty(reportData.Actual_import_shortfall, i) << ","
			<< valueOrEmpty(reportData.Actual_curtailed_export, i) << ","
			<< valueOrEmpty(reportData.Heat_shortfall, i) << ","
			<< valueOrEmpty(reportData.Heat_surplus, i) << ","
			<< valueOrEmpty(reportData.Hotel_load, i) << ","
			<< valueOrEmpty(reportData.Heatload, i) << ","
			<< valueOrEmpty(reportData.PVdcGen, i) << ","
			<< valueOrEmpty(reportData.PVacGen, i) << ","
			<< valueOrEmpty(reportData.EV_targetload, i) << ","
			<< valueOrEmpty(reportData.EV_actualload, i) << ","
			<< valueOrEmpty(reportData.ESS_charge, i) << ","
			<< valueOrEmpty(reportData.ESS_discharge, i) << ","
			<< valueOrEmpty(reportData.ESS_resulting_SoC, i) << ","
			<< valueOrEmpty(reportData.ESS_AuxLoad, i) << ","
			<< valueOrEmpty(reportData.ESS_RTL, i) << ","
			<< valueOrEmpty(reportData.Data_centre_target_load, i) << ","
			<< valueOrEmpty(reportData.Data_centre_actual_load, i) << ","
			<< valueOrEmpty(reportData.Data_centre_target_heat, i) << ","
			<< valueOrEmpty(reportData.Data_centre_available_hot_heat, i) << ","
			<< valueOrEmpty(reportData.Grid_Import, i) << ","
			<< valueOrEmpty(reportData.Grid_Export, i) << ","
			<< valueOrEmpty(reportData.MOP_load, i) << ","
			<< valueOrEmpty(reportData.GasCH_load, i) << ","
			<< valueOrEmpty(reportData.DHW_load, i) << ","
			<< valueOrEmpty(reportData.DHW_charging, i) << ","
			<< valueOrEmpty(reportData.DHW_SoC, i) << ","
			<< valueOrEmpty(reportData.DHW_Standby_loss, i) << ","
			<< valueOrEmpty(reportData.DHW_ave_temperature, i) << ","
			<< valueOrEmpty(reportData.DHW_Shortfall, i) << "\n";
	}
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

void writeJsonToFile(const nlohmann::json& jsonObj, std::filesystem::path filepath) {
	try {
		std::ofstream file(filepath);
		file << jsonObj.dump(4);  // The "4" argument adds pretty-printing with indentation
		file.close();
	}
	catch (const std::exception& e) {
		spdlog::warn("Error: {}", e.what());
	}
}

nlohmann::json readJsonFromFile(std::filesystem::path filepath)
{
	try {
		std::ifstream f(filepath);
		return nlohmann::json::parse(f);
	}
	catch (const std::exception&) {
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

	// determine and the number of timesteps and check that all of the timeseries are equal in length
	size_t timesteps = hotel_eload_data.size();
	if (
		ev_eload_data.size() != timesteps ||
		heatload_data.size() != timesteps ||
		RGen_data_1.size() != timesteps ||
		RGen_data_2.size() != timesteps ||
		RGen_data_3.size() != timesteps ||
		RGen_data_4.size() != timesteps ||
		airtemp_data.size() != timesteps ||
		importtariff_data.size() != timesteps ||
		gridCO2_data.size() != timesteps ||
		DHWload_data.size() != timesteps
		) {
		throw EpochBaseException("Time series differ in length");
	}

	// FIXME for now the time interval is always 0.5 hours (half an hour)
	constexpr float TIMESTEP_HOURS = 0.5f;


	//read in the ASHP data
	std::filesystem::path ASHPinputFilepath = fileConfig.getASHPinputFilepath();
	std::vector<std::vector<float>> ASHPinputtable = readCSVAsTable(ASHPinputFilepath);

	std::filesystem::path ASHPoutputFilepath = fileConfig.getASHPoutputFilepath();
	std::vector<std::vector<float>> ASHPoutputtable = readCSVAsTable(ASHPoutputFilepath);

	
	return {
		TIMESTEP_HOURS,
		timesteps,
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

	for (size_t i = 0; i < vec.size(); i++) {
		eig[i] = vec[i];
	}

	return eig;
}

Eigen::MatrixXf toEigen(const std::vector<std::vector<float>>& mat) {
	Eigen::MatrixXf eig = Eigen::MatrixXf(mat.size(), mat[0].size());

	for (size_t i = 0; i < mat.size(); i++) {
		for (size_t j = 0; j < mat[0].size(); j++) {
			eig(i,j) = mat[i][j];
		}
	}

	return eig;
}


