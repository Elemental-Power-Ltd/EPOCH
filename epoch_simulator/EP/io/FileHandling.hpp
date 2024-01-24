#pragma once

#include "../dependencies/json.hpp"
#include "../Definitions.h"

#include <filesystem>
#include <string>
#include <vector>


std::vector<float> readCSVColumn(const std::filesystem::path& filename, int column);
bool isValidFloat(const std::string& str);
void writeToCSV(std::filesystem::path filepath, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumns);
void writeResultsToCSV(std::filesystem::path filepath, const std::vector<SimulationResult>& results);
void appendCSV(std::filesystem::path filepath, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumns);

nlohmann::json inputToJson(const InputValues& data);
nlohmann::json outputToJson(const OutputValues& data);
nlohmann::json convert_to_ranges(nlohmann::json& j);

nlohmann::json handleJsonConversion(const InputValues& inputValues, std::filesystem::path inputDir);
void writeJsonToFile(const nlohmann::json& jsonObj, std::filesystem::path filepath);

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
