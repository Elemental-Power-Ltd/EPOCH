#pragma once

#include "../Definitions.hpp"
#include "FileConfig.hpp"

#include <nlohmann/json.hpp>

#include <filesystem>
#include <string>
#include <vector>


std::vector<float> readCSVColumn(const std::filesystem::path& filename, int column, bool skipHeader);
std::vector<float> readCSVColumnAndSkipHeader(const std::filesystem::path& filename, int column);
std::vector<float> readCSVColumnWithoutSkip(const std::filesystem::path& filename, int column);
std::vector<std::vector<float>> readCSVAsTable(const std::filesystem::path& filename);


void writeResultsToCSV(std::filesystem::path filepath, const std::vector<ObjectiveResult>& results);
void appendResultToCSV(std::filesystem::path filepath, const ObjectiveResult& result);

void writeObjectiveResultHeader(std::ofstream& outFile);
void writeObjectiveResultRow(std::ofstream& outFile, const ObjectiveResult& result);

void writeTimeSeriesToCSV(std::filesystem::path filepath, const ReportData& reportData);
void writeCostDataToCSV(std::filesystem::path filepath, const ReportData& reportData);

nlohmann::json inputToJson(const InputValues& data);
nlohmann::json outputToJson(const OutputValues& data);
nlohmann::json convert_to_ranges(nlohmann::json& j);

nlohmann::json handleJsonConversion(const InputValues& inputValues, std::filesystem::path inputParametersFilepath);
void writeJsonToFile(const nlohmann::json& jsonObj, std::filesystem::path filepath);
nlohmann::json readJsonFromFile(std::filesystem::path filepath);

const HistoricalData readHistoricalData(const FileConfig& fileConfig);
Eigen::VectorXf toEigen(const std::vector<float>& vec);
Eigen::MatrixXf toEigen(const std::vector<std::vector<float>>& mat);


// The subset of values in the TaskData class that we want to write to the output CSVs
constexpr std::array<std::string_view, 35> taskDataParamNames = {
	"Fixed_load1_scalar",
	"Fixed_load2_scalar",
	"Flex_load_max",
	"Mop_load_max",
	"ScalarRG1",
	"ScalarRG2",
	"ScalarRG3",
	"ScalarRG4",
	"ScalarHYield",
	"s7_EV_CP_number",
	"f22_EV_CP_number",
	"r50_EV_CP_number",
	"u150_EV_CP_number",
	"EV_flex",
	"ScalarHL1",
	"ASHP_HPower",
	"ASHP_HSource",
	"ASHP_RadTemp",
	"ASHP_HotTemp",
	"GridImport",
	"GridExport",
	"Import_headroom",
	"Export_headroom",
	"Min_power_factor",
	"ESS_charge_power",
	"ESS_discharge_power",
	"ESS_capacity",
	"ESS_start_SoC",
	"DHW_cylinder_volume",
	"Export_kWh_price",
	"time_budget_min",
	"CAPEX_limit",
	"OPEX_limit",
	"ESS_charge_mode",
	"ESS_discharge_mode"
};