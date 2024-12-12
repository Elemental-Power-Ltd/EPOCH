#include "Bindings.hpp"

#include <format>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>
#include <sstream>

#include "Simulate_py.hpp"
#include "../epoch_lib/Simulation/TaskData.hpp"
#include "../epoch_lib/Definitions.hpp"
#include "../epoch_lib/io/EnumToString.hpp"
#include "../epoch_lib/Simulation/Costs/CostData.hpp"
#include "../epoch_lib/Simulation/Costs/Capex.hpp"


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
		.def_readwrite("building", &TaskData::building)
		.def_readwrite("data_centre", &TaskData::data_centre)
		.def_readwrite("domestic_hot_water", &TaskData::domestic_hot_water)
		.def_readwrite("electric_vehicles", &TaskData::electric_vehicles)
		.def_readwrite("energy_storage_system", &TaskData::energy_storage_system)
		.def_readwrite("grid", &TaskData::grid)
		.def_readwrite("heat_pump", &TaskData::heat_pump)
		.def_readwrite("mop", &TaskData::mop)
		.def_readwrite("renewables", &TaskData::renewables)
		.def_readwrite("config", &TaskData::config)
		.def("__repr__", &taskDataToString);

	pybind11::class_<Building>(m, "Building")
		.def(pybind11::init<>())
		.def_readwrite("scalar_heat_load", &Building::scalar_heat_load)
		.def_readwrite("scalar_electrical_load", &Building::scalar_electrical_load)
		.def_readwrite("fabric_intervention_index", &Building::fabric_intervention_index);

	pybind11::class_<DataCentreData>(m, "DataCentre")
		.def(pybind11::init<>())
		.def_readwrite("maximum_load", &DataCentreData::maximum_load)
		.def_readwrite("hotroom_temp", &DataCentreData::hotroom_temp);

	pybind11::class_<DomesticHotWater>(m, "DomesticHotWater")
		.def(pybind11::init<>())
		.def_readwrite("cylinder_volume", &DomesticHotWater::cylinder_volume);

	pybind11::class_<ElectricVehicles>(m, "ElectricVehicles")
		.def(pybind11::init<>())
		.def_readwrite("flexible_load_ratio", &ElectricVehicles::flexible_load_ratio)
		.def_readwrite("small_chargers", &ElectricVehicles::small_chargers)
		.def_readwrite("fast_chargers", &ElectricVehicles::fast_chargers)
		.def_readwrite("rapid_chargers", &ElectricVehicles::rapid_chargers)
		.def_readwrite("ultra_chargers", &ElectricVehicles::ultra_chargers)
		.def_readwrite("scalar_electrical_load", &ElectricVehicles::scalar_electrical_load);

	pybind11::class_<EnergyStorageSystem>(m, "EnergyStorageSystem")
		.def(pybind11::init<>())
		.def_readwrite("capacity", &EnergyStorageSystem::capacity)
		.def_readwrite("charge_power", &EnergyStorageSystem::charge_power)
		.def_readwrite("discharge_power", &EnergyStorageSystem::discharge_power)
		.def_readwrite("battery_mode", &EnergyStorageSystem::battery_mode)
		.def_readwrite("initial_charge", &EnergyStorageSystem::initial_charge);

	pybind11::enum_<BatteryMode>(m, "BatteryMode")
		.value("CONSUME", BatteryMode::CONSUME);

	pybind11::class_<GridData>(m, "Grid")
		.def(pybind11::init<>())
		.def_readwrite("export_headroom", &GridData::export_headroom)
		.def_readwrite("grid_export", &GridData::grid_export)
		.def_readwrite("grid_import", &GridData::grid_import)
		.def_readwrite("import_headroom", &GridData::import_headroom)
		.def_readwrite("min_power_factor", &GridData::min_power_factor)
		.def_readwrite("tariff_index", &GridData::tariff_index);

	pybind11::class_<HeatPumpData>(m, "HeatPump")
		.def(pybind11::init<>())
		.def_readwrite("heat_power", &HeatPumpData::heat_power)
		.def_readwrite("heat_source", &HeatPumpData::heat_source)
		.def_readwrite("send_temp", &HeatPumpData::send_temp);

	pybind11::enum_<HeatSource>(m, "HeatSource")
		.value("AMBIENT_AIR", HeatSource::AMBIENT_AIR)
		.value("HOTROOM", HeatSource::HOTROOM);

	pybind11::class_<MopData>(m, "Mop")
		.def(pybind11::init<>())
		.def_readwrite("maximum_load", &MopData::maximum_load);

	pybind11::class_<Renewables>(m, "Renewables")
		.def(pybind11::init<>())
		.def_readwrite("yield_scalars", &Renewables::yield_scalars);

	pybind11::class_<TaskConfig>(m, "Config")
		.def(pybind11::init<>())
		.def_readwrite("capex_limit", &TaskConfig::capex_limit);


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

	pybind11::class_<CapexBreakdown>(m, "CapexBreakdown")
		.def_readonly("dhw_capex", &CapexBreakdown::dhw_capex)
		.def_readonly("ev_charger_cost", &CapexBreakdown::ev_charger_cost)
		.def_readonly("ev_charger_install", &CapexBreakdown::ev_charger_install)
		.def_readonly("grid_capex", &CapexBreakdown::grid_capex)
		.def_readonly("heatpump_capex", &CapexBreakdown::heatpump_capex)
		.def_readonly("ess_pcs_capex", &CapexBreakdown::ess_pcs_capex)
		.def_readonly("ess_enclosure_capex", &CapexBreakdown::ess_enclosure_capex)
		.def_readonly("ess_enclosure_disposal", &CapexBreakdown::ess_enclosure_disposal)
		.def_readonly("pv_panel_capex", &CapexBreakdown::pv_panel_capex)
		.def_readonly("pv_roof_capex", &CapexBreakdown::pv_roof_capex)
		.def_readonly("pv_ground_capex", &CapexBreakdown::pv_ground_capex)
		.def_readonly("pv_BoP_capex", &CapexBreakdown::pv_BoP_capex)
		.def_readonly("total_capex", &CapexBreakdown::total_capex)
		.def("__repr__", &capexBreakdownToString);

	// TODO - standalone functions should not be directly in the module
	m.def("calculate_capex", &calculate_capex);
}


