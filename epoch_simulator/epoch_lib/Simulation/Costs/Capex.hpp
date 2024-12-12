#pragma once

#include "CostData.hpp"
#include "../TaskData.hpp"
#include "../TaskComponents.hpp"

CapexBreakdown calculate_capex(const TaskData& taskData);


void calculate_dhw_capex(const DomesticHotWater& dhw, CapexBreakdown& capex_breakdown);

void calculate_ev_capex(const ElectricVehicles& ev, CapexBreakdown& capex_breakdown);

void calculate_ess_capex(const EnergyStorageSystem& ess, CapexBreakdown& capex_breakdown);

void calculate_grid_capex(const GridData& grid, CapexBreakdown& capex_breakdown);

void calculate_heatpump_capex(const HeatPumpData& hp, CapexBreakdown& capex_breakdown);

void calculate_renewables_capex(const Renewables& renewables, CapexBreakdown& capex_breakdown);

