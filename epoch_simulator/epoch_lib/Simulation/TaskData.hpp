#pragma once

#include <optional>
#include <nlohmann/json.hpp>

#include "TaskComponents.hpp"

struct TaskData {
	std::optional<Building> building;
	std::optional<DataCentreData> data_centre;
	std::optional<DomesticHotWater> domestic_hot_water;
	std::optional<ElectricVehicles> electric_vehicles;
	std::optional<EnergyStorageSystem> energy_storage_system;
	std::optional<GridData> grid;
	std::optional<HeatPumpData> heat_pump;
	std::optional<MopData> mop;
	std::optional<Renewables> renewables;
	TaskConfig config;
};

