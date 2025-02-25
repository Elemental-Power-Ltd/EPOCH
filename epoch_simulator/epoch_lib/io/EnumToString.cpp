#include "EnumToString.hpp"

#include <stdexcept>

std::string enumToString(const HeatSource& heat_source) {
	switch (heat_source) {
	case HeatSource::AMBIENT_AIR:
		return "AMBIENT_AIR";
	case HeatSource::HOTROOM:
		return "HOTROOM";
	default:
		throw std::invalid_argument("Invalid Heat Source");
	}
}

std::string enumToString(const BatteryMode& battery_mode) {
	switch (battery_mode) {
	case BatteryMode::CONSUME:
		return "CONSUME";
	case BatteryMode::CONSUME_PLUS:
		return "CONSUME_PLUS";
	default:
		throw std::invalid_argument("Invalid Battery Mode");
	}
}