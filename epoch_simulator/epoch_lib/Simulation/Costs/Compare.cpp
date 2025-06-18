#include "Compare.hpp"

#include <limits> 
#include <Eigen/Core>

#include "NetPresentValue.hpp"


ScenarioComparison compareScenarios(
	const SiteData& siteData,
	const UsageData& baselineUsage, const SimulationMetrics& baselineMetrics, 
	const UsageData& scenarioUsage, const SimulationMetrics& scenarioMetrics
) {
	ScenarioComparison comparison{};

	comparison.npv_balance = scenarioMetrics.total_net_present_value - baselineMetrics.total_net_present_value;

	float baseline_opex = baselineUsage.opex_breakdown.ess_enclosure_opex
		+ baselineUsage.opex_breakdown.ess_pcs_opex
		+ baselineUsage.opex_breakdown.pv_opex;

	float scenario_opex = scenarioUsage.opex_breakdown.ess_enclosure_opex
		+ scenarioUsage.opex_breakdown.ess_pcs_opex
		+ scenarioUsage.opex_breakdown.pv_opex;

	// meter balance is the difference between the baseline & scenario imports and exports
	comparison.meter_balance = baselineUsage.total_meter_cost - scenarioUsage.total_meter_cost;
	// operating balance then include the OPEX difference
	comparison.operating_balance = comparison.meter_balance + baseline_opex - scenario_opex;
	// finally, cost balance also includes the annualised cost of the components
	comparison.cost_balance = comparison.operating_balance + baselineMetrics.total_annualised_cost - scenarioMetrics.total_annualised_cost;

	comparison.payback_horizon_years = calculate_payback_horizon(scenarioUsage.capex_breakdown.total_capex, comparison.cost_balance);

	float baseline_carbon_scope_1 = calculate_carbon_usage_scope_1(baselineUsage);
	float scenario_carbon_scope_1 = calculate_carbon_usage_scope_1(scenarioUsage);

	float baseline_carbon_scope_2 = calculate_carbon_usage_scope_2(baselineUsage);
	float scenario_carbon_scope_2 = calculate_carbon_usage_scope_2(scenarioUsage);

	comparison.carbon_balance_scope_1 = baseline_carbon_scope_1 - scenario_carbon_scope_1;
	comparison.carbon_balance_scope_2 = baseline_carbon_scope_2 - scenario_carbon_scope_2;

	return comparison;
}


/**
* Calculate the payback hoizon of a scenario.
*
* This is the capex divided by the yearly cost balance.
*
* Note: we deliberately allow for negative payback horizons.
* These should be considered invalid (as the scenario will never pay back)
* but is useful to provide gradient information for optimisation.
*/
float calculate_payback_horizon(float capex, float cost_balance) {
	if (capex <= 0) {
		// if we haven't spend any money then the payback horizon is 0
		return 0.0f;
	}
	else if (cost_balance == 0.0f) {
		// return the smallest possible negative number
		return -1.0f / std::numeric_limits<float>::max();
	}
	else {
		return capex / cost_balance;
	}
};

float calculate_carbon_usage_scope_1(const UsageData& usage) {
	return usage.fuel_kg_CO2e - usage.low_priority_kg_CO2e_avoided;
}

float calculate_carbon_usage_scope_2(const UsageData& usage) {
	// export_kg_CO2e <= 0
	// it is the CO2 'saved' by exporting 100% green electricity to the grid
	return usage.elec_kg_CO2e + usage.export_kg_CO2e;
}
