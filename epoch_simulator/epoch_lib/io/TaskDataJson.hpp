#pragma once
// logic for serializing and deserializing TaskData to nlohmann json

#include <nlohmann/json.hpp>

#include "../Simulation/TaskComponents.hpp"
#include "../Simulation/TaskData.hpp"

using json = nlohmann::json;

// Building
void from_json(const json& j, Building& building);
void to_json(json& j, const Building& building);

// DataCentre
void from_json(const json& j, DataCentreData& dc);
void to_json(json& j, const DataCentreData& dc);

// DomesticHotWater
void from_json(const json& j, DomesticHotWater& dhw);
void to_json(json& j, const DomesticHotWater& dhw);

//ElectricVehicles
void from_json(const json& j, ElectricVehicles& ev);
void to_json(json& j, const ElectricVehicles& ev);

// BatteryMode
void from_json(const json& j, BatteryMode& mode);
void to_json(json& j, const BatteryMode& mode);

// EnergyStorageSystem
void from_json(const json& j, EnergyStorageSystem& ess);
void to_json(json& j, const EnergyStorageSystem& ess);

// Grid
void from_json(const json& j, GridData& grid);
void to_json(json& j, const GridData& grid);

// HeatSource
void from_json(const json& j, HeatSource& source);
void to_json(json& j, const HeatSource& source);

// HeatPump
void from_json(const json& j, HeatPumpData& hp);
void to_json(json& j, const HeatPumpData& hp);

// Mop
void from_json(const json& j, MopData& mop);
void to_json(json& j, const MopData& mop);

// Renewables
void from_json(const json& j, Renewables& renewables);
void to_json(json& j, const Renewables& renewables);

// Config
void from_json(const json& j, TaskConfig& config);
void to_json(json& j, const TaskConfig& config);

// TaskData
void from_json(const json& j, TaskData& taskData);
void to_json(json& j, const TaskData& taskData);