#pragma once

#include <Eigen/Core>
#include <vector>
#include <string>

#include "../Definitions.hpp"
#include "TaskData.hpp"
#include "SiteData.hpp"
#include "TempSum.hpp"


enum class SimulationType {
	FullReporting,
	ResultOnly
};


class Simulator {
public:
	Simulator();

	SimulationResult simulateScenario(const SiteData& siteData, const TaskData& taskData, SimulationType simulationType = SimulationType::ResultOnly) const;

	/**
	* Perform validation that the data in the SiteData and TaskData are aligned
	* Raise an exception if they are not compatible
	*/
	void validateScenario(const SiteData& siteData, const TaskData& taskData) const;

private:

	SimulationResult makeInvalidResult(const TaskData& taskData) const;

	float getFixedAvailableImport(const SiteData& siteData, const TaskData& taskData) const;
};
