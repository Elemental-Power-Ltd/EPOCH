#pragma once

#include <Eigen/Core>
#include <vector>
#include <string>

#include "../Definitions.hpp"
#include "TaskData.hpp"


enum class SimulationType {
	FullReporting,
	ResultOnly
};


class Simulator {
public:
	Simulator();

	SimulationResult simulateScenario(const HistoricalData& historicalData, const TaskData& taskData, SimulationType simulationType = SimulationType::ResultOnly) const;

	FullSimulationResult simulateScenarioFull(const HistoricalData& historicalData, const TaskData& taskData, SimulationType simulationType) const;

	FullSimulationResult makeInvalidResult(const TaskData& taskData) const;

	year_TS calculateRGenTotal(const HistoricalData& historicalData, const TaskData& taskData) const;
};
