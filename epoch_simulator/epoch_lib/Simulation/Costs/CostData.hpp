#pragma once

#include <vector>

struct EVChargerCosts {
	float small_cost = 1200.0f;
	float fast_cost = 2500.0f;
	float rapid_cost = 20000.0f;
	float ultra_cost = 60000.0f;

	float small_install = 600.0f;
	float fast_install = 1000.0f;
	float rapid_install = 3000.0f;
	float ultra_install = 10000.0f;
};


struct Segment {
	float upper;
	float rate;
};

struct PiecewiseCostModel {
	float fixed_cost;
	std::vector<Segment> segments;
	float final_rate;

	bool operator==(const PiecewiseCostModel&) const = default;
};


struct CapexModel {
	// dhw costs are in £ / litre
	PiecewiseCostModel dhw_prices;
	//EV Charger costs are in £ / charger (of each of the four types)
	EVChargerCosts ev_prices = EVChargerCosts();

	// Gas Boiler costs are in £ / kW
	PiecewiseCostModel gas_heater_prices;
	// grid costs are in £ / kW DC
	PiecewiseCostModel grid_prices;
	// Heatpump costs are in £ / KW DC
	PiecewiseCostModel heatpump_prices;

	// ESS
	// - PCS cost varies on the charge power
	// - enclosure costs vary on the capacity
	PiecewiseCostModel ess_pcs_prices;
	PiecewiseCostModel ess_enclosure_prices;
	PiecewiseCostModel ess_enclosure_disposal_prices;

	// Solar panels vary on kWp and location
	PiecewiseCostModel pv_panel_prices;
	PiecewiseCostModel pv_roof_prices;
	PiecewiseCostModel pv_ground_prices;
	PiecewiseCostModel pv_BoP_prices;

	static constexpr float max_boiler_upgrade_scheme_funding = 7500.0f;

	bool operator==(const CapexModel&) const = default;
};


struct OpexModel {
	PiecewiseCostModel ess_pcs_prices;
	PiecewiseCostModel ess_enclosure_prices;
	PiecewiseCostModel gas_heater_prices;
	PiecewiseCostModel heatpump_prices;
	PiecewiseCostModel pv_prices;
};


CapexModel make_default_capex_prices();
OpexModel make_default_opex_prices();



struct EVCapex {
	float charger_cost;
	float charger_install;
};

struct ESSCapex {
	float pcs_capex;
	float enclosure_capex;
	float enclosure_disposal;
};

struct SolarCapex {
	float panel_capex;
	float roof_capex;
	float ground_capex;
	float BoP_capex;
};


struct OpexBreakdown {
	float ess_pcs_opex;
	float ess_enclosure_opex;
	float gas_heater_opex;
	float heatpump_opex;
	float pv_opex;

	float sum() const;
};


float calculate_piecewise_costs(const PiecewiseCostModel& costModel, float numUnits);
