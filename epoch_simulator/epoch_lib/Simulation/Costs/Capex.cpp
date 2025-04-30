#include "Capex.hpp"


static CapexPrices capex_prices{};

CapexBreakdown calculate_capex_with_discounts(const SiteData& siteData, const TaskData& baseline, const TaskData& scenario) {

	// first calculate the unadjusted capex of the scenario
	auto capex_breakdown = calculate_capex(siteData, scenario);

	if (scenario.config.use_boiler_upgrade_scheme) {
		if (is_elegible_for_boiler_upgrade_scheme(baseline, scenario)) {
			// discount the lower amount of the total heatpump cost and the maximum funding
			capex_breakdown.boiler_upgrade_scheme_funding = std::min(capex_prices.max_boiler_upgrade_scheme_funding, capex_breakdown.heatpump_capex);
			capex_breakdown.total_capex -= capex_breakdown.boiler_upgrade_scheme_funding;
		}
	}

	// catch-all grant funding. Reduce the capex unconditionally down towards 0
	if (scenario.config.general_grant_funding > 0) {
		capex_breakdown.general_grant_funding = std::min(capex_breakdown.total_capex, scenario.config.general_grant_funding);;
		capex_breakdown.total_capex -= capex_breakdown.general_grant_funding;
	}

	return capex_breakdown;
}


CapexBreakdown calculate_capex(const SiteData& siteData, const TaskData& taskData) {
	CapexBreakdown capex_breakdown{};

	if (taskData.building) {
		calculate_building_capex(siteData, taskData.building.value(), capex_breakdown);
	}

	if (taskData.domestic_hot_water) {
		calculate_dhw_capex(taskData.domestic_hot_water.value(), capex_breakdown);
	}

	if (taskData.electric_vehicles) {
		calculate_ev_capex(taskData.electric_vehicles.value(), capex_breakdown);
	}

	if (taskData.energy_storage_system) {
		calculate_ess_capex(taskData.energy_storage_system.value(), capex_breakdown);
	}

	if (taskData.grid) {
		calculate_grid_capex(taskData.grid.value(), capex_breakdown);
	}

	if (taskData.heat_pump) {
		calculate_heatpump_capex(taskData.heat_pump.value(), capex_breakdown);
	}

	if (taskData.renewables) {
		calculate_renewables_capex(taskData.renewables.value(), capex_breakdown);
	}

	// TODO JW
	//  refactor has currently removed the project_plan_develop_EPC and project_plan_develop_Grid scalars
	capex_breakdown.total_capex = (
		capex_breakdown.building_fabric_capex 

		 + capex_breakdown.dhw_capex

		+ capex_breakdown.ev_charger_cost
		+ capex_breakdown.ev_charger_install

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

void calculate_building_capex(const SiteData& siteData, const Building& building, CapexBreakdown& capex_breakdown) {
	if (building.fabric_intervention_index == 0) {
		capex_breakdown.building_fabric_capex = 0.0f;
	}
	else {
		// we subtract one as a fabric_intervention_index of 0 corresponds to the base heating load with 0 cost
		capex_breakdown.building_fabric_capex = siteData.fabric_interventions[building.fabric_intervention_index - 1].cost;
	}
}

void calculate_dhw_capex(const DomesticHotWater& dhw, CapexBreakdown& capex_breakdown) {
	capex_breakdown.dhw_capex = calculate_three_tier_costs(capex_prices.dhw_prices, dhw.cylinder_volume);
}

void calculate_ev_capex(const ElectricVehicles& ev, CapexBreakdown& capex_breakdown) {
	capex_breakdown.ev_charger_cost = (
		ev.small_chargers * capex_prices.ev_prices.small_cost
		+ ev.fast_chargers * capex_prices.ev_prices.fast_cost
		+ ev.rapid_chargers * capex_prices.ev_prices.rapid_cost
		+ ev.ultra_chargers * capex_prices.ev_prices.ultra_cost
	);

	capex_breakdown.ev_charger_install = (
		ev.small_chargers * capex_prices.ev_prices.small_install
		+ ev.fast_chargers * capex_prices.ev_prices.fast_install
		+ ev.rapid_chargers * capex_prices.ev_prices.rapid_install
		+ ev.ultra_chargers * capex_prices.ev_prices.ultra_install
	);
}

void calculate_ess_capex(const EnergyStorageSystem& ess, CapexBreakdown& capex_breakdown) {

	float ess_power = std::max(ess.charge_power, ess.discharge_power);

	capex_breakdown.ess_pcs_capex = calculate_three_tier_costs(capex_prices.ess_pcs_prices, ess_power);
	capex_breakdown.ess_enclosure_capex = calculate_three_tier_costs(capex_prices.ess_enclosure_prices, ess.capacity);
	capex_breakdown.ess_enclosure_disposal = calculate_three_tier_costs(capex_prices.ess_enclosure_disposal_prices, ess.capacity);
}

void calculate_grid_capex(const GridData& grid, CapexBreakdown& capex_breakdown) {
	// set Grid upgrade to zero for the moment
	const float grid_upgrade_kw = 0.0f;
	capex_breakdown.grid_capex = calculate_three_tier_costs(capex_prices.grid_prices, grid_upgrade_kw);
}

void calculate_heatpump_capex(const HeatPumpData& hp, CapexBreakdown& capex_breakdown) {
	capex_breakdown.heatpump_capex = calculate_three_tier_costs(capex_prices.heatpump_prices, hp.heat_power);
}

void calculate_renewables_capex(const Renewables& renewables, CapexBreakdown& capex_breakdown) {

	float pv_kWp_total = 0;
	for (auto& scalar : renewables.yield_scalars) {
		pv_kWp_total += scalar;
	}

	// For now, it is assumed that all ALCHEMAI solar is roof mounted
	float pv_kWp_roof = pv_kWp_total;
	float pv_kWp_ground = 0.0f;

	capex_breakdown.pv_panel_capex = calculate_three_tier_costs(capex_prices.pv_panel_prices, pv_kWp_total);
	capex_breakdown.pv_roof_capex = calculate_three_tier_costs(capex_prices.pv_roof_prices, pv_kWp_roof);
	capex_breakdown.pv_ground_capex = calculate_three_tier_costs(capex_prices.pv_ground_prices, pv_kWp_ground);
	capex_breakdown.pv_BoP_capex = calculate_three_tier_costs(capex_prices.pv_BoP_prices, pv_kWp_total);
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
