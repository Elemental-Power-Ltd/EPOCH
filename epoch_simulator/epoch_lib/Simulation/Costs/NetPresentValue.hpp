#pragma once

#include <vector>

#include "../TaskData.hpp"
#include "Usage.hpp"


/**
* A generalised component to extract the necessary fields for NPV calculation
*/
struct ComponentView {
	float capex;
	float age;
	float lifetime;
	bool incumbent;
};

template<typename T>
ComponentView make_component(const T& comp, float capex) {
	return ComponentView{ capex, comp.age, comp.lifetime, comp.incumbent };
}


struct ValueMetrics {
	float annualised_cost = 0;
	float net_present_value = 0;
};


ValueMetrics calculate_npv(const SiteData& siteData, const TaskConfig& config, const TaskData& scenario, const UsageData& usage);