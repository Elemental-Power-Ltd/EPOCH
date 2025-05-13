#include "Usage.hpp"


/**
* internal method to sum up the usage data for both baseline and scenario data
*/
UsageData sumUsage(const SiteData& siteData, const TaskData& taskData, const CostVectors& costVectors) {
	UsageData usage{};

	// TODO - extract these somewhere else (make this a class or put make these globals?)
	const float mains_gas_price = 0.068f; // £/kWh  
	const float LPG_cost_price = 0.122f; // £/kWh
	const float mains_gas_kg_C02e = 0.201f; // kg/kWh(w2h) 
	const float LPG_kg_C02e = 0.239f; // kg/kWh (well2heat)
	const float boiler_efficiency = 0.9f;

	const float EV_low_price = 0.45f; // £/kWh site price for destination EV charging, 22 kW and below
	const float EV_high_price = 0.79f; //£/kWh site price for high power EV charging, 50 KW and above
	const float high_priority_price = 0.50f; // £/kWh site price for data centre compute (hi priority load)
	const float low_priority_price = mains_gas_price; // assume this is just the equivalent lowest cost fossil fuel derived heat

	// supress unused warnings
	(void)low_priority_price;
	(void)EV_high_price;

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
		float gas_price = taskData.gas_heater->gas_type == GasType::NATURAL_GAS ? mains_gas_price : LPG_cost_price;
		float CO2e = taskData.gas_heater->gas_type == GasType::NATURAL_GAS ? mains_gas_kg_C02e : LPG_kg_C02e;

		usage.fuel_cost = costVectors.gas_import_h.sum() * gas_price;
		usage.fuel_kg_CO2e = costVectors.gas_import_h.sum() * CO2e;
	}

	if (taskData.mop) {
		// assume the counterfactual of LP heat is gas based heat emissions
		usage.low_priority_kg_CO2e_avoided = costVectors.actual_low_priority_load_e.sum() * mains_gas_kg_C02e;
		usage.low_priority_revenue = costVectors.actual_low_priority_load_e.sum() * mains_gas_price / boiler_efficiency;
	}

	if (taskData.data_centre) {
		usage.high_priority_revenue = costVectors.actual_data_centre_load_e.sum() * high_priority_price;
	}

	if (taskData.electric_vehicles) {
		// will need to separate out EV charge tariffs later, assume all destination charging for now
		usage.electric_vehicle_revenue = costVectors.actual_ev_load_e.sum() * EV_low_price;
	}

	return usage;
}


UsageData calculateBaselineUsage(const SiteData& siteData, const TaskData& taskData, const CostVectors& costVectors) {
	auto usage = sumUsage(siteData, taskData, costVectors);
	usage.capex_breakdown = calculate_capex(siteData, taskData);
	usage.opex_breakdown = calculate_opex(taskData);
	return usage;
}


UsageData calculateScenarioUsage(const SiteData& siteData, const TaskData& baseline, const TaskData& scenario, const CostVectors& costVectors) {
	auto usage = sumUsage(siteData, scenario, costVectors);
	usage.capex_breakdown = calculate_capex_with_discounts(siteData, baseline, scenario);
	usage.opex_breakdown = calculate_opex(scenario);
	return usage;
}
