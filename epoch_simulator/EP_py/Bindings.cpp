#include "Bindings.hpp"

#include <format>

#include "Simulate_py.hpp"
#include "../epoch_lib/Simulation/Config.h"


PYBIND11_MODULE(EPSimulator, m) {
	pybind11::class_<Simulator_py>(m, "Simulator")
		.def(pybind11::init<>())
		.def("simulate_scenario", &Simulator_py::simulateScenario);

	pybind11::class_<Config>(m, "Config")
		.def(pybind11::init<>())
		.def_readwrite("Fixed_load1_scalar", &Config::Fixed_load1_scalar)
		.def_readwrite("Fixed_load2_scalar", &Config::Fixed_load2_scalar)
		.def_readwrite("Flex_load_max", &Config::Flex_load_max)
		.def_readwrite("Mop_load_max", &Config::Mop_load_max)
		.def_readwrite("ScalarRG1", &Config::ScalarRG1)
		.def_readwrite("ScalarRG2", &Config::ScalarRG2)
		.def_readwrite("ScalarRG3", &Config::ScalarRG3)
		.def_readwrite("ScalarRG4", &Config::ScalarRG4)
		.def_readwrite("ScalarHL1", &Config::ScalarHL1)
		.def_readwrite("ScalarHYield1", &Config::ScalarHYield1)
		.def_readwrite("ScalarHYield2", &Config::ScalarHYield2)
		.def_readwrite("ScalarHYield3", &Config::ScalarHYield3)
		.def_readwrite("ScalarHYield4", &Config::ScalarHYield4)
		.def_readwrite("GridImport", &Config::GridImport)
		.def_readwrite("GridExport", &Config::GridExport)
		.def_readwrite("Import_headroom", &Config::Import_headroom)
		.def_readwrite("Export_headroom", &Config::Export_headroom)
		.def_readwrite("ESS_charge_power", &Config::ESS_charge_power)
		.def_readwrite("ESS_discharge_power", &Config::ESS_discharge_power)
		.def_readwrite("ESS_capacity", &Config::ESS_capacity)
		.def_readwrite("ESS_RTE", &Config::ESS_RTE)
		.def_readwrite("ESS_aux_load", &Config::ESS_aux_load)
		.def_readwrite("ESS_start_SoC", &Config::ESS_start_SoC)
		.def_readwrite("ESS_charge_mode", &Config::ESS_charge_mode)
		.def_readwrite("ESS_discharge_mode", &Config::ESS_discharge_mode)
		.def_readwrite("Import_kWh_price", &Config::Import_kWh_price)
		.def_readwrite("Export_kWh_price", &Config::Export_kWh_price)
		.def_readwrite("time_budget_min", &Config::time_budget_min)
		.def_readwrite("target_max_concurrency", &Config::target_max_concurrency)
		.def_readwrite("CAPEX_limit", &Config::CAPEX_limit)
		.def_readwrite("OPEX_limit", &Config::OPEX_limit)
		.def("__repr__", &configToString);


	pybind11::class_<SimulationResult>(m, "SimulationResult")
		.def_readwrite("carbon_balance", &SimulationResult::scenario_carbon_balance)
		.def_readwrite("cost_balance", &SimulationResult::scenario_cost_balance)
		.def_readwrite("capex", &SimulationResult::project_CAPEX)
		.def_readwrite("payback_horizon", &SimulationResult::payback_horizon_years)
		.def_readwrite("annualised_cost", &SimulationResult::total_annualised_cost)
		.def("__repr__", &resultToString);
}




std::string resultToString(const SimulationResult& result)
{
	return std::format(
		"SimulationResult(carbon_balance: {}, "
		"cost_balance: {}, capex: {}, payback_horizon: {}, annualised_cost: {})",
		result.scenario_carbon_balance, 
		result.scenario_cost_balance, 
		result.project_CAPEX, 
		result.payback_horizon_years, 
		result.total_annualised_cost
	);
}
std::string configToString(const Config& config)
{
	const int maxLineLength = 100;
	std::string configAsString = "Config(";

	std::string currentLine = "";

	for (const auto& [key, value] : config.param_map_float) {
		std::string currentField = std::format("{}: {}, ", key, *value);
		if (currentLine.length() + currentField.length() > maxLineLength) {
			// 'flush' the currentLine first as it would be over the max length
			configAsString += currentLine + "\n";
			currentLine = currentField;
		}
		else {
			currentLine += currentField;
		}
	}

	for (const auto& [key, value] : config.param_map_int) {
		std::string currentField = std::format("{}: {}, ", key, *value);
		if (currentLine.length() + currentField.length() > maxLineLength) {
			// 'flush' the currentLine first as it would be over the max length
			configAsString += currentLine + "\n";
			currentLine = currentField;
		}
		else {
			currentLine += currentField;
		}
	}

	// add the final line
	configAsString += currentLine;

	// remove the final comma and space, then close parentheses
	configAsString.resize(configAsString.length() - 2);
	configAsString += ")";
	return configAsString;

}
