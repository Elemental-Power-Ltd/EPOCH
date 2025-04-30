// logic for serializing and deserializing TaskData to nlohmann json

#include "TaskDataJson.hpp"
#include "EnumToString.hpp"

// Building
void from_json(const json& j, Building& building) {
	j.at("scalar_heat_load").get_to(building.scalar_heat_load);
	j.at("scalar_electrical_load").get_to(building.scalar_electrical_load);
	j.at("fabric_intervention_index").get_to(building.fabric_intervention_index);
}

void to_json(json& j, const Building& building) {
	j = json{
		{"scalar_heat_load", building.scalar_heat_load},
		{"scalar_electrical_load", building.scalar_electrical_load},
		{"fabric_intervention_index", building.fabric_intervention_index}
	};
}

// DataCentre
void from_json(const json& j, DataCentreData& dc) {
	j.at("maximum_load").get_to(dc.maximum_load);
	j.at("hotroom_temp").get_to(dc.hotroom_temp);
}

void to_json(json& j, const DataCentreData& dc) {
	j = json{
		{"maximum_load", dc.maximum_load},
		{"hotroom_temp", dc.hotroom_temp}
	};
}

// DomesticHotWater
void from_json(const json& j, DomesticHotWater& dhw) {
	j.at("cylinder_volume").get_to(dhw.cylinder_volume);
}

void to_json(json& j, const DomesticHotWater& dhw) {
	j = json{
		{"cylinder_volume", dhw.cylinder_volume}
	};
}


//ElectricVehicles
void from_json(const json& j, ElectricVehicles& ev) {
	j.at("flexible_load_ratio").get_to(ev.flexible_load_ratio);
	j.at("small_chargers").get_to(ev.small_chargers);
	j.at("fast_chargers").get_to(ev.fast_chargers);
	j.at("rapid_chargers").get_to(ev.rapid_chargers);
	j.at("ultra_chargers").get_to(ev.ultra_chargers);
	j.at("scalar_electrical_load").get_to(ev.scalar_electrical_load);
}

void to_json(json& j, const ElectricVehicles& ev) {
	j = json{
		{"flexible_load_ratio", ev.flexible_load_ratio},
		{"small_chargers", ev.small_chargers},
		{"fast_chargers", ev.fast_chargers},
		{"rapid_chargers", ev.rapid_chargers},
		{"ultra_chargers", ev.ultra_chargers},
		{"scalar_electrical_load", ev.scalar_electrical_load}
	};
}

// BatteryMode
void from_json(const json& j, BatteryMode& mode) {
	std::string str = j.get<std::string>();
	if (str == "CONSUME") {
		mode = BatteryMode::CONSUME;
	}
	else if (str == "CONSUME_PLUS") {
		mode = BatteryMode::CONSUME_PLUS;
	}
	else {
		throw std::invalid_argument("Invalid Battery Mode - " + str);
	}
}

void to_json(json& j, const BatteryMode& mode) {
	j = enumToString(mode);
}


// EnergyStorageSystem
void from_json(const json& j, EnergyStorageSystem& ess) {
	j.at("capacity").get_to(ess.capacity);
	j.at("charge_power").get_to(ess.charge_power);
	j.at("discharge_power").get_to(ess.discharge_power);
	j.at("battery_mode").get_to(ess.battery_mode);
	j.at("initial_charge").get_to(ess.initial_charge);
}

void to_json(json& j, const EnergyStorageSystem& ess) {
	j = json{
		{"capacity", ess.capacity},
		{"charge_power", ess.charge_power},
		{"discharge_power", ess.discharge_power},
		{"battery_mode", ess.battery_mode},
		{"initial_charge", ess.initial_charge}
	};
}

// Gas Type
void from_json(const json& j, GasType& gas_type) {
	std::string str = j.get<std::string>();
	if (str == "NATURAL_GAS") {
		gas_type = GasType::NATURAL_GAS;
	}
	else if (str == "LIQUID_PETROLEUM_GAS") {
		gas_type = GasType::LIQUID_PETROLEUM_GAS;
	}
	else {
		throw std::invalid_argument("Invalid Gas Type - " + str);
	}
}

void to_json(json& j, const GasType& gas_type) {
	j = enumToString(gas_type);
}

// Gas Heater
void from_json(const json& j, GasCHData& gas_heater) {
	j.at("maximum_output").get_to(gas_heater.maximum_output);
	j.at("boiler_efficiency").get_to(gas_heater.boiler_efficiency);
	j.at("gas_type").get_to(gas_heater.gas_type);
}

void to_json(json& j, const GasCHData& gas_heater) {
	j = json{
		{"maximum_output", gas_heater.maximum_output},
		{"boiler_efficiency", gas_heater.boiler_efficiency},
		{"gas_type", gas_heater.gas_type}
	};
}

// Grid
void from_json(const json& j, GridData& grid) {
	j.at("grid_export").get_to(grid.grid_export);
	j.at("grid_import").get_to(grid.grid_import);
	j.at("import_headroom").get_to(grid.import_headroom);
	j.at("tariff_index").get_to(grid.tariff_index);
	j.at("export_tariff").get_to(grid.export_tariff);
}

