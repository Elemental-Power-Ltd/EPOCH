#include "Bindings.hpp"

#include <format>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>
#include <pybind11/stl/filesystem.h>
#include <pybind11/native_enum.h>
#include <sstream>

#include "Simulate_py.hpp"
#include "../epoch_lib/Simulation/TaskData.hpp"
#include "../epoch_lib/Definitions.hpp"
#include "../epoch_lib/io/EnumToString.hpp"
#include "../epoch_lib/io/TaskDataJson.hpp"
#include "../epoch_lib/io/ToString.hpp"
#include "../epoch_lib/Portfolio/Portfolio.hpp"
#include "../epoch_lib/Simulation/Costs/CostData.hpp"
#include "../epoch_lib/Simulation/Costs/Capex.hpp"


PYBIND11_MODULE(epoch_simulator, m) {
	m.attr("__version__") = EPOCH_VERSION;

	pybind11::class_<Simulator_py>(m, "Simulator")
		.def_static("from_file", &Simulator_py::from_file, pybind11::arg("site_data_path"), pybind11::arg("config_path"))
		.def_static("from_json", &Simulator_py::from_json, pybind11::arg("site_data_json_str"), pybind11::arg("config_json_str"))
		.def("simulate_scenario", &Simulator_py::simulateScenario,
			pybind11::arg("taskData"),
			pybind11::arg("fullReporting") = false)
		.def("is_valid", &Simulator_py::isValid, pybind11::arg("taskData"))
		.def("calculate_capex", &Simulator_py::calculateCapexWithDiscounts, pybind11::arg("taskData"))
		.def_readonly("config", &Simulator_py::config);

	pybind11::class_<TaskData>(m, "TaskData")
		.def(pybind11::init<>())
		.def_readwrite("building", &TaskData::building)
		.def_readwrite("data_centre", &TaskData::data_centre)
		.def_readwrite("domestic_hot_water", &TaskData::domestic_hot_water)
		.def_readwrite("electric_vehicles", &TaskData::electric_vehicles)
		.def_readwrite("energy_storage_system", &TaskData::energy_storage_system)
		.def_readwrite("gas_heater", &TaskData::gas_heater)
		.def_readwrite("grid", &TaskData::grid)
		.def_readwrite("heat_pump", &TaskData::heat_pump)
		.def_readwrite("mop", &TaskData::mop)
		.def_readwrite("solar_panels", &TaskData::solar_panels)
		.def_static("from_json", [](const std::string& json_str) {
			nlohmann::json j = nlohmann::json::parse(json_str);
			return j.get<TaskData>();
		})
		.def("to_json", [](const TaskData& self) {
			nlohmann::json j = self;
			return j.dump();
		})
		.def("__repr__", &taskDataToString)
		.def("__hash__", [](const TaskData& self){ return std::hash<TaskData>{}(self);})
		.def("__eq__", &TaskData::operator==);

	pybind11::class_<Building>(m, "Building")
		.def(pybind11::init<>())
		.def_readwrite("scalar_heat_load", &Building::scalar_heat_load)
		.def_readwrite("scalar_electrical_load", &Building::scalar_electrical_load)
		.def_readwrite("fabric_intervention_index", &Building::fabric_intervention_index)
		.def_readwrite("floor_area", &Building::floor_area)
		.def_readwrite("incumbent", &Building::incumbent)
		.def_readwrite("age", &Building::age)
		.def_readwrite("lifetime", &Building::lifetime);

	pybind11::class_<DataCentreData>(m, "DataCentre")
		.def(pybind11::init<>())
		.def_readwrite("maximum_load", &DataCentreData::maximum_load)
		.def_readwrite("hotroom_temp", &DataCentreData::hotroom_temp)
		.def_readwrite("incumbent", &DataCentreData::incumbent)
		.def_readwrite("age", &DataCentreData::age)
		.def_readwrite("lifetime", &DataCentreData::lifetime);


	pybind11::class_<DomesticHotWater>(m, "DomesticHotWater")
		.def(pybind11::init<>())
		.def_readwrite("cylinder_volume", &DomesticHotWater::cylinder_volume)
		.def_readwrite("incumbent", &DomesticHotWater::incumbent)
		.def_readwrite("age", &DomesticHotWater::age)
		.def_readwrite("lifetime", &DomesticHotWater::lifetime);


	pybind11::class_<ElectricVehicles>(m, "ElectricVehicles")
		.def(pybind11::init<>())
		.def_readwrite("flexible_load_ratio", &ElectricVehicles::flexible_load_ratio)
		.def_readwrite("small_chargers", &ElectricVehicles::small_chargers)
		.def_readwrite("fast_chargers", &ElectricVehicles::fast_chargers)
		.def_readwrite("rapid_chargers", &ElectricVehicles::rapid_chargers)
		.def_readwrite("ultra_chargers", &ElectricVehicles::ultra_chargers)
		.def_readwrite("scalar_electrical_load", &ElectricVehicles::scalar_electrical_load)
		.def_readwrite("incumbent", &ElectricVehicles::incumbent)
		.def_readwrite("age", &ElectricVehicles::age)
		.def_readwrite("lifetime", &ElectricVehicles::lifetime);


	pybind11::class_<EnergyStorageSystem>(m, "EnergyStorageSystem")
		.def(pybind11::init<>())
		.def_readwrite("capacity", &EnergyStorageSystem::capacity)
		.def_readwrite("charge_power", &EnergyStorageSystem::charge_power)
		.def_readwrite("discharge_power", &EnergyStorageSystem::discharge_power)
		.def_readwrite("battery_mode", &EnergyStorageSystem::battery_mode)
		.def_readwrite("initial_charge", &EnergyStorageSystem::initial_charge)
		.def_readwrite("incumbent", &EnergyStorageSystem::incumbent)
		.def_readwrite("age", &EnergyStorageSystem::age)
		.def_readwrite("lifetime", &EnergyStorageSystem::lifetime);


	pybind11::enum_<BatteryMode>(m, "BatteryMode")
		.value("CONSUME", BatteryMode::CONSUME)
		.value("CONSUME_PLUS", BatteryMode::CONSUME_PLUS);

	pybind11::class_<GasCHData>(m, "GasHeater")
		.def(pybind11::init<>())
		.def_readwrite("maximum_output", &GasCHData::maximum_output)
		.def_readwrite("gas_type", &GasCHData::gas_type)
		.def_readwrite("boiler_efficiency", &GasCHData::boiler_efficiency)
		.def_readwrite("incumbent", &GasCHData::incumbent)
		.def_readwrite("age", &GasCHData::age)
		.def_readwrite("lifetime", &GasCHData::lifetime);


	pybind11::enum_<GasType>(m, "GasType")
		.value("NATURAL_GAS", GasType::NATURAL_GAS)
		.value("LIQUID_PETROLEUM_GAS", GasType::LIQUID_PETROLEUM_GAS);

	pybind11::class_<GridData>(m, "Grid")
		.def(pybind11::init<>())
		.def_readwrite("grid_export", &GridData::grid_export)
		.def_readwrite("grid_import", &GridData::grid_import)
		.def_readwrite("import_headroom", &GridData::import_headroom)
		.def_readwrite("tariff_index", &GridData::tariff_index)
		.def_readwrite("export_tariff", &GridData::export_tariff)
		.def_readwrite("incumbent", &GridData::incumbent)
		.def_readwrite("age", &GridData::age)
		.def_readwrite("lifetime", &GridData::lifetime);


	pybind11::class_<HeatPumpData>(m, "HeatPump")
		.def(pybind11::init<>())
		.def_readwrite("heat_power", &HeatPumpData::heat_power)
		.def_readwrite("heat_source", &HeatPumpData::heat_source)
		.def_readwrite("send_temp", &HeatPumpData::send_temp)
		.def_readwrite("incumbent", &HeatPumpData::incumbent)
		.def_readwrite("age", &HeatPumpData::age)
		.def_readwrite("lifetime", &HeatPumpData::lifetime);


	pybind11::enum_<HeatSource>(m, "HeatSource")
		.value("AMBIENT_AIR", HeatSource::AMBIENT_AIR)
		.value("HOTROOM", HeatSource::HOTROOM);

	pybind11::class_<MopData>(m, "Mop")
		.def(pybind11::init<>())
		.def_readwrite("maximum_load", &MopData::maximum_load)
		.def_readwrite("incumbent", &MopData::incumbent)
		.def_readwrite("age", &MopData::age)
		.def_readwrite("lifetime", &MopData::lifetime);


	pybind11::class_<SolarData>(m, "SolarPanel")
		.def(pybind11::init<>())
		.def_readwrite("yield_scalar", &SolarData::yield_scalar)
		.def_readwrite("yield_index", &SolarData::yield_index)
		.def_readwrite("incumbent", &SolarData::incumbent)
		.def_readwrite("age", &SolarData::age)
		.def_readwrite("lifetime", &SolarData::lifetime);

	pybind11::class_<TaskConfig>(m, "Config")
		.def(pybind11::init<>())
		.def_readwrite("capex_limit", &TaskConfig::capex_limit)
		.def_readwrite("use_boiler_upgrade_scheme", &TaskConfig::use_boiler_upgrade_scheme)
		.def_readwrite("general_grant_funding", &TaskConfig::general_grant_funding)
		.def_readwrite("npv_time_horizon", &TaskConfig::npv_time_horizon)
		.def_readwrite("npv_discount_factor", &TaskConfig::npv_discount_factor)
		.def("__repr__", &configToString);


	pybind11::class_<SimulationResult>(m, "SimulationResult")
		// provide a default-initialised constructor, primarily for tests in the Optimisation service
		.def(pybind11::init<>())
		.def_readwrite("comparison", &SimulationResult::comparison)
		.def_readwrite("metrics", &SimulationResult::metrics)
		.def_readwrite("baseline_metrics", &SimulationResult::baseline_metrics)
		.def_readwrite("scenario_capex_breakdown", &SimulationResult::scenario_capex_breakdown)
		.def_readwrite("report_data", &SimulationResult::report_data)
		.def("__repr__", &resultToString);

	pybind11::class_<ScenarioComparison>(m, "ScenarioComparison")
		.def_readwrite("meter_balance", &ScenarioComparison::meter_balance)
		.def_readwrite("operating_balance", &ScenarioComparison::operating_balance)
		.def_readwrite("cost_balance", &ScenarioComparison::cost_balance)
		.def_readwrite("npv_balance", &ScenarioComparison::npv_balance)
		.def_readwrite("payback_horizon_years", &ScenarioComparison::payback_horizon_years)
		.def_readwrite("carbon_balance_scope_1", &ScenarioComparison::carbon_balance_scope_1)
		.def_readwrite("carbon_balance_scope_2", &ScenarioComparison::carbon_balance_scope_2)
		.def_readwrite("combined_carbon_balance", &ScenarioComparison::combined_carbon_balance)
		.def_readwrite("carbon_cost", &ScenarioComparison::carbon_cost);

	pybind11::native_enum<RatingGrade>(m, "RatingGrade", "enum.IntEnum", "Rating bands for SAP grades")
		.value("A", RatingGrade::A)
		.value("B", RatingGrade::B)
		.value("C", RatingGrade::C)
		.value("D", RatingGrade::D)
		.value("E", RatingGrade::E)
		.value("F", RatingGrade::F)
		.value("G", RatingGrade::G)
		.export_values()
		.finalize();

	pybind11::class_<SimulationMetrics>(m, "SimulationMetrics")
		.def_readwrite("total_gas_used", &SimulationMetrics::total_gas_used)
		.def_readwrite("total_electricity_imported", &SimulationMetrics::total_electricity_imported)
		.def_readwrite("total_electricity_generated", &SimulationMetrics::total_electricity_generated)
		.def_readwrite("total_electricity_exported", &SimulationMetrics::total_electricity_exported)
		.def_readwrite("total_electricity_curtailed", &SimulationMetrics::total_electricity_curtailed)
		.def_readwrite("total_electricity_used", &SimulationMetrics::total_electricity_used)

		.def_readwrite("total_electrical_shortfall", &SimulationMetrics::total_electrical_shortfall)
		.def_readwrite("total_heat_shortfall", &SimulationMetrics::total_heat_shortfall)
		.def_readwrite("total_ch_shortfall", &SimulationMetrics::total_ch_shortfall)
		.def_readwrite("total_dhw_shortfall", &SimulationMetrics::total_dhw_shortfall)

		.def_readwrite("total_capex", &SimulationMetrics::total_capex)
		.def_readwrite("total_gas_import_cost", &SimulationMetrics::total_gas_import_cost)
		.def_readwrite("total_electricity_import_cost", &SimulationMetrics::total_electricity_import_cost)
		.def_readwrite("total_electricity_export_gain", &SimulationMetrics::total_electricity_export_gain)

		.def_readwrite("total_meter_cost", &SimulationMetrics::total_meter_cost)
		.def_readwrite("total_operating_cost", &SimulationMetrics::total_operating_cost)
		.def_readwrite("total_annualised_cost", &SimulationMetrics::total_annualised_cost)
		.def_readwrite("total_net_present_value", &SimulationMetrics::total_net_present_value)

		.def_readwrite("total_scope_1_emissions", &SimulationMetrics::total_scope_1_emissions)
		.def_readwrite("total_scope_2_emissions", &SimulationMetrics::total_scope_2_emissions)
		.def_readwrite("total_combined_carbon_emissions", &SimulationMetrics::total_combined_carbon_emissions)

		.def_readwrite("environmental_impact_score", &SimulationMetrics::environmental_impact_score)
		.def_readwrite("environmental_impact_grade", &SimulationMetrics::environmental_impact_grade)
		.def("__repr__", &metricsToString);

	pybind11::class_<ReportData>(m, "ReportData")
		.def_readonly("Actual_import_shortfall", &ReportData::Actual_import_shortfall)
		.def_readonly("Actual_curtailed_export", &ReportData::Actual_curtailed_export)
		.def_readonly("Heat_shortfall", &ReportData::Heat_shortfall)
		.def_readonly("CH_shortfall", &ReportData::CH_shortfall)
		.def_readonly("DHW_Shortfall", &ReportData::DHW_Shortfall)
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
		.def_readonly("DHW_immersion_top_up", &ReportData::DHW_immersion_top_up)
		.def_readonly("ASHP_elec_load", &ReportData::ASHP_elec_load)
		.def_readonly("ASHP_DHW_output", &ReportData::ASHP_DHW_output)
		.def_readonly("ASHP_CH_output", &ReportData::ASHP_CH_output)
		.def_readonly("ASHP_free_heat", &ReportData::ASHP_free_heat)
		.def_readonly("ASHP_used_hotroom_heat", &ReportData::ASHP_used_hotroom_heat);

	pybind11::class_<CapexBreakdown>(m, "CapexBreakdown")
		.def_readonly("building_fabric_capex", &CapexBreakdown::building_fabric_capex)
		.def_readonly("dhw_capex", &CapexBreakdown::dhw_capex)
		.def_readonly("ev_charger_cost", &CapexBreakdown::ev_charger_cost)
		.def_readonly("ev_charger_install", &CapexBreakdown::ev_charger_install)
		.def_readonly("gas_heater_capex", &CapexBreakdown::gas_heater_capex)
		.def_readonly("grid_capex", &CapexBreakdown::grid_capex)
		.def_readonly("heatpump_capex", &CapexBreakdown::heatpump_capex)
		.def_readonly("ess_pcs_capex", &CapexBreakdown::ess_pcs_capex)
		.def_readonly("ess_enclosure_capex", &CapexBreakdown::ess_enclosure_capex)
		.def_readonly("ess_enclosure_disposal", &CapexBreakdown::ess_enclosure_disposal)
		.def_readonly("pv_panel_capex", &CapexBreakdown::pv_panel_capex)
		.def_readonly("pv_roof_capex", &CapexBreakdown::pv_roof_capex)
		.def_readonly("pv_ground_capex", &CapexBreakdown::pv_ground_capex)
		.def_readonly("pv_BoP_capex", &CapexBreakdown::pv_BoP_capex)
		.def_readonly("boiler_upgrade_scheme_funding", &CapexBreakdown::boiler_upgrade_scheme_funding)
		.def_readonly("general_grant_funding", &CapexBreakdown::general_grant_funding)
		.def_readonly("total_capex", &CapexBreakdown::total_capex)
		.def("__repr__", &capexBreakdownToString);

	m.def("aggregate_site_results", &aggregateSiteResults,
		pybind11::arg("site_results"));

}
