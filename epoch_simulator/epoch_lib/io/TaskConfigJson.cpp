#include "TaskConfigJson.hpp"
#include "CostModelJson.hpp"
#include "../Simulation/Costs/CostData.hpp"


// Config
void from_json(const json& j, TaskConfig& config) {
	j.at("capex_limit").get_to(config.capex_limit);
	j.at("use_boiler_upgrade_scheme").get_to(config.use_boiler_upgrade_scheme);
	j.at("general_grant_funding").get_to(config.general_grant_funding);
	j.at("npv_time_horizon").get_to(config.npv_time_horizon);
	j.at("npv_discount_factor").get_to(config.npv_discount_factor);

	if (j.contains("capex_model")) {
		j.at("capex_model").get_to(config.capex_model);
	}
	else {
		config.capex_model = make_default_capex_prices();
	}

	if (j.contains("opex_model")) {
		j.at("opex_model").get_to(config.opex_model);
	}
	else {
		config.opex_model = make_default_opex_prices();
	}
}

void to_json(json& j, const TaskConfig& config) {
	j = json{
		{"capex_limit", config.capex_limit},
		{"use_boiler_upgrade_scheme", config.use_boiler_upgrade_scheme},
		{"general_grant_funding", config.general_grant_funding},
		{"npv_time_horizon", config.npv_time_horizon},
		{"npv_discount_factor", config.npv_discount_factor},
		{"capex_model", config.capex_model},
		{"opex_model", config.opex_model}
	};
}
