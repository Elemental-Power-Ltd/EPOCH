#pragma once

#include <optional>
#include <vector>

#include <nlohmann/json.hpp>

#include "TaskComponents.hpp"

struct TaskData {
	std::optional<Building> building;
	std::optional<DataCentreData> data_centre;
	std::optional<DomesticHotWater> domestic_hot_water;
	std::optional<ElectricVehicles> electric_vehicles;
	std::optional<EnergyStorageSystem> energy_storage_system;
	std::optional<GasCHData> gas_heater;
	std::optional<GridData> grid;
	std::optional<HeatPumpData> heat_pump;
	std::optional<MopData> mop;
	std::vector<SolarData> solar_panels;
	TaskConfig config;

	bool operator==(const TaskData& other) const { 
		return (
			building == other.building &&
			data_centre == other.data_centre &&
			domestic_hot_water == other.domestic_hot_water &&
			electric_vehicles == other.electric_vehicles &&
			energy_storage_system == other.energy_storage_system &&
			gas_heater == other.gas_heater &&
			grid == other.grid &&
			heat_pump == other.heat_pump &&
			mop == other.mop &&
			solar_panels == other.solar_panels);
		}
};

template<>
struct std::hash<TaskData>
{
    std::size_t operator()(const TaskData& td) const noexcept
    {
        std::size_t h = 0;
		hash_combine(
			h, 
			td.building,
			td.data_centre, 
			td.domestic_hot_water, 
			td.electric_vehicles,
			td.energy_storage_system,
			td.gas_heater,
			td.grid,
			td.heat_pump,
			td.mop,
			vector_hasher<SolarData>{}(td.solar_panels)
		);
        return h;
    }
};