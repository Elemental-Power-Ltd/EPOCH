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

    bool operator==(const Building&) const = default;
};

struct DataCentreData {
    float maximum_load = 50.0f;
    float hotroom_temp = 43.0f;

    bool operator==(const DataCentreData&) const = default;
};

struct DomesticHotWater {
    float cylinder_volume = 2500.0f;
    bool operator==(const DomesticHotWater&) const = default;
};

struct ElectricVehicles {
    float flexible_load_ratio = 0.5f;
    size_t small_chargers = 0;
    size_t fast_chargers = 3;
    size_t rapid_chargers = 0;
    size_t ultra_chargers = 0;
    float scalar_electrical_load = 3.0f;

    bool operator==(const ElectricVehicles&) const = default;
};

enum class BatteryMode {CONSUME, CONSUME_PLUS};

struct EnergyStorageSystem {
    float capacity = 800.0f;
    float charge_power = 300.0f;
    float discharge_power = 300.0f;
    BatteryMode battery_mode = BatteryMode::CONSUME;
    float initial_charge = 0.0f;

    bool operator==(const EnergyStorageSystem&) const = default;
};


struct GridData {
    float grid_export = 100.0f;
    float grid_import = 140.0f;
    float import_headroom = 0.4f;
    size_t tariff_index = 0;

    bool operator==(const GridData&) const = default;
};

enum class HeatSource {AMBIENT_AIR, HOTROOM};

struct HeatPumpData {
    float heat_power = 70.0f;
    HeatSource heat_source = HeatSource::AMBIENT_AIR;
    float send_temp = 70.0f;

    bool operator==(const HeatPumpData&) const = default;
};

struct MopData {
    float maximum_load = 300.0f;

    bool operator==(const MopData&) const = default;
};

struct Renewables {
    std::vector<float> yield_scalars = {};

    bool operator==(const Renewables&) const = default;
};

struct TaskConfig {
    float capex_limit = 2500000.0f;
};


template<>
struct std::hash<Building>
{
    std::size_t operator()(const Building& b) const noexcept
    {
        std::size_t h=0;
        hash_combine(h, b.scalar_heat_load, b.scalar_electrical_load, b.fabric_intervention_index); 
        return h;
    }
};

template<>
struct std::hash<DataCentreData>
{
    std::size_t operator()(const DataCentreData& d) const noexcept
    {
        std::size_t h=0;
        hash_combine(h, d.hotroom_temp, d.maximum_load); 
        return h;
    }
};

template<>
struct std::hash<DomesticHotWater>
{
    std::size_t operator()(const DomesticHotWater& d) const noexcept
    {
        // We've only got one component, so hash it directly.
        return std::hash<float>{}(d.cylinder_volume);
    }
};

template<>
struct std::hash<ElectricVehicles>
{
    std::size_t operator()(const ElectricVehicles& ev) const noexcept
    {
        std::size_t h = 0;
        hash_combine(h, ev.fast_chargers, ev.flexible_load_ratio, ev.rapid_chargers, ev.scalar_electrical_load,
        ev.small_chargers, ev.ultra_chargers);
        return h;
    }
};

template<>
struct std::hash<EnergyStorageSystem>
{
    std::size_t operator()(const EnergyStorageSystem& ess) const noexcept
    {
        std::size_t h = 0;
        hash_combine(h, ess.battery_mode, ess.capacity, ess.charge_power, ess.initial_charge, ess.discharge_power);
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
            grid.grid_export, grid.grid_import,
            grid.import_headroom, grid.tariff_index);
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
            hpd.heat_power, hpd.heat_source, hpd.send_temp);
        return h;
    }
};

template<>
struct std::hash<MopData>
{
    std::size_t operator()(const MopData& m) const noexcept
    {
        // We've only got one component, so hash it directly.
        return std::hash<float>{}(m.maximum_load);
    }
};

class vector_hasher {
    // Hash a float vector, which we need for the renewables
    // yield scalars.
    // Taken from https://stackoverflow.com/questions/20511347/a-good-hash-function-for-a-vector
    public:
    std::size_t operator()(std::vector<float> const& vec) const {
        std::size_t seed = vec.size();
        for(auto x : vec) {
            std::uint32_t y = std::bit_cast<std::uint32_t>(x);
            y = ((y >> 16) ^ y) * 0x45d9f3b;
            y = ((y >> 16) ^ y) * 0x45d9f3b;
            y = (y >> 16) ^ y;
            seed ^= y + 0x9e3779b9 + (seed << 6) + (seed >> 2);
        }
        return seed;
    };
};

template<>
struct std::hash<Renewables>
{
    std::size_t operator()(const Renewables& r) const noexcept
    {
        // We've only got one component, so hash it directly.
        return vector_hasher{}(r.yield_scalars);
    }
};