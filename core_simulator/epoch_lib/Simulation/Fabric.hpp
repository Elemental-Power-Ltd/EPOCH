#pragma once

#include <optional>
#include <vector>

#include <Eigen/Core>

struct FabricCostBreakdown {
	std::string name;
	std::optional<float> area;
	float cost;
};

struct FabricIntervention {
	// the cost in pounds of this fabric intervention
	float cost;

	// breakdown of costs in £ including the areas affected by each intervention
	// if unknown, this is empty
	std::vector<FabricCostBreakdown> cost_breakdown;

	// the peak heating demand in kW (as calculated by an external source such as PHPP)
	float peak_hload;

	// The (reduced) heating demand in kWh/timestep
	Eigen::VectorXf reduced_hload;
};
