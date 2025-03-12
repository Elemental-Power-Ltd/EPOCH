#pragma once

#include <string>

#include "../Simulation/TaskComponents.hpp"

// Helper methods to convert the TaskComponent enums to string
std::string enumToString(const HeatSource& heat_source);
std::string enumToString(const BatteryMode& battery_mode);
std::string enumToString(const GasType& gas_type);
