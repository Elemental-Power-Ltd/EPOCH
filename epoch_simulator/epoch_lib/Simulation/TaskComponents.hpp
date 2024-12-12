#pragma once

#include <vector>

// This file contains definitions for the component types that make up a TaskData

struct Building {
	float scalar_heat_load = 1.0f;
	float scalar_electrical_load = 1.0f;
	size_t fabric_intervention_index = 0;
};

struct DataCentreData {
	float maximum_load = 50.0f;
	float hotroom_temp = 43.0f;
};

struct DomesticHotWater {
	float cylinder_volume = 2500.0f;
};

struct ElectricVehicles {
	float flexible_load_ratio = 0.5f;
	size_t small_chargers = 0;
	size_t fast_chargers = 3;
	size_t rapid_chargers = 0;
	size_t ultra_chargers = 0;
	float scalar_electrical_load = 3.0f;
};

enum class BatteryMode { CONSUME };

struct EnergyStorageSystem {
	float capacity = 800.0f;
	float charge_power = 300.0f;
	float discharge_power = 300.0f;
	BatteryMode battery_mode = BatteryMode::CONSUME;
	float initial_charge = 0.0f;
};


struct GridData {
	float export_headroom = 0.0f;
	float grid_export = 100.0f;
	float grid_import = 140.0f;
	float import_headroom = 0.4f;
	float min_power_factor = 0.95f;
	size_t tariff_index = 0;
};

enum class HeatSource {AMBIENT_AIR, HOTROOM};

struct HeatPumpData {
	float heat_power = 70.0f;
	HeatSource heat_source = HeatSource::AMBIENT_AIR;
	float send_temp = 70.0f;
};

struct MopData {
	float maximum_load = 300.0f;
};

struct Renewables {
	std::vector<float> yield_scalars = {};
};

struct TaskConfig {
	float capex_limit = 2500000.0f;
};




