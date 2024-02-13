#pragma once

#include <Eigen/Core>
#include <vector>
#include <string>

#include "../Definitions.h"
#include "Config.h"


enum class SimulationType {
	FullReporting,
	ResultOnly
};


class Simulator {
public:
	Simulator();

	SimulationResult simulateScenario(const HistoricalData& historicalData, const Config& config, SimulationType simulationType = SimulationType::ResultOnly) const;

	FullSimulationResult simulateScenarioFull(const HistoricalData& historicalData, const Config& config, SimulationType simulationType) const;

	year_TS calculateRGenTotal(const HistoricalData& historicalData, const Config& config) const;
};
