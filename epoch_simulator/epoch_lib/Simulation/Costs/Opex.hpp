#pragma once

#include "CostData.hpp"
#include "../TaskData.hpp"
#include "../TaskComponents.hpp"

OpexBreakdown calculate_opex(const TaskData& taskData, const OpexModel& opex_model);
