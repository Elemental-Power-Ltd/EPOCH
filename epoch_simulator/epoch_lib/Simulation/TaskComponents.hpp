#pragma once

#include <vector>
#include <bit>
#include <cstdint>
// This file contains definitions for the component types that make up a TaskData


inline void hash_combine([[maybe_unused]] std::size_t& seed) { }

template <typename T, typename... Rest>
inline void hash_combine(std::size_t& seed, const T& v, Rest... rest) {
    std::hash<T> hasher;
    seed ^= hasher(v) + 0x9e3779b9 + (seed<<6) + (seed>>2);
    hash_combine(seed, rest...);
}

struct Building {
    float scalar_heat_load = 1.0f;
    float scalar_electrical_load = 1.0f;
    size_t fabric_intervention_index = 0;
    bool incumbent = false;
    float age = 0;
    float lifetime = 25;

    bool operator==(const Building&) const = default;
};

struct DataCentreData {
    float maximum_load = 50.0f;
    float hotroom_temp = 43.0f;
    bool incumbent = false;
    float age = 0;
    float lifetime = 10;

    bool operator==(const DataCentreData&) const = default;
};

struct DomesticHotWater {
    float cylinder_volume = 100.0f;
    bool incumbent = false;
    float age = 0;
    float lifetime = 12;

    bool operator==(const DomesticHotWater&) const = default;
};

struct ElectricVehicles {
    float flexible_load_ratio = 0.5f;
    size_t small_chargers = 0;
    size_t fast_chargers = 3;
    size_t rapid_chargers = 0;
    size_t ultra_chargers = 0;
    float scalar_electrical_load = 3.0f;
    bool incumbent = false;
    float age = 0;
    float lifetime = 15;

    bool operator==(const ElectricVehicles&) const = default;
};

enum class BatteryMode {CONSUME, CONSUME_PLUS};

struct EnergyStorageSystem {
    float capacity = 20.0f;
    float charge_power = 10.0f;
    float discharge_power = 10.0f;
    BatteryMode battery_mode = BatteryMode::CONSUME;
    float initial_charge = 0.0f;
    bool incumbent = false;
    float age = 0;
    float lifetime = 15;

    bool operator==(const EnergyStorageSystem&) const = default;
};

enum class GasType { NATURAL_GAS, LIQUID_PETROLEUM_GAS };

struct GasCHData {
    // boiler output in kW
    float maximum_output = 40.0f;
    float boiler_efficiency = 0.9f;
    GasType gas_type = GasType::NATURAL_GAS;
    bool incumbent = false;
    float age = 0;
    float lifetime = 10;

    bool operator==(const GasCHData&) const = default;
};

struct GridData {
    float grid_export = 23.0;
    float grid_import = 23.0;
    float import_headroom = 0.25f;
    size_t tariff_index = 0;
    float export_tariff = 0.05f;
    bool incumbent = false;
    float age = 0;
    float lifetime = 25;

    bool operator==(const GridData&) const = default;
};

enum class HeatSource {AMBIENT_AIR, HOTROOM};

struct HeatPumpData {
    float heat_power = 20.0f;
    HeatSource heat_source = HeatSource::AMBIENT_AIR;
    float send_temp = 70.0f;
    bool incumbent = false;
    float age = 0;
    float lifetime = 10;

    bool operator==(const HeatPumpData&) const = default;
};

struct MopData {
    float maximum_load = 300.0f;
    bool incumbent = false;
    float age = 0;
    float lifetime = 10;

    bool operator==(const MopData&) const = default;
};

struct SolarData {
    float yield_scalar = 10.0;
    int yield_index = 0;
    bool incumbent = false;
    float age = 0;
    float lifetime = 25;

    bool operator==(const SolarData&) const = default;
};

struct Renewables {
    std::vector<SolarData> solar_panels = {};

    bool operator==(const Renewables&) const = default;
};

struct TaskConfig {
    float capex_limit = 2500000.0f;
    bool use_boiler_upgrade_scheme = false;
    float general_grant_funding = 0.0f;
    int npv_time_horizon = 10;
    float npv_discount_factor = 0.0f;