void to_json(json& j, const GridData& grid) {
	j = json{
		{"grid_export", grid.grid_export},
		{"grid_import", grid.grid_import},
		{"import_headroom", grid.import_headroom},
		{"tariff_index", grid.tariff_index},
		{"export_tariff", grid.export_tariff}
	};
}

// HeatSource
void from_json(const json& j, HeatSource& source) {
	std::string str = j.get<std::string>();
	if (str == "AMBIENT_AIR") {
		source = HeatSource::AMBIENT_AIR;
	}
	else if (str == "HOTROOM") {
		source = HeatSource::HOTROOM;
	}
	else {
		throw std::invalid_argument("Invalid Heat Source - " + str);
	}
}

void to_json(json& j, const HeatSource& source) {
	j = enumToString(source);
}


// HeatPump
void from_json(const json& j, HeatPumpData& hp) {
	j.at("heat_power").get_to(hp.heat_power);
	j.at("heat_source").get_to(hp.heat_source);
	j.at("send_temp").get_to(hp.send_temp);
}

void to_json(json& j, const HeatPumpData& hp) {
	j = json{
		{"heat_power", hp.heat_power},
		{"heat_source", hp.heat_source},
		{"send_temp", hp.send_temp}
	};
}

// Mop
void from_json(const json& j, MopData& mop) {
	j.at("maximum_load").get_to(mop.maximum_load);
}

void to_json(json& j, const MopData& mop) {
	j = json{
		{"maximum_load", mop.maximum_load}
	};
}

// Renewables
void from_json(const json& j, Renewables& renewables) {
	j.at("yield_scalars").get_to(renewables.yield_scalars);
}

void to_json(json& j, const Renewables& renewables) {
	j = json{
		{"yield_scalars", renewables.yield_scalars}
	};
}

// Config
void from_json(const json& j, TaskConfig& config) {
	j.at("capex_limit").get_to(config.capex_limit);
	j.at("use_boiler_upgrade_scheme").get_to(config.use_boiler_upgrade_scheme);
	j.at("general_grant_funding").get_to(config.general_grant_funding);
}

void to_json(json& j, const TaskConfig& config) {
	j = json{
		{"capex_limit", config.capex_limit},
		{"use_boiler_upgrade_scheme", config.use_boiler_upgrade_scheme},
		{"general_grant_funding", config.general_grant_funding}
	};
}


// TaskData
void from_json(const json& j, TaskData& taskData) {
	if (j.contains("building") && !j["building"].is_null()) {
		taskData.building = j.at("building").get<Building>();
	}

	if (j.contains("data_centre") && !j["data_centre"].is_null()) {
		taskData.data_centre = j.at("data_centre").get<DataCentreData>();
	}

	if (j.contains("domestic_hot_water") && !j["domestic_hot_water"].is_null()) {
		taskData.domestic_hot_water = j.at("domestic_hot_water").get<DomesticHotWater>();
	}

	if (j.contains("electric_vehicles") && !j["electric_vehicles"].is_null()) {
		taskData.electric_vehicles = j.at("electric_vehicles").get<ElectricVehicles>();
	}

	if (j.contains("energy_storage_system") && !j["energy_storage_system"].is_null()) {
		taskData.energy_storage_system = j.at("energy_storage_system").get<EnergyStorageSystem>();
	}

	if (j.contains("gas_heater") && !j["gas_heater"].is_null()) {
		taskData.gas_heater = j.at("gas_heater").get<GasCHData>();
	}

	if (j.contains("grid") && !j["grid"].is_null()) {
		taskData.grid = j.at("grid").get<GridData>();
	}

	if (j.contains("heat_pump") && !j["heat_pump"].is_null()) {
		taskData.heat_pump = j.at("heat_pump").get<HeatPumpData>();
	}

	if (j.contains("mop") && !j["mop"].is_null()) {
		taskData.mop = j.at("mop").get<MopData>();
	}

	if (j.contains("renewables") && !j["renewables"].is_null()) {
		taskData.renewables = j.at("renewables").get<Renewables>();
	}

	taskData.config = j.at("config").get<TaskConfig>();

};

void to_json(json& j, const TaskData& taskData) {
	if (taskData.building) {
		j["building"] = taskData.building.value();
	}

	if (taskData.data_centre) {
		j["data_centre"] = taskData.data_centre.value();
	}

	if (taskData.domestic_hot_water) {
		j["domestic_hot_water"] = taskData.domestic_hot_water.value();
	}

	if (taskData.electric_vehicles) {
		j["electric_vehicles"] = taskData.electric_vehicles.value();
	}

	if (taskData.energy_storage_system) {
		j["energy_storage_system"] = taskData.energy_storage_system.value();
	}

	if (taskData.gas_heater) {
		j["gas_heater"] = taskData.gas_heater.value();
	}

	if (taskData.grid) {
		j["grid"] = taskData.grid.value();
	}

	if (taskData.mop) {
		j["mop"] = taskData.mop.value();
	}

	if (taskData.renewables) {
		j["renewables"] = taskData.renewables.value();
	}


	if (taskData.building) {
		j["building"] = taskData.building.value();
	}

	j["config"] = taskData.config;

}