#include "Bindings.hpp"

#include <format>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>

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
		.def("simulate_scenario", &Simulator_py::simulateScenario,
			pybind11::arg("taskData"),
			pybind11::arg("fullReporting") = false);

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
		.def_readwrite("DHW_cylinder_volume", &TaskData::DHW_cylinder_volume)
		.def_readwrite("Export_kWh_price", &TaskData::Export_kWh_price)
		.def_readwrite("time_budget_min", &TaskData::time_budget_min)
		.def_readwrite("target_max_concurrency", &TaskData::target_max_concurrency)
		.def_readwrite("timestep_hours", &TaskData::timestep_hours)
		.def_readwrite("CAPEX_limit", &TaskData::CAPEX_limit)
		.def_readwrite("OPEX_limit", &TaskData::OPEX_limit)
		.def_readwrite("timewindow", &TaskData::timewindow)
		.def("__repr__", &taskDataToString);

	pybind11::class_<SimulationResult>(m, "SimulationResult")
		.def_readonly("carbon_balance_scope_1", &SimulationResult::scenario_carbon_balance_scope_1)
		.def_readonly("carbon_balance_scope_2", &SimulationResult::scenario_carbon_balance_scope_2)
		.def_readonly("cost_balance", &SimulationResult::scenario_cost_balance)
		.def_readonly("capex", &SimulationResult::project_CAPEX)
		.def_readonly("payback_horizon", &SimulationResult::payback_horizon_years)
		.def_readonly("annualised_cost", &SimulationResult::total_annualised_cost)
		.def_readonly("report_data", &SimulationResult::report_data)
		.def("__repr__", &resultToString);

	pybind11::class_<ReportData>(m, "ReportData")
		.def_readonly("Actual_import_shortfall", &ReportData::Actual_import_shortfall)
		.def_readonly("Actual_curtailed_export", &ReportData::Actual_curtailed_export)
		.def_readonly("Heat_shortfall", &ReportData::Heat_shortfall)
		.def_readonly("Heat_surplus", &ReportData::Heat_surplus)
		.def_readonly("Hotel_load", &ReportData::Hotel_load)
		.def_readonly("Heatload", &ReportData::Heatload)
		.def_readonly("PVdcGen", &ReportData::PVdcGen)
		.def_readonly("PVacGen", &ReportData::PVacGen)
		.def_readonly("EV_targetload", &ReportData::EV_targetload)
		.def_readonly("EV_actualload", &ReportData::EV_actualload)
		.def_readonly("ESS_charge", &ReportData::ESS_charge)
		.def_readonly("ESS_discharge", &ReportData::ESS_discharge)
		.def_readonly("ESS_resulting_SoC", &ReportData::ESS_resulting_SoC)
		.def_readonly("ESS_AuxLoad", &ReportData::ESS_AuxLoad)
		.def_readonly("ESS_RTL", &ReportData::ESS_RTL)
		.def_readonly("Data_centre_target_load", &ReportData::Data_centre_target_load)
		.def_readonly("Data_centre_actual_load", &ReportData::Data_centre_actual_load)
		.def_readonly("Data_centre_target_heat", &ReportData::Data_centre_target_heat)
		.def_readonly("Data_centre_available_hot_heat", &ReportData::Data_centre_available_hot_heat)
		.def_readonly("Grid_Import", &ReportData::Grid_Import)
		.def_readonly("Grid_Export", &ReportData::Grid_Export)
		.def_readonly("MOP_load", &ReportData::MOP_load)
		.def_readonly("GasCH_load", &ReportData::GasCH_load)
		.def_readonly("DHW_load", &ReportData::DHW_load)
		.def_readonly("DHW_charging", &ReportData::DHW_charging)
		.def_readonly("DHW_SoC", &ReportData::DHW_SoC)
		.def_readonly("DHW_Standby_loss", &ReportData::DHW_Standby_loss)
		.def_readonly("DHW_ave_temperature", &ReportData::DHW_ave_temperature)
		.def_readonly("DHW_Shortfall", &ReportData::DHW_Shortfall);
}


std::string resultToString(const SimulationResult& result)
{
	return std::format(
		"SimulationResult("
		"carbon_balance_scope_1: {},"
		"carbon_balance_scope_2: {},"
		"cost_balance: {},"
		"capex: {},"
		"payback_horizon: {},"
		"annualised_cost: {}"
		")",
		result.scenario_carbon_balance_scope_1, 
		result.scenario_carbon_balance_scope_2,
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
