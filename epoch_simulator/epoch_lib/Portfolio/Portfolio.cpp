#include "Portfolio.hpp"

#include "../Simulation/Costs/Compare.hpp"

void addMetrics(const SimulationMetrics& from, SimulationMetrics& to) {
	to.total_gas_used += from.total_gas_used;
	to.total_electricity_imported += from.total_electricity_imported;
	to.total_electricity_generated += from.total_electricity_generated;
	to.total_electricity_exported += from.total_electricity_exported;
	to.total_electricity_curtailed += from.total_electricity_curtailed;
	to.total_electricity_used += from.total_electricity_used;

	to.total_heat_load += from.total_heat_load;
	to.total_dhw_load += from.total_dhw_load;
	to.total_ch_load += from.total_ch_load;

	to.total_electrical_shortfall += from.total_electrical_shortfall;
	to.total_heat_shortfall += from.total_heat_shortfall;
	to.total_ch_shortfall += from.total_ch_shortfall;
	to.total_dhw_shortfall += from.total_dhw_shortfall;

	to.total_capex += from.total_capex;
	to.total_gas_import_cost += from.total_gas_import_cost;
	to.total_electricity_import_cost += from.total_electricity_import_cost;
	to.total_electricity_export_gain += from.total_electricity_export_gain;

	to.total_meter_cost += from.total_meter_cost;
	to.total_operating_cost += from.total_operating_cost;
	to.total_annualised_cost += from.total_annualised_cost;
	to.total_net_present_value += from.total_net_present_value;

	to.total_scope_1_emissions += from.total_scope_1_emissions;
	to.total_scope_2_emissions += from.total_scope_2_emissions;
	to.total_combined_carbon_emissions += from.total_combined_carbon_emissions;
}

SimulationResult aggregateSiteResults(const std::vector<SimulationResult>& siteResults) {
	SimulationResult portfolioResult = {};

	for (const auto& site : siteResults) {
		addMetrics(site.baseline_metrics, portfolioResult.baseline_metrics);
		addMetrics(site.metrics, portfolioResult.metrics);

		portfolioResult.comparison.meter_balance += site.comparison.meter_balance;
		portfolioResult.comparison.operating_balance += site.comparison.operating_balance;
		portfolioResult.comparison.cost_balance += site.comparison.cost_balance;
		portfolioResult.comparison.npv_balance += site.comparison.npv_balance;

		portfolioResult.comparison.carbon_balance_scope_1 += site.comparison.carbon_balance_scope_1;
		portfolioResult.comparison.carbon_balance_scope_2 += site.comparison.carbon_balance_scope_2;
		portfolioResult.comparison.combined_carbon_balance += site.comparison.combined_carbon_balance;
	}

	portfolioResult.comparison.payback_horizon_years = calculate_payback_horizon(
		portfolioResult.metrics.total_capex, portfolioResult.comparison.operating_balance
	);

	portfolioResult.comparison.return_on_investment = calculate_return_on_investment(
		portfolioResult.metrics.total_capex, portfolioResult.comparison.operating_balance
	);

	portfolioResult.comparison.carbon_cost = calculate_carbon_cost(
		portfolioResult.metrics.total_capex, portfolioResult.comparison.carbon_balance_scope_1);

	// These metrics don't make sense for a portfolio
	// (they should be nullopt from the initialisation above, this just makes that explicit)
	portfolioResult.metrics.environmental_impact_grade = std::nullopt;
	portfolioResult.metrics.environmental_impact_score = std::nullopt;
	portfolioResult.baseline_metrics.environmental_impact_grade = std::nullopt;
	portfolioResult.baseline_metrics.environmental_impact_score = std::nullopt;

	return portfolioResult;
}

