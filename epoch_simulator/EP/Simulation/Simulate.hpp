#pragma once

#include <vector>
#include <string>

#include "../Definitions.h"
#include "Config.h"


FullSimulationResult simulateScenario(const HistoricalData& historicalData, const Config& config);

SimulationResult simulateScenarioAndSum(const HistoricalData& historicalData, const Config& config);

float sumVector(const std::vector<float>& v);
