#include "Capex.hpp"


CapexBreakdown calculate_capex_with_discounts(const SiteData& siteData, const TaskConfig& config, const TaskData& scenario) {

	const auto& capex_model = config.capex_model;

	// first calculate the unadjusted capex of the scenario
	auto capex_breakdown = calculate_capex(siteData, scenario, capex_model);

	if (config.use_boiler_upgrade_scheme) {
		if (is_elegible_for_boiler_upgrade_scheme(siteData.baseline, scenario)) {
			// discount the lower amount of the total heatpump cost and the maximum funding
			capex_breakdown.boiler_upgrade_scheme_funding = std::min(capex_model.max_boiler_upgrade_scheme_funding, capex_breakdown.heatpump_capex);
			capex_breakdown.total_capex -= capex_breakdown.boiler_upgrade_scheme_funding;
		}
	}

	// catch-all grant funding. Reduce the capex unconditionally down towards 0
	if (config.general_grant_funding > 0) {
		capex_breakdown.general_grant_funding = std::min(capex_breakdown.total_capex, config.general_grant_funding);;
		capex_breakdown.total_capex -= capex_breakdown.general_grant_funding;
	}

	return capex_breakdown;
}


CapexBreakdown calculate_capex(const SiteData& siteData, const TaskData& taskData, const CapexModel& capexModel) {
	CapexBreakdown capex_breakdown{};

	if (taskData.building && !taskData.building->incumbent) {
		capex_breakdown.building_fabric_capex = calculate_fabric_cost(siteData, taskData.building.value());

		size_t fabric_index = taskData.building->fabric_intervention_index;
		if (fabric_index == 0) {
			// this corresponds to no interventions
			capex_breakdown.fabric_cost_breakdown = {};
		}
		else {
			capex_breakdown.fabric_cost_breakdown = siteData.fabric_interventions[fabric_index - 1].cost_breakdown;
		}
	}

	if (taskData.domestic_hot_water && !taskData.domestic_hot_water->incumbent) {
		capex_breakdown.dhw_capex = calculate_dhw_cost(taskData.domestic_hot_water.value(), capexModel);
	}

	if (taskData.electric_vehicles && !taskData.electric_vehicles->incumbent) {
		EVCapex ev_capex = calculate_ev_cost(taskData.electric_vehicles.value(), capexModel);
		capex_breakdown.ev_charger_cost = ev_capex.charger_cost;
		capex_breakdown.ev_charger_install = ev_capex.charger_install;
	}

	if (taskData.energy_storage_system && !taskData.energy_storage_system->incumbent) {
		ESSCapex ess_capex = calculate_ess_cost(taskData.energy_storage_system.value(), capexModel);
		capex_breakdown.ess_enclosure_capex = ess_capex.enclosure_capex;
		capex_breakdown.ess_enclosure_disposal = ess_capex.enclosure_disposal;
		capex_breakdown.ess_pcs_capex = ess_capex.pcs_capex;
	}

	if (taskData.gas_heater && !taskData.gas_heater->incumbent) {
		capex_breakdown.gas_heater_capex = calculate_gas_heater_cost(taskData.gas_heater.value(), capexModel);
	}

	if (taskData.grid && !taskData.grid->incumbent) {
		capex_breakdown.grid_capex = calculate_grid_cost(taskData.grid.value(), capexModel);
	}

	if (taskData.heat_pump && !taskData.heat_pump->incumbent) {
		capex_breakdown.heatpump_capex = calculate_heatpump_cost(taskData.heat_pump.value(), capexModel);
	}

	for (const auto& panel : taskData.solar_panels) {
		if (!panel.incumbent) {
			SolarCapex solar_capex = calculate_solar_cost(panel, capexModel);
			capex_breakdown.pv_panel_capex += solar_capex.panel_capex;
			capex_breakdown.pv_ground_capex += solar_capex.ground_capex;
			capex_breakdown.pv_roof_capex += solar_capex.roof_capex;
			capex_breakdown.pv_BoP_capex += solar_capex.BoP_capex;
		}
	}

	capex_breakdown.total_capex = (
		capex_breakdown.building_fabric_capex 

		 + capex_breakdown.dhw_capex

		+ capex_breakdown.ev_charger_cost
		+ capex_breakdown.ev_charger_install

		+ capex_breakdown.gas_heater_capex

		+ capex_breakdown.grid_capex

		+ capex_breakdown.heatpump_capex

		+ capex_breakdown.ess_pcs_capex
		+ capex_breakdown.ess_enclosure_capex
		+ capex_breakdown.ess_enclosure_disposal

		+ capex_breakdown.pv_panel_capex
		+ capex_breakdown.pv_roof_capex
		+ capex_breakdown.pv_ground_capex
		+ capex_breakdown.pv_BoP_capex
	);

	return capex_breakdown;
}

