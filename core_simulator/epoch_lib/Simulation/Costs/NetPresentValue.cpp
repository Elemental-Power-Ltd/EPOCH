#include "NetPresentValue.hpp"

#include <cmath>

ValueMetrics calculate_npv(const SiteData& siteData, const TaskConfig& config, const TaskData& scenario, const UsageData& usage) {
	ValueMetrics valueMetrics{};

	int horizon = config.npv_time_horizon;
	float discount_factor = config.npv_discount_factor;
	const auto& capex_model = config.capex_model;
	//const auto& opex_model = config.opex_model;

	std::vector<ComponentView> components{};

	if (scenario.building) {
		float fabric_cost = calculate_fabric_cost(siteData, scenario.building.value());
		components.emplace_back(make_component(scenario.building.value(), fabric_cost));
	}

	if (scenario.data_centre) {
		components.emplace_back(make_component(scenario.data_centre.value(), 0.0f));
	}

	if (scenario.domestic_hot_water) {
		float dhw_cost = calculate_dhw_cost(scenario.domestic_hot_water.value(), capex_model);
		components.emplace_back(make_component(scenario.domestic_hot_water.value(), dhw_cost));
	}

	if (scenario.electric_vehicles) {
		EVCapex ev_capex = calculate_ev_cost(scenario.electric_vehicles.value(), capex_model);
		components.emplace_back(make_component(scenario.electric_vehicles.value(), 
			ev_capex.charger_cost + ev_capex.charger_install));
	}

	if (scenario.energy_storage_system) {
		ESSCapex ess_capex = calculate_ess_cost(scenario.energy_storage_system.value(), capex_model);

		components.emplace_back(make_component(scenario.energy_storage_system.value(),
			ess_capex.enclosure_capex + ess_capex.enclosure_disposal + ess_capex.pcs_capex));
	}

	if (scenario.gas_heater) {
		float heater_cost = calculate_gas_heater_cost(scenario.gas_heater.value(), capex_model);
		components.emplace_back(make_component(scenario.gas_heater.value(), heater_cost));
	}

	if (scenario.grid) {
		float grid_cost = calculate_grid_cost(scenario.grid.value(), capex_model);
		components.emplace_back(make_component(scenario.grid.value(), grid_cost));
	}

	if (scenario.heat_pump) {
		float hp_cost = calculate_heatpump_cost(scenario.heat_pump.value(), capex_model);
		components.emplace_back(make_component(scenario.heat_pump.value(), hp_cost));
	}

	if (scenario.mop) {
		components.emplace_back(make_component(scenario.mop.value(), 0.0f));
	}

	for (const auto& panel : scenario.solar_panels) {
		ComponentView cv{};
		cv.age = panel.age;
		cv.lifetime = panel.lifetime;
		cv.incumbent = panel.incumbent;
		auto solar_capex = calculate_solar_cost(panel, capex_model);
		cv.capex = solar_capex.panel_capex + solar_capex.roof_capex + solar_capex.ground_capex + solar_capex.BoP_capex;
		components.emplace_back(cv);
	}


	float out = usage.elec_cost + usage.fuel_cost;
	float in = usage.export_revenue + usage.electric_vehicle_revenue +
		usage.high_priority_revenue + usage.low_priority_revenue;

	const float meter_balance = out - in;

	float total_opex = usage.opex_breakdown.ess_enclosure_opex
		+ usage.opex_breakdown.ess_pcs_opex
		+ usage.opex_breakdown.pv_opex;

	valueMetrics.annualised_cost += total_opex;

	std::vector<float> costs(horizon, meter_balance + total_opex);

	float total_funding = usage.capex_breakdown.general_grant_funding + usage.capex_breakdown.boiler_upgrade_scheme_funding;
	// subtract the total_funding from year 0
	costs[0] -= total_funding;


	for (const auto& comp : components) {
		if (!comp.incumbent) {
			costs[0] += comp.capex;
			valueMetrics.annualised_cost += (comp.capex / comp.lifetime);
		}

		// If a user has provided an age greater than the lifetime of this component,
		// then presume we replace it in year zero.
		float next_replacement = std::max(comp.lifetime - comp.age, 0.0f);
		//int next_replacement = std::ceil(comp.lifetime - comp.age);

		while (next_replacement < horizon) {
			// next_replacement should always be >=0 so truncate / round down with static_cast
			costs[static_cast<int>(next_replacement)] += comp.capex;
			next_replacement += comp.lifetime;
		}

		// finally subtract any residual value
		float residual_years = next_replacement - horizon;
		float residual_capex = comp.capex * (residual_years / comp.lifetime);

		costs.back() -= residual_capex;
	}

	double npv = 0;
	for (int year = 0; year < horizon; ++year) {
		double df = std::pow(1.0f + discount_factor, year);
		// we subtract as we have framed everything as a cost rather than a value
		npv -= costs[year] / df;
	}

	valueMetrics.net_present_value = static_cast<float>(npv);

	return valueMetrics;
}