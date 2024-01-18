#pragma once

#include <vector>
#include <string>

#include "../Definitions.h"


FullSimulationResult simulateScenario(const HistoricalData& historicalData, std::vector<std::pair<std::string, float>> paramSlice);

SimulationResult simulateScenarioAndSum(const HistoricalData& historicalData, std::vector<std::pair<std::string, float>> paramSlice);

float sumVector(const std::vector<float>& v);
