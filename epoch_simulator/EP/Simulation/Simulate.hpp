#pragma once

#include <vector>
#include <string>

#include "../Definitions.h"


CustomDataTable simulateScenario(CustomDataTable inputdata, std::vector<std::pair<std::string, float>> paramSlice);

SimulationResult simulateScenarioAndSum(CustomDataTable inputdata, std::vector<std::pair<std::string, float>> paramSlice);

std::vector<float> getDataForKey(const CustomDataTable& table, const std::string& key);

float vec2sum(CustomDataTable table, std::string key);
float vec2first(CustomDataTable table, std::string key);
