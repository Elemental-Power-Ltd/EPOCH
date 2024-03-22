#pragma once

#include "../Definitions.h"
#include "FileConfig.h"

#include <nlohmann/json.hpp>

#include <filesystem>
#include <string>
#include <vector>


std::vector<float> readCSVColumn(const std::filesystem::path& filename, int column);
bool isValidFloat(const std::string& str);
void writeResultsToCSV(std::filesystem::path filepath, const std::vector<SimulationResult>& results);
void writeResultsToCSV(std::filesystem::path filepath, const std::vector<ObjectiveResult>& results);

nlohmann::json inputToJson(const InputValues& data);
nlohmann::json outputToJson(const OutputValues& data);
nlohmann::json convert_to_ranges(nlohmann::json& j);

nlohmann::json handleJsonConversion(const InputValues& inputValues, std::filesystem::path inputParametersFilepath);
void writeJsonToFile(const nlohmann::json& jsonObj, std::filesystem::path filepath);
nlohmann::json readJsonFromFile(std::filesystem::path filepath);

const HistoricalData readHistoricalData(const FileConfig& fileConfig);
Eigen::VectorXf toEigen(const std::vector<float>& vec);


constexpr std::array<std::string_view, 31> resultHeader = {
	"Parameter index",
	"Calculative execution time (s)",

	"Annualised cost",
	"Project CAPEX",
	"Scenario Balance (£)",
	"Payback horizon (yrs)",
	"Scenario Carbon Balance (kgC02e)",

	"Scaled RGen_total",
	"Total_scaled_target_load",
	"Total load minus Rgen (ESUM)",
	"ESS_available_discharge_power",
	"ESS_available_charge_power",
	"ESS_Rgen_only_charge",
	"ESS_discharge",
	"ESS_charge",
	"ESS_resulting_SoC",
	"Pre_grid_balance",
	"Grid Import",
	"Grid Export",
	"Post_grid_balance",
	"Pre_flex_import_shortfall",
	"Pre_mop_curtailed Export",
	"Actual import shortfall",
	"Actual curtailed export",
	"Actual high priority load",
	"Actual low priority load",
	"Heat load",
	"Scaled Heat load",
	"Electrical load scaled heat",
	"Heat shortfall",
	"Heat surplus",
};

// The subset of values in the Config class that we want to write to the output CSVs
constexpr std::array<std::string_view, 30> configParamNames = {
	"Fixed_load1_scalar",
	"Fixed_load2_scalar",
	"Flex_load_max",
	"Mop_load_max",
	"ScalarRG1",
	"ScalarRG2",
	"ScalarRG3",
	"ScalarRG4",
	"ScalarHL1",
	"ScalarHYield1",
	"ScalarHYield2",
	"ScalarHYield3",
	"ScalarHYield4",
	"GridImport",
	"GridExport",
	"Import_headroom",
	"Export_headroom",
	"ESS_charge_power",
	"ESS_discharge_power",
	"ESS_capacity",
	"ESS_RTE",
	"ESS_aux_load",
	"ESS_start_SoC",
	"import_kWh_price",
	"export_kWh_price",
	"time_budget_min",
	"CAPEX_limit",
	"OPEX_limit",
	"ESS_charge_mode",
	"ESS_discharge_mode"
};