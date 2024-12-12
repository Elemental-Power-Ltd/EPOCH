#include "Opex.hpp"

static OpexPrices opex_prices{};

OpexBreakdown calculate_opex(const TaskData& taskData) {
	OpexBreakdown opex_breakdown{};

	if (taskData.renewables) {
		calculate_pv_opex(taskData.renewables.value(), opex_breakdown);
	}

	if (taskData.energy_storage_system) {
		calculate_ess_opex(taskData.energy_storage_system.value(), opex_breakdown);
	}

	return opex_breakdown;
}

void calculate_ess_opex(const EnergyStorageSystem& ess, OpexBreakdown& opex_breakdown) {
	float ess_power = std::max(ess.charge_power, ess.discharge_power);
	opex_breakdown.ess_pcs_opex = calculate_three_tier_costs(opex_prices.ess_pcs_prices, ess_power);

	opex_breakdown.ess_enclosure_opex = calculate_three_tier_costs(opex_prices.ess_enclosure_prices, ess.capacity);
}


void calculate_pv_opex(const Renewables& pv, OpexBreakdown& opex_breakdown) {
	float pv_kWp_total = 0;
	for (auto& scalar : pv.yield_scalars) {
		pv_kWp_total += scalar;
	}

	opex_breakdown.pv_opex = calculate_three_tier_costs(opex_prices.pv_prices, pv_kWp_total);

}
