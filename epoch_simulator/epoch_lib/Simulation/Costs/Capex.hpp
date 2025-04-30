#pragma once

#include "CostData.hpp"
#include "../SiteData.hpp"
#include "../TaskData.hpp"
#include "../TaskComponents.hpp"

CapexBreakdown calculate_capex_with_discounts(const SiteData& siteData, const TaskData& baseline, const TaskData& scenario);

CapexBreakdown calculate_capex(const SiteData& siteData, const TaskData& taskData);

void calculate_building_capex(const SiteData& siteData, const Building& building, CapexBreakdown& capex_breakdown);

void calculate_dhw_capex(const DomesticHotWater& dhw, CapexBreakdown& capex_breakdown);

void calculate_ev_capex(const ElectricVehicles& ev, CapexBreakdown& capex_breakdown);

void calculate_ess_capex(const EnergyStorageSystem& ess, CapexBreakdown& capex_breakdown);

void calculate_grid_capex(const GridData& grid, CapexBreakdown& capex_breakdown);

void calculate_heatpump_capex(const HeatPumpData& hp, CapexBreakdown& capex_breakdown);

void calculate_renewables_capex(const Renewables& renewables, CapexBreakdown& capex_breakdown);

bool is_elegible_for_boiler_upgrade_scheme(const TaskData& baseline, const TaskData& scenario);
