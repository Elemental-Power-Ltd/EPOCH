#include "Opex.hpp"


OpexBreakdown calculate_opex(const TaskData& taskData, const OpexModel& opex_model) {
	OpexBreakdown opex_breakdown{};

	if (taskData.solar_panels.size()) {
		float pv_kWp_total = 0;
		for (auto& panel : taskData.solar_panels) {
			pv_kWp_total += panel.yield_scalar;
		}

		opex_breakdown.pv_opex = calculate_piecewise_costs(opex_model.pv_prices, pv_kWp_total);
	}

	if (taskData.energy_storage_system) {
		const auto& ess = taskData.energy_storage_system;
		float ess_power = std::max(ess->charge_power, ess->discharge_power);

		opex_breakdown.ess_pcs_opex = calculate_piecewise_costs(opex_model.ess_pcs_prices, ess_power);
		opex_breakdown.ess_enclosure_opex = calculate_piecewise_costs(opex_model.ess_enclosure_prices, ess->capacity);
	}

	if (taskData.gas_heater) {
		opex_breakdown.gas_heater_opex = calculate_piecewise_costs(opex_model.gas_heater_prices, taskData.gas_heater->maximum_output);
	}

	if (taskData.heat_pump) {
		opex_breakdown.heatpump_opex = calculate_piecewise_costs(opex_model.heatpump_prices, taskData.heat_pump->heat_power);
	}

	return opex_breakdown;
}

