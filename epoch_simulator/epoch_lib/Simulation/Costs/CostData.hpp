#pragma once

struct ThreeTierCostData {
	float fixed;
	float small_threshold;
	float mid_threshold;

	float small_cost;
	float mid_cost;
	float large_cost;
};

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


// The Capex price data is defined as a hardcoded struct for now
// TODO - this should ultimately be read from JSON

struct CapexPrices {
	// dhw costs are in £ / litre
	ThreeTierCostData dhw_prices = ThreeTierCostData(1000.0f, 300.0f, 800.0f, 6.5f, 5.0f, 3.0f);

	//EV Charger costs are in £ / charger (of each of the four types)
	EVChargerCosts ev_prices = EVChargerCosts();

	// grid costs are in £ / kW DC
	ThreeTierCostData grid_prices = ThreeTierCostData(0.0f, 50.0f, 1000.0f, 240.0f, 160.0f, 120.0f);

	// Heatpump costs are in £ / KW DC
	// 2500 mid_cost not a mistake - mid range HP have reverse economies of scale,
	// fixed costs deals with most of CAPEX for small <15 kW systems
	ThreeTierCostData heatpump_prices = ThreeTierCostData(4000.0f, 15.0f, 100.0f, 800.0f, 2500.0f, 1500.0f);

	// For the Energy Storage System we have 3 sets of costs
	ThreeTierCostData ess_pcs_prices = ThreeTierCostData(0.0f, 50.0f, 1000.0f, 250.0f, 125.0f, 75.0f);
	ThreeTierCostData ess_enclosure_prices = ThreeTierCostData(0.0f, 100.0f, 2000.0f, 480.0f, 360.0f, 300.0f);
	ThreeTierCostData ess_enclosure_disposal_prices = ThreeTierCostData(0.0f, 100.0f, 2000.0f, 30.0f, 20.0f, 15.0f);

	// Renewables
	ThreeTierCostData pv_panel_prices = ThreeTierCostData(0.0f, 50.0f, 1000.0f, 150.0f, 110.0f, 95.0f);
	ThreeTierCostData pv_roof_prices = ThreeTierCostData(4250.0f, 50.0f, 1000.0f, 850.0f, 750.0f, 600.0f);
	ThreeTierCostData pv_ground_prices = ThreeTierCostData(4250.0f, 50.0f, 1000.0f, 800.0f, 600.0f, 500.0f);
	ThreeTierCostData pv_BoP_prices = ThreeTierCostData(0.0f, 50.0f, 1000.0f, 120.0f, 88.0f, 76.0f);
};

struct OpexPrices {
	ThreeTierCostData ess_pcs_prices = ThreeTierCostData(0.0f, 50.0f, 1000.0f, 8.0f, 4.0f, 1.0f);
	ThreeTierCostData ess_enclosure_prices = ThreeTierCostData(0.0f, 100.0f, 2000.0f, 10.0f, 4.0f, 2.0f);
	ThreeTierCostData pv_prices = ThreeTierCostData(0.0f, 50.0f, 1000.0f, 2.0f, 1.0f, 0.5f);
};

// We store the component costs as they are necessary to calculate annualised costs
struct CapexBreakdown {
	float dhw_capex;

	float ev_charger_cost;
	float ev_charger_install;

	float grid_capex;

	float heatpump_capex;

	float ess_pcs_capex;
	float ess_enclosure_capex;
	float ess_enclosure_disposal;

	float pv_panel_capex;
	float pv_roof_capex;
	float pv_ground_capex;
	float pv_BoP_capex;

	float total_capex;
};

struct OpexBreakdown {
	float ess_pcs_opex;
	float ess_enclosure_opex;
	float pv_opex;
};


float calculate_three_tier_costs(const ThreeTierCostData& tierData, float numUnits);
