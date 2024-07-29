#include "Bindings.hpp"

#include <format>

#include <pybind11/pybind11.h>

#include "Simulate_py.hpp"
#include "../epoch_lib/Simulation/TaskData.hpp"
#include "../epoch_lib/Definitions.hpp"


PYBIND11_MODULE(epoch_simulator, m) {
	m.attr("__version__") = EPOCH_VERSION;

	pybind11::class_<Simulator_py>(m, "Simulator")
		.def(
			pybind11::init<const std::string&, const std::string&, const std::string&>(),
				pybind11::arg("inputDir") = std::string("./InputData"),
				pybind11::arg("outputDir") = std::string("./OutputData"),
			 	pybind11::arg("configDir") = std::string("./ConfigData"))
		.def("simulate_scenario", &Simulator_py::simulateScenario);

	pybind11::class_<TaskData>(m, "TaskData")
		.def(pybind11::init<>())
		.def_readwrite("Fixed_load1_scalar", &TaskData::Fixed_load1_scalar)
		.def_readwrite("Fixed_load2_scalar", &TaskData::Fixed_load2_scalar)
		.def_readwrite("Flex_load_max", &TaskData::Flex_load_max)
		.def_readwrite("Mop_load_max", &TaskData::Mop_load_max)
		.def_readwrite("ScalarRG1", &TaskData::ScalarRG1)
		.def_readwrite("ScalarRG2", &TaskData::ScalarRG2)
		.def_readwrite("ScalarRG3", &TaskData::ScalarRG3)
		.def_readwrite("ScalarRG4", &TaskData::ScalarRG4)
		.def_readwrite("ScalarHYield", &TaskData::ScalarHYield)
		.def_readwrite("s7_EV_CP_number", &TaskData::s7_EV_CP_number)
		.def_readwrite("f22_EV_CP_number", &TaskData::f22_EV_CP_number)
		.def_readwrite("r50_EV_CP_number", &TaskData::r50_EV_CP_number)
		.def_readwrite("u150_EV_CP_number", &TaskData::u150_EV_CP_number)
		.def_readwrite("EV_flex", &TaskData::EV_flex)
		.def_readwrite("ASHP_HPower", &TaskData::ASHP_HPower)
		.def_readwrite("ASHP_HSource", &TaskData::ASHP_HSource)
		.def_readwrite("ASHP_RadTemp", &TaskData::ASHP_RadTemp)
		.def_readwrite("ASHP_HotTemp", &TaskData::ASHP_HotTemp)
		.def_readwrite("ScalarHL1", &TaskData::ScalarHL1)
		.def_readwrite("GridImport", &TaskData::GridImport)
		.def_readwrite("GridExport", &TaskData::GridExport)
		.def_readwrite("Import_headroom", &TaskData::Import_headroom)
		.def_readwrite("Export_headroom", &TaskData::Export_headroom)
		.def_readwrite("Min_power_factor", &TaskData::Min_power_factor)
		.def_readwrite("ESS_charge_power", &TaskData::ESS_charge_power)
		.def_readwrite("ESS_discharge_power", &TaskData::ESS_discharge_power)
		.def_readwrite("ESS_capacity", &TaskData::ESS_capacity)
		.def_readwrite("ESS_start_SoC", &TaskData::ESS_start_SoC)
		.def_readwrite("ESS_charge_mode", &TaskData::ESS_charge_mode)
		.def_readwrite("ESS_discharge_mode", &TaskData::ESS_discharge_mode)
		.def_readwrite("Export_kWh_price", &TaskData::Export_kWh_price)
		.def_readwrite("time_budget_min", &TaskData::time_budget_min)
		.def_readwrite("target_max_concurrency", &TaskData::target_max_concurrency)
		.def_readwrite("timestep_hours", &TaskData::timestep_hours)
		.def_readwrite("CAPEX_limit", &TaskData::CAPEX_limit)
		.def_readwrite("OPEX_limit", &TaskData::OPEX_limit)
		.def_readwrite("timewindow", &TaskData::timewindow)
		.def("__repr__", &taskDataToString);


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
std::string taskDataToString(const TaskData& taskData)
{
	const int maxLineLength = 100;
	std::string taskDataAsString = "TaskData(";

	std::string currentLine = "";

	for (const auto& [key, value] : taskData.param_map_float) {
		std::string currentField = std::format("{}: {}, ", key, *value);
		if (currentLine.length() + currentField.length() > maxLineLength) {
			// 'flush' the currentLine first as it would be over the max length
			taskDataAsString += currentLine + "\n";
			currentLine = currentField;
		}
		else {
			currentLine += currentField;
		}
	}

	for (const auto& [key, value] : taskData.param_map_int) {
		std::string currentField = std::format("{}: {}, ", key, *value);
		if (currentLine.length() + currentField.length() > maxLineLength) {
			// 'flush' the currentLine first as it would be over the max length
			taskDataAsString += currentLine + "\n";
			currentLine = currentField;
		}
		else {
			currentLine += currentField;
		}
	}

	// add the final line
	taskDataAsString += currentLine;

	// remove the final comma and space, then close parentheses
	taskDataAsString.resize(taskDataAsString.length() - 2);
	taskDataAsString += ")";
	return taskDataAsString;

}