std::string resultToString(const SimulationResult& result) {
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

std::string taskDataToString(const TaskData& taskData) {
	std::ostringstream oss;

	oss << "TaskData" << '\n';

	if (taskData.building) {
		oss << buildingToString(taskData.building.value()) << '\n';
	}

	if (taskData.data_centre) {
		oss << dataCentreToString(taskData.data_centre.value()) << '\n';
	}

	if (taskData.domestic_hot_water) {
		oss << dhwToString(taskData.domestic_hot_water.value()) << '\n';
	}

	if (taskData.electric_vehicles) {
		oss << evToString(taskData.electric_vehicles.value()) << '\n';
	}

	if (taskData.energy_storage_system) {
		oss << essToString(taskData.energy_storage_system.value()) << '\n';
	}

	if (taskData.grid) {
		oss << gridToString(taskData.grid.value()) << '\n';
	}

	if (taskData.heat_pump) {
		oss << heatpumpToString(taskData.heat_pump.value()) << '\n';
	}

	if (taskData.mop) {
		oss << mopToString(taskData.mop.value()) << '\n';
	}

	if (taskData.renewables) {
		oss << renewablesToString(taskData.renewables.value()) << '\n';
	}

	oss << configToString(taskData.config);

	return oss.str();

}

std::string buildingToString(const Building& b) {
	std::ostringstream oss;
	oss << "<Building scalar_heat_load=" << b.scalar_heat_load
		<< ", scalar_electrical_load=" << b.scalar_electrical_load
		<< ", fabric_intervention_index=" << b.fabric_intervention_index << ">";
	return oss.str();
}

std::string dataCentreToString(const DataCentreData& dc) {
	std::ostringstream oss;
	oss << "<DataCentre maximum_load=" << dc.maximum_load
		<< ", hotroom_temp=" << dc.hotroom_temp << ">";
	return oss.str();
}

std::string dhwToString(const DomesticHotWater& dhw) {
	std::ostringstream oss;
	oss << "<DomesticHotWater cylinder_volume=" << dhw.cylinder_volume << ">";
	return oss.str();
}

std::string evToString(const ElectricVehicles& ev) {
	std::ostringstream oss;
	oss << "<ElectricVehicles flexible_load_ratio=" << ev.flexible_load_ratio
		<< ", small_chargers=" << ev.small_chargers
		<< ", fast_chargers=" << ev.fast_chargers
		<< ", rapid_chargers=" << ev.rapid_chargers
		<< ", ultra_chargers=" << ev.ultra_chargers
		<< ", scalar_electrical_load=" << ev.scalar_electrical_load << ">";
	return oss.str();
}

std::string essToString(const EnergyStorageSystem& ess) {
	std::ostringstream oss;
	oss << "<EnergyStorageSystem capacity=" << ess.capacity
		<< ", charge_power=" << ess.charge_power
		<< ", discharge_power=" << ess.discharge_power
		<< ", battery_mode=" << enumToString(ess.battery_mode)
		<< ", initial_charge=" << ess.initial_charge << ">";
	return oss.str();
}

std::string gridToString(const GridData& grid) {
	std::ostringstream oss;
	oss << "<Grid export_headroom=" << grid.export_headroom
		<< ", grid_export=" << grid.grid_export
		<< ", grid_import=" << grid.grid_import
		<< ", import_headroom=" << grid.import_headroom
		<< ", min_power_factor=" << grid.min_power_factor
		<< ", tariff_index=" << grid.tariff_index << ">";
	return oss.str();
}

std::string heatpumpToString(const HeatPumpData& hp) {
	std::ostringstream oss;
	oss << "<HeatPump heat_power=" << hp.heat_power
		<< ", heat_source=" << enumToString(hp.heat_source)
		<< ", send_temp=" << hp.send_temp << ">";
	return oss.str();
}

std::string mopToString(const MopData& mop) {
	std::ostringstream oss;
	oss << "<Mop maximum_load=" << mop.maximum_load << ">";
	return oss.str();
}

std::string renewablesToString(const Renewables& r) {
	std::ostringstream oss;
	oss << "<Renewables yield_scalars=[";
	for (size_t i = 0; i < r.yield_scalars.size(); ++i) {
		oss << r.yield_scalars[i];
		if (i < r.yield_scalars.size() - 1) {
			oss << ", ";
		}
	}
	oss << "]>";
	return oss.str();
}

std::string configToString(const TaskConfig& config) {
	std::ostringstream oss;
	oss << "<Config capex_limit=" << config.capex_limit << ">";
	return oss.str();
}

std::string capexBreakdownToString(const CapexBreakdown& breakdown) {
	std::ostringstream oss;
	oss << "<CapexBreakdown " << "dhw_capex=" << breakdown.dhw_capex
		<< ", ev_charger_cost=" << breakdown.ev_charger_cost
		<< ", ev_charger_install=" << breakdown.ev_charger_install
		<< ", grid_capex=" << breakdown.grid_capex
		<< ", heatpump_capex=" << breakdown.heatpump_capex
		<< ", ess_pcs_capex=" << breakdown.ess_pcs_capex
		<< ", ess_enclosure_capex=" << breakdown.ess_enclosure_capex
		<< ", ess_enclosure_disposal=" << breakdown.ess_enclosure_disposal
		<< ", pv_panel_capex=" << breakdown.pv_panel_capex
		<< ", pv_roof_capex=" << breakdown.pv_roof_capex
		<< ", pv_ground_capex=" << breakdown.pv_ground_capex
		<< ", pv_BoP_capex=" << breakdown.pv_BoP_capex
		<< ", total_capex=" << breakdown.total_capex;
	return oss.str();
}
