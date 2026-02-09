#pragma once

#include <nlohmann/json.hpp>

#include "../Definitions.hpp"

using json = nlohmann::json;

// we only define to_json because there's no need to read a result in again

// for simplicity, we're not supporting the ReportData fields
// if you need these, read from the CSV or use the Python Bindings

void to_json(json& j, const ScenarioComparison comparison);
void to_json(json& j, const SimulationMetrics metrics);

void to_json(json& j, const SimulationResult result);
