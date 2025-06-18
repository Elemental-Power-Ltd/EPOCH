#include "ToString.hpp"
#include "EnumToString.hpp"


std::string resultToString(const SimulationResult& result) {
	return std::format(
		"SimulationResult(\n"
		"  carbon_balance_scope_1: {},\n"
		"  carbon_balance_scope_2: {},\n"
		"  meter_balance: {},\n"
		"  operating_balance: {},\n"
		"  cost_balance: {},\n"
		"  capex: {},\n"
		"  payback_horizon: {},\n"
		"  annualised_cost: {},\n"
		"  npv_balance: {},\n"
		"  scenario: {}\n"
		"  baseline: {}\n"
		")",
		result.scenario_carbon_balance_scope_1,
		result.scenario_carbon_balance_scope_2,
		result.meter_balance,
		result.operating_balance,
		result.scenario_cost_balance,
		result.project_CAPEX,
		result.payback_horizon_years,
		result.total_annualised_cost,
		result.npv_balance,
		metricsToString(result.metrics),
		metricsToString(result.baseline_metrics)
	);
}

std::string metricsToString(const SimulationMetrics& metrics) {
	return std::format(
		"\n    total_gas_used: {},\n"
		"    total_electricity_imported: {},\n"
		"    total_electricity_generated: {},\n"
		"    total_electricity_exported: {},\n"
		"    total_electrical_shortfall: {},\n"
		"    total_heat_shortfall: {},\n"
		"    total_gas_import_cost: {},\n"
		"    total_electricity_import_cost: {},\n"
		"    total_electricity_export_gain: {},\n"
		"    total_meter_cost: {},\n"
		"    total_operating_cost: {},\n"
		"    total_net_present_value: {},\n",
		metrics.total_gas_used,
		metrics.total_electricity_imported,
		metrics.total_electricity_generated,
		metrics.total_electricity_exported,
		metrics.total_electrical_shortfall,
		metrics.total_heat_shortfall,
		metrics.total_gas_import_cost,
		metrics.total_electricity_import_cost,
		metrics.total_electricity_export_gain,
		metrics.total_meter_cost,
		metrics.total_operating_cost,
		metrics.total_net_present_value
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

	if (taskData.gas_heater) {
		oss << gasHeaterToString(taskData.gas_heater.value()) << '\n';
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

	for (const auto& solar : taskData.solar_panels) {
		oss << solarToString(solar) << '\n';
	}

	oss << configToString(taskData.config);

	return oss.str();

}

std::string buildingToString(const Building& b) {
	std::ostringstream oss;
	oss << "<Building scalar_heat_load=" << b.scalar_heat_load
		<< ", scalar_electrical_load=" << b.scalar_electrical_load
		<< ", fabric_intervention_index=" << b.fabric_intervention_index 
		<< ", incumbent=" << b.incumbent
		<< ", age=" << b.age
		<< ", lifetime=" << b.lifetime
		<< ">";
	return oss.str();
}

std::string dataCentreToString(const DataCentreData& dc) {
	std::ostringstream oss;
	oss << "<DataCentre maximum_load=" << dc.maximum_load
		<< ", hotroom_temp=" << dc.hotroom_temp 
		<< ", incumbent=" << dc.incumbent
		<< ", age=" << dc.age
		<< ", lifetime=" << dc.lifetime
		<< ">";
	return oss.str();
}

std::string dhwToString(const DomesticHotWater& dhw) {
	std::ostringstream oss;
	oss << "<DomesticHotWater cylinder_volume=" << dhw.cylinder_volume 
		<< ", incumbent=" << dhw.incumbent
		<< ", age=" << dhw.age
		<< ", lifetime=" << dhw.lifetime
		<< ">";
	return oss.str();
}

std::string evToString(const ElectricVehicles& ev) {
	std::ostringstream oss;
	oss << "<ElectricVehicles flexible_load_ratio=" << ev.flexible_load_ratio
		<< ", small_chargers=" << ev.small_chargers
		<< ", fast_chargers=" << ev.fast_chargers
		<< ", rapid_chargers=" << ev.rapid_chargers
		<< ", ultra_chargers=" << ev.ultra_chargers
		<< ", scalar_electrical_load=" << ev.scalar_electrical_load 
		<< ", incumbent=" << ev.incumbent
		<< ", age=" << ev.age
		<< ", lifetime=" << ev.lifetime
		<< ">";
	return oss.str();
}

std::string essToString(const EnergyStorageSystem& ess) {
	std::ostringstream oss;
	oss << "<EnergyStorageSystem capacity=" << ess.capacity
		<< ", charge_power=" << ess.charge_power
		<< ", discharge_power=" << ess.discharge_power
		<< ", battery_mode=" << enumToString(ess.battery_mode)
		<< ", initial_charge=" << ess.initial_charge 
		<< ", incumbent=" << ess.incumbent
		<< ", age=" << ess.age
		<< ", lifetime=" << ess.lifetime
		<< ">";
	return oss.str();
}

std::string gasHeaterToString(const GasCHData& gh) {
	std::ostringstream oss;
	oss << "<GasHeater maximum_output=" << gh.maximum_output
		<< ", gas_type=" << enumToString(gh.gas_type)
		<< ", boiler_efficiency=" << gh.boiler_efficiency 
		<< ", incumbent=" << gh.incumbent
		<< ", age=" << gh.age
		<< ", lifetime=" << gh.lifetime 
		<< ">";
	return oss.str();
}

std::string gridToString(const GridData& grid) {
	std::ostringstream oss;
	oss << "<Grid grid_export=" << grid.grid_export
		<< ", grid_import=" << grid.grid_import
		<< ", import_headroom=" << grid.import_headroom
		<< ", tariff_index=" << grid.tariff_index 
		<< ", export_tariff=" << grid.export_tariff 
		<< ", incumbent=" << grid.incumbent
		<< ", age=" << grid.age
		<< ", lifetime=" << grid.lifetime
		<< ">";
	return oss.str();
}

std::string heatpumpToString(const HeatPumpData& hp) {
	std::ostringstream oss;
	oss << "<HeatPump heat_power=" << hp.heat_power
		<< ", heat_source=" << enumToString(hp.heat_source)
		<< ", send_temp=" << hp.send_temp 
		<< ", incumbent=" << hp.incumbent
		<< ", age=" << hp.age
		<< ", lifetime=" << hp.lifetime
		<< ">";
	return oss.str();
}

std::string mopToString(const MopData& mop) {
	std::ostringstream oss;
	oss << "<Mop maximum_load=" << mop.maximum_load 
		<< ", incumbent=" << mop.incumbent
		<< ", age=" << mop.age
		<< ", lifetime=" << mop.lifetime
		<< ">";
	return oss.str();
}

std::string solarToString(const SolarData& solar) {
	std::ostringstream oss;
	oss << "<Solar maximum_load=" << solar.yield_scalar
		<< ", yield_index=" << solar.yield_index
		<< ", incumbent=" << solar.incumbent
		<< ", age=" << solar.age
		<< ", lifetime=" << solar.lifetime
		<< ">";
	return oss.str();
}

std::string configToString(const TaskConfig& config) {
	std::ostringstream oss;
	oss << "<Config capex_limit=" << config.capex_limit 
		<< ", use_boiler_upgrade_scheme=" << config.use_boiler_upgrade_scheme 
		<< ", general_grant_funding=" << config.general_grant_funding 
		<< ", npv_time_horizon=" << config.npv_time_horizon
		<< ", npv_discount_factor=" << config.npv_discount_factor
		<< ">";
	return oss.str();
}

std::string capexBreakdownToString(const CapexBreakdown& breakdown) {
	std::ostringstream oss;
	oss << "<CapexBreakdown "
		<< "building_fabric_capex=" << breakdown.building_fabric_capex
		<< "dhw_capex=" << breakdown.dhw_capex
		<< ", ev_charger_cost=" << breakdown.ev_charger_cost
		<< ", ev_charger_install=" << breakdown.ev_charger_install
		<< ", gas_heater_capex=" << breakdown.gas_heater_capex
		<< ", grid_capex=" << breakdown.grid_capex
		<< ", heatpump_capex=" << breakdown.heatpump_capex
		<< ", ess_pcs_capex=" << breakdown.ess_pcs_capex
		<< ", ess_enclosure_capex=" << breakdown.ess_enclosure_capex
		<< ", ess_enclosure_disposal=" << breakdown.ess_enclosure_disposal
		<< ", pv_panel_capex=" << breakdown.pv_panel_capex
		<< ", pv_roof_capex=" << breakdown.pv_roof_capex
		<< ", pv_ground_capex=" << breakdown.pv_ground_capex
		<< ", pv_BoP_capex=" << breakdown.pv_BoP_capex
		<< ", boiler_upgrade_scheme_funding=" << breakdown.boiler_upgrade_scheme_funding
		<< ", general_grant_funding=" << breakdown.general_grant_funding
		<< ", total_capex=" << breakdown.total_capex;
	return oss.str();
}
