#pragma once

#include "../TaskData.hpp"
#include "../SiteData.hpp"
#include "../../Definitions.hpp"
#include "Capex.hpp"
#include "Opex.hpp"


struct UsageData {
	float elec_cost = 0.0f;
	float elec_CO2e = 0.0f;
	float export_revenue = 0.0f;
	float export_CO2e = 0.0f;

	float fuel_cost = 0.0f;
	float fuel_CO2e = 0.0f;

	float low_priority_CO2e_avoided = 0.0f;

	float electric_vehicle_revenue = 0.0f;
	float high_priority_revenue = 0.0f;
	float low_priority_revenue = 0.0f;

	CapexBreakdown capex_breakdown;
	OpexBreakdown opex_breakdown;

};

UsageData calculateBaselineUsage(const SiteData& siteData, const TaskData& taskData, const CostVectors& costVectors);
UsageData calculateScenarioUsage(const SiteData& siteData, const TaskData& baseline, const TaskData& scenario, const CostVectors& costVectors);

