#pragma once

#include "CostData.hpp"
#include "../SiteData.hpp"
#include "../TaskData.hpp"
#include "../TaskComponents.hpp"
#include "../TaskConfig.hpp"

CapexBreakdown calculate_capex_with_discounts(const SiteData& siteData, const TaskConfig& config, const TaskData& scenario);

CapexBreakdown calculate_capex(const SiteData& siteData, const TaskData& taskData, const CapexModel& model);

// note: these functions are named calculate_X_cost
// this is to denote that they are not responsible for checking whether the component is incumbent
// this check is made in calculate_capex

float calculate_fabric_cost(const SiteData& siteData, const Building& building);

float calculate_dhw_cost(const DomesticHotWater& dhw, const CapexModel& model);

EVCapex calculate_ev_cost(const ElectricVehicles& ev, const CapexModel& model);

ESSCapex calculate_ess_cost(const EnergyStorageSystem& ess, const CapexModel& model);

float calculate_gas_heater_cost(const GasCHData& gas, const CapexModel& model);

float calculate_grid_cost(const GridData& grid, const CapexModel& model);

float calculate_heatpump_cost(const HeatPumpData& hp, const CapexModel& model);

SolarCapex calculate_solar_cost(const SolarData& panel, const CapexModel& model);

bool is_elegible_for_boiler_upgrade_scheme(const TaskData& baseline, const TaskData& scenario);
