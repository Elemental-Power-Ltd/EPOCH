#pragma once

#include <Eigen/Core>
#include <vector>
#include <string>

#include "../Definitions.hpp"
#include "TaskData.hpp"
#include "SiteData.hpp"
#include "TempSum.hpp"
#include "Costs/Capex.hpp"
#include "Costs/Usage.hpp"


enum class SimulationType {
	FullReporting,
	ResultOnly
};


class Simulator {
public:
	explicit Simulator(SiteData siteData);

	SimulationResult simulateScenario(const TaskData& taskData, SimulationType simulationType = SimulationType::ResultOnly) const;

	/**
	* Perform validation that the data in the SiteData and TaskData are aligned
	* Raise an exception if they are not compatible
	*/
	void validateScenario(const TaskData& taskData) const;

	/**
	* Calculate the Capital Expenditure (upfront costs) for a given site
	* returns an object containing the total cost and a breakdown per component
	*/
	CapexBreakdown calculateCapexWithDiscounts(const TaskData& taskData) const;

private:
	ReportData simulateTimesteps(const TaskData& taskData, SimulationType simulationType = SimulationType::ResultOnly) const;

	SimulationResult makeInvalidResult(const TaskData& taskData) const;

	CostVectors extractCostVectors(const ReportData& reportData, const TaskData& taskData) const;

	SimulationMetrics calculateMetrics(const SiteData& siteData, const TaskData& taskData, const ReportData& reportData, const UsageData& usage) const;

	float getFixedAvailableImport(const TaskData& taskData) const;

	const SiteData mSiteData;
	TaskData mBaselineTaskData;
	UsageData mBaselineUsage;
	SimulationMetrics mBaselineMetrics;

};
