#include "Usage.hpp"


/**
* internal method to sum up the usage data for both baseline and scenario data
*/
UsageData sumUsage(const SiteData& siteData, const TaskData& taskData, const CostVectors& costVectors) {
	UsageData usage{};

	// TODO - extract these somewhere else (make this a class or put make these globals?)
	const float LPG_cost_price = 0.122f; // £/kWh
	const float mains_gas_kg_C02e = 0.201f; // kg/kWh(w2h) 
	const float LPG_kg_C02e = 0.239f; // kg/kWh (well2heat)
	const float boiler_efficiency = 0.9f;

	const float EV_low_price = 0.45f; // £/kWh site price for destination EV charging, 22 kW and below
	const float EV_high_price = 0.79f; //£/kWh site price for high power EV charging, 50 KW and above
	const float high_priority_price = 0.50f; // £/kWh site price for data centre compute (hi priority load)

	const float fallback_mains_gas_price = 0.068f; // necessary for cases where we have a mop component but no gas heater
	// assume this is just the equivalent lowest cost fossil fuel derived hea
	const float low_priority_price = taskData.gas_heater ? taskData.gas_heater->fixed_gas_price : fallback_mains_gas_price;

	// supress unused warnings
	(void)EV_high_price;
	(void)LPG_cost_price;

	if (taskData.grid) {
		// SiteData grid intensity is in g/kWh
		// our reporting metrics are in kg/kWh so we need to convert
		constexpr float g_to_kg = 0.001f;

		auto& tariff = siteData.import_tariffs[taskData.grid->tariff_index];
		usage.elec_cost = costVectors.grid_import_e.dot(tariff);
		usage.elec_kg_CO2e = costVectors.grid_import_e.dot(siteData.grid_co2) * g_to_kg;
		usage.export_revenue = costVectors.grid_export_e.dot(costVectors.grid_export_prices);
		usage.export_kg_CO2e = -(costVectors.grid_export_e.dot(siteData.grid_co2)) * g_to_kg;
	}


	if (taskData.gas_heater) {
		float gas_price = taskData.gas_heater->fixed_gas_price;
		float CO2e = taskData.gas_heater->gas_type == GasType::NATURAL_GAS ? mains_gas_kg_C02e : LPG_kg_C02e;

		usage.fuel_cost = costVectors.gas_import_h.sum() * gas_price;
		usage.fuel_kg_CO2e = costVectors.gas_import_h.sum() * CO2e;
	}

	if (taskData.mop) {
		// assume the counterfactual of LP heat is gas based heat emissions
		usage.low_priority_kg_CO2e_avoided = costVectors.actual_low_priority_load_e.sum() * mains_gas_kg_C02e;
		usage.low_priority_revenue = costVectors.actual_low_priority_load_e.sum() * low_priority_price / boiler_efficiency;
	}

	if (taskData.data_centre) {
		usage.high_priority_revenue = costVectors.actual_data_centre_load_e.sum() * high_priority_price;
	}

	if (taskData.electric_vehicles) {
		// will need to separate out EV charge tariffs later, assume all destination charging for now
		usage.electric_vehicle_revenue = costVectors.actual_ev_load_e.sum() * EV_low_price;
	}

	usage.carbon_scope_1_kg_CO2e = usage.fuel_kg_CO2e - usage.low_priority_kg_CO2e_avoided;
	// export_kg_CO2e <= 0
	// it is the CO2 'saved' by exporting 100% green electricity to the grid
	usage.carbon_scope_2_kg_CO2e = usage.elec_kg_CO2e + usage.export_kg_CO2e;

	return usage;
}


float calculate_meter_cost(const UsageData& usage) {
	float costs = usage.elec_cost + usage.fuel_cost;
	float revenues = usage.export_revenue + usage.electric_vehicle_revenue + usage.high_priority_revenue + usage.low_priority_revenue;
	return costs - revenues;
}


UsageData calculateBaselineUsage(const SiteData& siteData, const CostVectors& costVectors) {
	auto usage = sumUsage(siteData, siteData.baseline, costVectors);
	usage.capex_breakdown = calculate_capex(siteData, siteData.baseline);
	usage.opex_breakdown = calculate_opex(siteData.baseline);
	usage.total_meter_cost = calculate_meter_cost(usage);
	usage.total_operating_cost = usage.total_meter_cost + 
		usage.opex_breakdown.ess_enclosure_opex + usage.opex_breakdown.ess_pcs_opex + usage.opex_breakdown.pv_opex;
	return usage;
}


UsageData calculateScenarioUsage(const SiteData& siteData, const TaskConfig& config, const TaskData& scenario, const CostVectors& costVectors) {
	auto usage = sumUsage(siteData, scenario, costVectors);
	usage.capex_breakdown = calculate_capex_with_discounts(siteData, config, scenario);
	usage.opex_breakdown = calculate_opex(scenario);
	usage.total_meter_cost = calculate_meter_cost(usage);
	usage.total_operating_cost = usage.total_meter_cost +
		usage.opex_breakdown.ess_enclosure_opex + usage.opex_breakdown.ess_pcs_opex + usage.opex_breakdown.pv_opex;
	return usage;
}
