#include "EnumToString.hpp"

#include <stdexcept>

std::string enumToString(const HeatSource heat_source) {
	switch (heat_source) {
	case HeatSource::AMBIENT_AIR:
		return "AMBIENT_AIR";
	case HeatSource::HOTROOM:
		return "HOTROOM";
	default:
		throw std::invalid_argument("Invalid Heat Source");
	}
}

std::string enumToString(const BatteryMode battery_mode) {
	switch (battery_mode) {
	case BatteryMode::CONSUME:
		return "CONSUME";
	case BatteryMode::CONSUME_PLUS:
		return "CONSUME_PLUS";
	default:
		throw std::invalid_argument("Invalid Battery Mode");
	}
}

std::string enumToString(const GasType gas_type) {
	switch (gas_type) {
	case GasType::NATURAL_GAS:
		return "NATURAL_GAS";
	case GasType::LIQUID_PETROLEUM_GAS:
		return "LIQUID_PETROLEUM_GAS";
	default:
		throw std::invalid_argument("Invalid Gas Type");
	}
}

std::string enumToString(const RatingGrade grade)
{
	switch (grade) {
	case RatingGrade::A:
		return "A";
	case RatingGrade::B:
		return "B";
	case RatingGrade::C:
		return "C";
	case RatingGrade::D:
		return "D";
	case RatingGrade::E:
		return "E";
	case RatingGrade::F:
		return "F";
	case RatingGrade::G:
		return "G";
	default:
		throw std::invalid_argument("Invalid SAP Grade");

	}
}