    bool operator==(const TaskConfig&) const = default;
};


template<>
struct std::hash<Building>
{
    std::size_t operator()(const Building& b) const noexcept
    {
        std::size_t h=0;
        hash_combine(h, b.scalar_heat_load, b.scalar_electrical_load, b.fabric_intervention_index, b.incumbent, b.age, b.lifetime); 
        return h;
    }
};

template<>
struct std::hash<DataCentreData>
{
    std::size_t operator()(const DataCentreData& d) const noexcept
    {
        std::size_t h=0;
        hash_combine(h, d.hotroom_temp, d.maximum_load, d.incumbent, d.age, d.lifetime);
        return h;
    }
};

template<>
struct std::hash<DomesticHotWater>
{
    std::size_t operator()(const DomesticHotWater& d) const noexcept
    {
        std::size_t h = 0;
        hash_combine(h, d.cylinder_volume, d.incumbent, d.age, d.lifetime);
        return h;
    }
};

template<>
struct std::hash<ElectricVehicles>
{
    std::size_t operator()(const ElectricVehicles& ev) const noexcept
    {
        std::size_t h = 0;
        hash_combine(h, ev.fast_chargers, ev.flexible_load_ratio, ev.rapid_chargers, ev.scalar_electrical_load,
        ev.small_chargers, ev.ultra_chargers, ev.incumbent, ev.age, ev.lifetime);
        return h;
    }
};

template<>
struct std::hash<EnergyStorageSystem>
{
    std::size_t operator()(const EnergyStorageSystem& ess) const noexcept
    {
        std::size_t h = 0;
        hash_combine(h, ess.battery_mode, ess.capacity, ess.charge_power, ess.initial_charge, ess.discharge_power,
        ess.incumbent, ess.age, ess.lifetime);
        return h;
    }
};

template<>
struct std::hash<GridData>
{
    std::size_t operator()(const GridData& grid) const noexcept
    {
        std::size_t h = 0;
        hash_combine(h,
            grid.grid_export, grid.grid_import, grid.import_headroom, grid.tariff_index, grid.export_tariff,
            grid.incumbent, grid.age, grid.lifetime);
        return h;
    }
};

template<>
struct std::hash<HeatPumpData>
{
    std::size_t operator()(const HeatPumpData& hpd) const noexcept
    {
        std::size_t h = 0;
        hash_combine(h,
            hpd.heat_power, hpd.heat_source, hpd.send_temp, hpd.incumbent, hpd.age, hpd.lifetime);
        return h;
    }
};

template<>
struct std::hash<MopData>
{
    std::size_t operator()(const MopData& m) const noexcept
    {
        std::size_t h = 0;
        hash_combine(h, m.maximum_load, m.incumbent, m.age, m.lifetime);
        return h;
    }
};

template<>
struct std::hash<GasCHData>
{
    std::size_t operator()(const GasCHData& gch) const noexcept
    {
        std::size_t h = 0;
        hash_combine(h,
            gch.maximum_output, gch.boiler_efficiency, gch.gas_type, gch.incumbent, gch.age, gch.lifetime);
        return h;
    }
};

template <typename T>
class vector_hasher {
    // Hash a vector, which we need for the renewables
    // Taken from https://stackoverflow.com/questions/20511347/a-good-hash-function-for-a-vector
    public:
    std::size_t operator()(std::vector<T> const& vec) const {
        std::size_t seed = vec.size();
        std::hash<T> hasher;

        for(const T& x: vec) {
            std::size_t h = hasher(x);
            seed ^= h + 0x9e3779b9 + (seed << 6) + (seed >> 2);
        }
        return seed;
    };
};

template<>
struct std::hash<SolarData>
{
    std::size_t operator()(const SolarData& sd) const noexcept
    {
        std::size_t h = 0;
        hash_combine(h, sd.yield_scalar, sd.yield_index, sd.incumbent, sd.age, sd.lifetime);
        return h;
    }
};

template<>
struct std::hash<Renewables>
{
    std::size_t operator()(const Renewables& r) const noexcept
    {
        // We've only got one component, so hash it directly.
        return vector_hasher<SolarData>{}(r.solar_panels);
    }
};
