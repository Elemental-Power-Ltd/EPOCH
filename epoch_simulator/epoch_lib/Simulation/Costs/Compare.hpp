#pragma once

#include "Usage.hpp"
#include "../SiteData.hpp"


struct ScenarioComparison {
	float cost_balance;
	float meter_balance;
	float operating_balance;
	float payback_horizon_years;
	float carbon_balance_scope_1;
	float carbon_balance_scope_2;
	float npv_balance;
};


ScenarioComparison compareScenarios(
	const SiteData& siteData,
	const UsageData& baselineUsage, const SimulationMetrics& baselineMetrics, 
	const UsageData& scenarioUsage, const SimulationMetrics& scenarioMetrics
);

float calculate_payback_horizon(float capex, float operating_balance);

float calculate_carbon_usage_scope_1(const UsageData& usage);

float calculate_carbon_usage_scope_2(const UsageData& usage);


// "hard wired" constants for the moment
// coefficient applied to local infrastructure CAPEX (decimal, not percentage)
const float project_plan_develop_EPC = 0.0f;  // set to zero for the moment as design and PM included in kit installation costs
// coefficient applied to grid infrastructure CAPEX (decimal, not percentage)
const float project_plan_develop_Grid = 0.1f;

// every kWh that goes into an EV saves this much on the counterfactual of an ICE petrol vehicle
const float petrol_displace_kg_CO2e = 0.9027f;

