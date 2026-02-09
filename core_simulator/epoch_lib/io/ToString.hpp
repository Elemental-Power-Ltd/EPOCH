#pragma once

#include <string>
#include <format>

#include "../Definitions.hpp"
#include "../Simulation/Costs/CostData.hpp"


/**
* A collection of string representations of Epoch types
* primarily to provide __repr__ methods to the python bindings
*/

std::string resultToString(const SimulationResult& result);
std::string metricsToString(const SimulationMetrics& metrics);
std::string taskDataToString(const TaskData& taskData);

std::string buildingToString(const Building& b);
std::string dataCentreToString(const DataCentreData& dc);
std::string dhwToString(const DomesticHotWater& dhw);
std::string evToString(const ElectricVehicles& ev);
std::string essToString(const EnergyStorageSystem& ess);
std::string gasHeaterToString(const GasCHData& gh);
std::string gridToString(const GridData& grid);
std::string heatpumpToString(const HeatPumpData& hp);
std::string mopToString(const MopData& mop);
std::string solarToString(const SolarData& solar);
std::string configToString(const TaskConfig& config);

std::string capexBreakdownToString(const CapexBreakdown& breakdown);