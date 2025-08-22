// logic for serializing and deserializing TaskData to nlohmann json

#include "TaskDataJson.hpp"
#include "EnumToString.hpp"

// Building
void from_json(const json& j, Building& building) {
	j.at("scalar_heat_load").get_to(building.scalar_heat_load);
	j.at("scalar_electrical_load").get_to(building.scalar_electrical_load);
	j.at("fabric_intervention_index").get_to(building.fabric_intervention_index);
	j.at("incumbent").get_to(building.incumbent);
	j.at("age").get_to(building.age);
	j.at("lifetime").get_to(building.lifetime);

	if (j.contains("floor_area") && !j.at("floor_area").is_null()) {
		building.floor_area = j.at("floor_area").get<float>();
	}
	else {
		building.floor_area = std::nullopt;
	}
}

void to_json(json& j, const Building& building) {
	j = json{
		{"scalar_heat_load", building.scalar_heat_load},
		{"scalar_electrical_load", building.scalar_electrical_load},
		{"fabric_intervention_index", building.fabric_intervention_index},
		{"incumbent", building.incumbent},
		{"age", building.age},
		{"lifetime", building.lifetime}
	};

	if (building.floor_area.has_value()) {
		j["floor_area"] = building.floor_area.value();
	}
	else {
		j["floor_area"] = nullptr;
	}
}

// DataCentre
void from_json(const json& j, DataCentreData& dc) {
	j.at("maximum_load").get_to(dc.maximum_load);
	j.at("hotroom_temp").get_to(dc.hotroom_temp);
	j.at("incumbent").get_to(dc.incumbent);
	j.at("age").get_to(dc.age);
	j.at("lifetime").get_to(dc.lifetime);

}

void to_json(json& j, const DataCentreData& dc) {
	j = json{
		{"maximum_load", dc.maximum_load},
		{"hotroom_temp", dc.hotroom_temp},
		{"incumbent", dc.incumbent},
		{"age", dc.age},
		{"lifetime", dc.lifetime}
	};
}

// DomesticHotWater
void from_json(const json& j, DomesticHotWater& dhw) {
	j.at("cylinder_volume").get_to(dhw.cylinder_volume);
	j.at("incumbent").get_to(dhw.incumbent);
	j.at("age").get_to(dhw.age);
	j.at("lifetime").get_to(dhw.lifetime);
}

void to_json(json& j, const DomesticHotWater& dhw) {
	j = json{
		{"cylinder_volume", dhw.cylinder_volume},
		{"incumbent", dhw.incumbent},
		{"age", dhw.age},
		{"lifetime", dhw.lifetime}
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
	j.at("incumbent").get_to(ev.incumbent);
	j.at("age").get_to(ev.age);
	j.at("lifetime").get_to(ev.lifetime);
}

void to_json(json& j, const ElectricVehicles& ev) {
	j = json{
		{"flexible_load_ratio", ev.flexible_load_ratio},
		{"small_chargers", ev.small_chargers},
		{"fast_chargers", ev.fast_chargers},
		{"rapid_chargers", ev.rapid_chargers},
		{"ultra_chargers", ev.ultra_chargers},
		{"scalar_electrical_load", ev.scalar_electrical_load},
		{"incumbent", ev.incumbent},
		{"age", ev.age},
		{"lifetime", ev.lifetime}
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
	j.at("incumbent").get_to(ess.incumbent);
	j.at("age").get_to(ess.age);
	j.at("lifetime").get_to(ess.lifetime);
}

void to_json(json& j, const EnergyStorageSystem& ess) {
	j = json{
		{"capacity", ess.capacity},
		{"charge_power", ess.charge_power},
		{"discharge_power", ess.discharge_power},
		{"battery_mode", ess.battery_mode},
		{"initial_charge", ess.initial_charge},
		{"incumbent", ess.incumbent},
		{"age", ess.age},
		{"lifetime", ess.lifetime}
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
	j.at("incumbent").get_to(gas_heater.incumbent);
	j.at("age").get_to(gas_heater.age);
	j.at("lifetime").get_to(gas_heater.lifetime);
}

void to_json(json& j, const GasCHData& gas_heater) {
	j = json{
		{"maximum_output", gas_heater.maximum_output},
		{"boiler_efficiency", gas_heater.boiler_efficiency},
		{"gas_type", gas_heater.gas_type},
		{"incumbent", gas_heater.incumbent},
		{"age", gas_heater.age},
		{"lifetime", gas_heater.lifetime}
	};
}

// Grid
void from_json(const json& j, GridData& grid) {
	j.at("grid_export").get_to(grid.grid_export);
	j.at("grid_import").get_to(grid.grid_import);
	j.at("import_headroom").get_to(grid.import_headroom);
	j.at("tariff_index").get_to(grid.tariff_index);
	j.at("export_tariff").get_to(grid.export_tariff);
	j.at("incumbent").get_to(grid.incumbent);
	j.at("age").get_to(grid.age);
	j.at("lifetime").get_to(grid.lifetime);
}

void to_json(json& j, const GridData& grid) {
	j = json{
		{"grid_export", grid.grid_export},
		{"grid_import", grid.grid_import},
		{"import_headroom", grid.import_headroom},
		{"tariff_index", grid.tariff_index},
		{"export_tariff", grid.export_tariff},
		{"incumbent", grid.incumbent},
		{"age", grid.age},
		{"lifetime", grid.lifetime}
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
	j.at("incumbent").get_to(hp.incumbent);
	j.at("age").get_to(hp.age);
	j.at("lifetime").get_to(hp.lifetime);
}

void to_json(json& j, const HeatPumpData& hp) {
	j = json{
		{"heat_power", hp.heat_power},
		{"heat_source", hp.heat_source},
		{"send_temp", hp.send_temp},
		{"incumbent", hp.incumbent},
		{"age", hp.age},
		{"lifetime", hp.lifetime}
	};
}

// Mop
void from_json(const json& j, MopData& mop) {
	j.at("maximum_load").get_to(mop.maximum_load);
	j.at("incumbent").get_to(mop.incumbent);
	j.at("age").get_to(mop.age);
	j.at("lifetime").get_to(mop.lifetime);
}

void to_json(json& j, const MopData& mop) {
	j = json{
		{"maximum_load", mop.maximum_load},
		{"incumbent", mop.incumbent},
		{"age", mop.age},
		{"lifetime", mop.lifetime}
	};
}

// Solar
void from_json(const json& j, SolarData& solar) {
	j.at("yield_scalar").get_to(solar.yield_scalar);
	j.at("yield_index").get_to(solar.yield_index);
	j.at("incumbent").get_to(solar.incumbent);
	j.at("age").get_to(solar.age);
	j.at("lifetime").get_to(solar.lifetime);
}

void to_json(json& j, const SolarData& solar) {
	j = json{
		{"yield_scalar", solar.yield_scalar},
		{"yield_index", solar.yield_index},
		{"incumbent", solar.incumbent},
		{"age", solar.age},
		{"lifetime", solar.lifetime}
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

	if (j.contains("solar_panels") && !j["solar_panels"].is_null()) {
		taskData.solar_panels = j.at("solar_panels").get<std::vector<SolarData>>();
	}
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

	if (taskData.heat_pump) {
		j["heat_pump"] = taskData.heat_pump.value();
	}

	if (taskData.mop) {
		j["mop"] = taskData.mop.value();
	}

	j["solar_panels"] = taskData.solar_panels;

}