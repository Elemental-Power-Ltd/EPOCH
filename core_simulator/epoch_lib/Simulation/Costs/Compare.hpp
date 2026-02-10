#pragma once

#include <optional>

#include "Usage.hpp"
#include "../SiteData.hpp"



ScenarioComparison compareScenarios(
	const SiteData& siteData,
	const UsageData& baselineUsage, const SimulationMetrics& baselineMetrics, 
	const UsageData& scenarioUsage, const SimulationMetrics& scenarioMetrics
);

float calculate_carbon_cost(float capex, float carbon_balance_scope_1);
float calculate_payback_horizon(float capex, float operating_balance);
std::optional<float> calculate_return_on_investment(float capex, float operating_balance);
