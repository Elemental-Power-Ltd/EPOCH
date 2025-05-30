#pragma once

#include "Usage.hpp"


struct ScenarioComparison {
	float cost_balance;
	float meter_balance;
	float operating_balance;
	float payback_horizon_years;
	float total_annualised_cost;
	float carbon_balance_scope_1;
	float carbon_balance_scope_2;
};


ScenarioComparison compareScenarios(const UsageData& baselineUsage, const UsageData& scenarioUsage);

float calculate_ESS_annualised_cost(const UsageData& usage);

float calculate_PV_annualised_cost(const UsageData& usage);

float calculate_EV_CP_annualised_cost(const UsageData& usage);

float calculate_ASHP_annualised_cost(const UsageData& usage);

float calculate_DHW_annualised_cost(const UsageData& usage);

float calculate_Grid_annualised_cost(const UsageData& usage);

float calculate_Project_annualised_cost(const UsageData& usage);

float calculate_total_annualised_cost(const UsageData& usage);

float calculate_payback_horizon(float capex, float cost_balance);

float calculate_carbon_usage_scope_1(const UsageData& usage);

float calculate_carbon_usage_scope_2(const UsageData& usage);


// "hard wired" constants for the moment
// coefficient applied to local infrastructure CAPEX (decimal, not percentage)
const float project_plan_develop_EPC = 0.0f;  // set to zero for the moment as design and PM included in kit installation costs
// coefficient applied to grid infrastructure CAPEX (decimal, not percentage)
const float project_plan_develop_Grid = 0.1f;

// every kWh that goes into an EV saves this much on the counterfactual of an ICE petrol vehicle
const float petrol_displace_kg_CO2e = 0.9027f;


// plant lifetimes in years

const float ESS_lifetime = 15.0f;
const float PV_panel_lifetime = 25.0f;
const float EV_CP_lifetime = 15.0f;
const float grid_lifetime = 25.0f;
const float ASHP_lifetime = 10.0f;
const float DHW_lifetime = 12.0f;
const float project_lifetime = 10.0f;
