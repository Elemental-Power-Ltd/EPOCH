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
		"    total_meter_cost: {}",
		metrics.total_gas_used,
		metrics.total_electricity_imported,
		metrics.total_electricity_generated,
		metrics.total_electricity_exported,
		metrics.total_electrical_shortfall,
		metrics.total_heat_shortfall,
		metrics.total_gas_import_cost,
		metrics.total_electricity_import_cost,
		metrics.total_electricity_export_gain,
		metrics.total_meter_cost
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

std::string gasHeaterToString(const GasCHData& gh) {
	std::ostringstream oss;
	oss << "<GasHeater maximum_output=" << gh.maximum_output
		<< ", gas_type=" << enumToString(gh.gas_type)
		<< ", boiler_efficiency=" << gh.boiler_efficiency << ">";
	return oss.str();
}

std::string gridToString(const GridData& grid) {
	std::ostringstream oss;
	oss << "<Grid grid_export=" << grid.grid_export
		<< ", grid_import=" << grid.grid_import
		<< ", import_headroom=" << grid.import_headroom
		<< ", tariff_index=" << grid.tariff_index 
		<< ", export_tariff=" << grid.export_tariff << ">";
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
	oss << "<Config capex_limit=" << config.capex_limit 
		<< "use_boiler_upgrade_scheme=" << config.use_boiler_upgrade_scheme 
		<< "general_grant_funding=" << config.general_grant_funding << ">";
	return oss.str();
}

std::string capexBreakdownToString(const CapexBreakdown& breakdown) {
	std::ostringstream oss;
	oss << "<CapexBreakdown "
		<< "building_fabric_capex=" << breakdown.building_fabric_capex
		<< "dhw_capex=" << breakdown.dhw_capex
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
