#include "CostModelJson.hpp"
#include <vector>


using nlohmann::json;


inline void from_json(const json& j, Segment& s) {
	j.at("upper").get_to(s.upper);
	j.at("rate").get_to(s.rate);
}

inline void to_json(json& j, const Segment& s) {
	j = json{
		{"upper", s.upper},
		{"rate", s.rate}
	};
}

void from_json(const nlohmann::json& j, PiecewiseCostModel& model) {
	j.at("fixed_cost").get_to(model.fixed_cost);
	// we allow 'segments' to be omitted
	if (j.contains("segments")) {
		j.at("segments").get_to(model.segments);
	}
	else {
		model.segments.clear();
	}
	j.at("final_rate").get_to(model.final_rate);
}

void to_json(nlohmann::json& j, const PiecewiseCostModel& model) {
	j = json{
		{"fixed_cost", model.fixed_cost},
		{"segments",   model.segments},
		{"final_rate", model.final_rate}
	};
}

void from_json(const nlohmann::json& j, CapexModel& model) {
	j.at("gas_heater_prices").get_to(model.gas_heater_prices);
	j.at("grid_prices").get_to(model.grid_prices);
	j.at("heatpump_prices").get_to(model.heatpump_prices);

	j.at("ess_pcs_prices").get_to(model.ess_pcs_prices);
	j.at("ess_enclosure_prices").get_to(model.ess_enclosure_prices);
	j.at("ess_enclosure_disposal_prices").get_to(model.ess_enclosure_disposal_prices);

	j.at("pv_panel_prices").get_to(model.pv_panel_prices);
	j.at("pv_roof_prices").get_to(model.pv_roof_prices);
	j.at("pv_ground_prices").get_to(model.pv_ground_prices);
	j.at("pv_BoP_prices").get_to(model.pv_BoP_prices);
}

void to_json(nlohmann::json& j, const CapexModel& model) {
	j = json{
		"gas_heater_prices", model.gas_heater_prices,
		"grid_prices", model.grid_prices,
		"heatpump_prices", model.heatpump_prices,

		"ess_pcs_prices", model.ess_pcs_prices,
		"ess_enclosure_prices", model.ess_enclosure_prices,
		"ess_enclosure_disposal_prices", model.ess_enclosure_disposal_prices,

		"pv_panel_prices", model.pv_panel_prices,
		"pv_roof_prices", model.pv_roof_prices,
		"pv_ground_prices", model.pv_ground_prices,
		"pv_BoP_prices", model.pv_BoP_prices
	};
}

void from_json(const nlohmann::json& j, OpexModel& model) {
	j.at("ess_pcs_prices").get_to(model.ess_pcs_prices);
	j.at("ess_enclosure_prices").get_to(model.ess_enclosure_prices);
	j.at("gas_heater_prices").get_to(model.gas_heater_prices);
	j.at("heatpump_prices").get_to(model.heatpump_prices);
	j.at("pv_prices").get_to(model.pv_prices);
}

void to_json(nlohmann::json& j, const OpexModel& model) {
	j = json{
		"ess_pcs_prices", model.ess_pcs_prices,
		"ess_enclosure_prices", model.ess_enclosure_prices,
		"gas_heater_prices", model.gas_heater_prices,
		"heatpump_prices", model.heatpump_prices,
		"pv_prices", model.pv_prices
	};
}
