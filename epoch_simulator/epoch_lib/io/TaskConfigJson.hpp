#pragma once

#include <nlohmann/json.hpp>

#include "../Simulation/TaskConfig.hpp"

using json = nlohmann::json;

// Config
void from_json(const json& j, TaskConfig& config);
void to_json(json& j, const TaskConfig& config);