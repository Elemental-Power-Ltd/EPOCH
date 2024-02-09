#pragma once

#include <Eigen/Core>
#include <vector>
#include <string>

#include "../Definitions.h"
#include "Config.h"


class Simulator {
public:
	Simulator();

	FullSimulationResult simulateScenario(const HistoricalData& historicalData, const Config& config) const;

	SimulationResult simulateScenarioAndSum(const HistoricalData& historicalData, const Config& config, bool computeAllSums = false) const;

	year_TS calculateRGenTotal(const HistoricalData& historicalData, const Config& config) const;
};