float calculate_fabric_cost(const SiteData& siteData, const Building& building) {
	if (building.fabric_intervention_index == 0) {
		return 0.0f;
	}
	else {
		// we subtract one as a fabric_intervention_index of 0 corresponds to the base heating load with 0 cost
		return siteData.fabric_interventions[building.fabric_intervention_index - 1].cost;
	}
}

float calculate_dhw_cost(const DomesticHotWater& dhw, const CapexModel& model) {
	return calculate_piecewise_costs(model.dhw_prices, dhw.cylinder_volume);
}

EVCapex calculate_ev_cost(const ElectricVehicles& ev, const CapexModel& model) {
	EVCapex ev_capex{};

	ev_capex.charger_cost = (
		ev.small_chargers * model.ev_prices.small_cost
		+ ev.fast_chargers * model.ev_prices.fast_cost
		+ ev.rapid_chargers * model.ev_prices.rapid_cost
		+ ev.ultra_chargers * model.ev_prices.ultra_cost
	);

	ev_capex.charger_install = (
		ev.small_chargers * model.ev_prices.small_install
		+ ev.fast_chargers * model.ev_prices.fast_install
		+ ev.rapid_chargers * model.ev_prices.rapid_install
		+ ev.ultra_chargers * model.ev_prices.ultra_install
	);

	return ev_capex;
}

ESSCapex calculate_ess_cost(const EnergyStorageSystem& ess, const CapexModel& model) {
	ESSCapex ess_capex{};
	float ess_power = std::max(ess.charge_power, ess.discharge_power);

	ess_capex.pcs_capex = calculate_piecewise_costs(model.ess_pcs_prices, ess_power);
	ess_capex.enclosure_capex = calculate_piecewise_costs(model.ess_enclosure_prices, ess.capacity);
	ess_capex.enclosure_disposal = calculate_piecewise_costs(model.ess_enclosure_disposal_prices, ess.capacity);
	return ess_capex;
}

float calculate_gas_heater_cost(const GasCHData& gas, const CapexModel& model) {
	return calculate_piecewise_costs(model.gas_heater_prices, gas.maximum_output);
}

float calculate_grid_cost([[maybe_unused]] const GridData& grid, const CapexModel& model) {

	// set Grid upgrade to zero for the moment
	const float grid_upgrade_kw = 0.0f;
	return calculate_piecewise_costs(model.grid_prices, grid_upgrade_kw);
}

float calculate_heatpump_cost(const HeatPumpData& hp, const CapexModel& model) {
	return calculate_piecewise_costs(model.heatpump_prices, hp.heat_power);
}

SolarCapex calculate_solar_cost(const SolarData& panel, const CapexModel& model) {
	SolarCapex solar_capex{};

	// For now, it is assumed that all ALCHEMAI solar is roof mounted
	bool is_roof_mounted = true;

	if (is_roof_mounted) {
		solar_capex.roof_capex = calculate_piecewise_costs(model.pv_roof_prices, panel.yield_scalar);
	}
	else {
		solar_capex.ground_capex = calculate_piecewise_costs(model.pv_ground_prices, panel.yield_scalar);
	}

	solar_capex.panel_capex = calculate_piecewise_costs(model.pv_panel_prices, panel.yield_scalar);
	solar_capex.BoP_capex = calculate_piecewise_costs(model.pv_BoP_prices, panel.yield_scalar);

	return solar_capex;
}


bool is_elegible_for_boiler_upgrade_scheme(const TaskData& baseline, const TaskData& scenario) {
	// the baseline must contain a gas boiler, which is replaced in the scenario
	if (!baseline.gas_heater || scenario.gas_heater) {
		return false;
	}

	// the baseline cannot have a heatpump, the scenario must
	if (baseline.heat_pump || !scenario.heat_pump) {
		return false;
	}

	// the scenario heatpump must be a new install
	if (scenario.heat_pump->incumbent) {
		return false;
	}

	// The peak capacity is 45 kW thermal
	if (scenario.heat_pump->heat_power > 45) {
		return false;
	}

	// The heat source cannot be from a building
	if (scenario.heat_pump->heat_source == HeatSource::HOTROOM) {
		return false;
	}

	return true;
}
