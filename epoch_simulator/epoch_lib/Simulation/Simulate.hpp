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

	SimulationResult makeInvalidResult(const TaskData& taskData) const;

};
