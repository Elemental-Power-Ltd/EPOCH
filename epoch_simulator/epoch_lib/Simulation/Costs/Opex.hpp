#pragma once

#include "CostData.hpp"
#include "../TaskData.hpp"
#include "../TaskComponents.hpp"

OpexBreakdown calculate_opex(const TaskData& taskData);

void calculate_ess_opex(const EnergyStorageSystem& ess, OpexBreakdown& opex_breakdown);

void calculate_pv_opex(const std::vector<SolarData>& panels, OpexBreakdown& opex_breakdown);
