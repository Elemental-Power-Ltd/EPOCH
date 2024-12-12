#pragma once

#include <string>

#include <pybind11/pybind11.h>

#include "../epoch_lib/Definitions.hpp"
#include "../epoch_lib/Simulation/Costs/CostData.hpp"

// define toString methods for the structs that we expose to Python
std::string resultToString(const SimulationResult& result);
std::string taskDataToString(const TaskData& taskData);

std::string buildingToString(const Building& b);
std::string dataCentreToString(const DataCentreData& dc);
std::string dhwToString(const DomesticHotWater& dhw);
std::string evToString(const ElectricVehicles& ev);
std::string essToString(const EnergyStorageSystem& ess);
std::string gridToString(const GridData& grid);
std::string heatpumpToString(const HeatPumpData& hp);
std::string mopToString(const MopData& mop);
std::string renewablesToString(const Renewables& renewables);
std::string configToString(const TaskConfig& config);

std::string capexBreakdownToString(const CapexBreakdown& breakdown);
