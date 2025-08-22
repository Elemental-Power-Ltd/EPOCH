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
	// (note that opex is a part of the total_annualised_cost along with the annualised_capex)
	comparison.cost_balance = comparison.meter_balance + baselineMetrics.total_annualised_cost - scenarioMetrics.total_annualised_cost;

	comparison.payback_horizon_years = calculate_payback_horizon(scenarioUsage.capex_breakdown.total_capex, comparison.operating_balance);

	comparison.carbon_balance_scope_1 = baselineUsage.carbon_scope_1_kg_CO2e - scenarioUsage.carbon_scope_1_kg_CO2e;
	comparison.carbon_balance_scope_2 = baselineUsage.carbon_scope_2_kg_CO2e - scenarioUsage.carbon_scope_2_kg_CO2e;
	comparison.combined_carbon_balance = comparison.carbon_balance_scope_1 + comparison.carbon_balance_scope_2;

	comparison.carbon_cost = calculate_carbon_cost(scenarioMetrics.total_capex, comparison.carbon_balance_scope_1);

	return comparison;
}


/**
* Calculate the payback hoizon of a scenario.
*
* This is the capex divided by the yearly operating balance.
* This does not include the annualised cost of the components.
*
* Note: we deliberately allow for negative payback horizons.
* These should be considered invalid (as the scenario will never pay back)
* but is useful to provide gradient information for optimisation.
*/
float calculate_payback_horizon(float capex, float operating_balance) {
	if (capex <= 0) {
		// if we haven't spend any money then the payback horizon is 0
		return 0.0f;
	}
	else if (operating_balance == 0.0f) {
		// return the smallest possible negative number
		return -1.0f / std::numeric_limits<float>::max();
	}
	else {
		return capex / operating_balance;
	}
};


/**
*   Calculates the salix carbon cost of a scenario.
*   It is the total CAPEX of a scenario divided by its scope 1 carbon emission savings in tonnes.
*   The carbon emissions need to be adjusted by multiplying each assets savings by its lifetime years.
*   The lifetime years of each asset and the carbon cost equation can be found:
*   https://www.salixfinance.co.uk/sites/default/files/2024-10/Guidance%20Notes%20%282%29.pdf.
*   Since, only heat pumps currently affect the carbon emissions, the ASSET_LIFETIME_YEARS is set to 20.
*   Returns largest float32 if CAPEX is non null and carbon_balance_scope_1 is null or negative.
*   Returns 0 if CAPEX is null.
*/
float calculate_carbon_cost(float capex, float carbon_balance_scope_1) {
	if (capex > 0 && carbon_balance_scope_1 > 0) {
		const float ASSET_LIFETIME_YEARS = 20.0f;
		return capex / (carbon_balance_scope_1 * ASSET_LIFETIME_YEARS / 1000.0f);
	}

	if (capex > 0 and carbon_balance_scope_1 <= 0) {
		return std::numeric_limits<float>::max();
	}

	return 0;

}