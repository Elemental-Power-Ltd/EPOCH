#pragma once

#include <nlohmann/json.hpp>
#include "../Simulation/Costs/CostData.hpp"

void from_json(const nlohmann::json& j, PiecewiseCostModel& model);
void to_json(nlohmann::json& j, const PiecewiseCostModel& model);

void from_json(const nlohmann::json& j, CapexModel& model);
void to_json(nlohmann::json& j, const CapexModel& model);

void from_json(const nlohmann::json& j, OpexModel& model);
void to_json(nlohmann::json& j, const OpexModel& model);
