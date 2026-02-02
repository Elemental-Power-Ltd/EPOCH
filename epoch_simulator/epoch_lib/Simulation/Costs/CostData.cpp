#include "CostData.hpp"


float calculate_piecewise_costs(const PiecewiseCostModel& costModel, float num_units) {
	/**
	* Calculate the cost of a component (or part of a component) using a piecewise linear model.
	* 
	* A fixed price is applied and then each segment is applied up to its upper threshold
	* Finally a final rate for anything beyond the segments is applied
	* 
	* This function is unit independent.
	*/

	// First apply the fixed cost
	float total_cost = costModel.fixed_cost;

	float prev_upper = 0.0f;

	for (const auto& segment : costModel.segments) {

		if (num_units > segment.upper) {
			total_cost += (segment.upper - prev_upper) * segment.rate;
		} else {
			// This is the final segment we need to deal with
			total_cost += (num_units - prev_upper) * segment.rate;
			return total_cost;
		}

		prev_upper = segment.upper;
	}

	if (num_units > prev_upper) {
		total_cost += (num_units - prev_upper) * costModel.final_rate;
	}

	return total_cost;
}


CapexModel make_default_capex_prices() {
	CapexModel model;

	model.dhw_prices = PiecewiseCostModel(
		1000.0f,
		{
			{300.0f, 6.5f},
			{800.0f, 5.0f},
		},
		3.0f
		);

	model.ev_prices = EVChargerCosts();

	model.gas_heater_prices = PiecewiseCostModel(
		1000.0f,
		{
			{100.0f, 250.0f},
			{200.0f, 225.0f}
		},
		200.0f
	);

	model.grid_prices = PiecewiseCostModel(
		0.0f,
		{
			{50.0f, 240.0f},
			{1000.0f, 160.0f}
		},
		120.0f
	);

	// mid range HP have reverse economies of scale, 2500 is not a mistake
	// fixed costs deals with most of CAPEX for small <15 kW systems
	model.heatpump_prices = PiecewiseCostModel(
		4000.0f,
		{
			{15.0f, 800.0f},
			{100.0f, 2500.0f}
		},
		1500.0f
	);

	model.ess_pcs_prices = PiecewiseCostModel(
		0.0f,
		{
			{50.0f, 250.0f},
			{1000.0f, 125.0f}
		},
		75.0f
	);
	model.ess_enclosure_prices = PiecewiseCostModel(
		0.0f,
		{
			{100.0f, 480.0f},
			{2000.0f, 360.0f},
		},
		300.0f
		);
	model.ess_enclosure_disposal_prices = PiecewiseCostModel(
		0.0f,
		{
			{100.0f, 30.0f},
			{2000.0f, 20.0f}
		},
		15.0f
	);

	model.pv_panel_prices = PiecewiseCostModel(
		0.0f,
		{
			{50.0f, 150.0f},
			{1000.0f, 110.0f}
		},
		95.0f
	);

	model.pv_roof_prices = PiecewiseCostModel(
		4250.0f,
		{
			{50.0f, 850.0f},
			{1000.0f, 750.0f}
		},
		600.0f
	);

	model.pv_ground_prices = PiecewiseCostModel(
		4250.0f,
		{
			{50.0f, 800.0f},
			{1000.0f, 600.0f}
		},
		500.0f
	);
	model.pv_BoP_prices = PiecewiseCostModel(
		0.0f,
		{
			{50.0f, 120.0f},
			{1000.0f, 88.0f}
		},
		76.0f
	);

	return model;
}

OpexModel make_default_opex_prices() {
	OpexModel model;

	model.ess_pcs_prices = PiecewiseCostModel(
		0.0f,
		{
			{50.0f, 8.0f},
			{1000.0f, 4.0f}
		},
		1.0f
	);
	model.ess_enclosure_prices = PiecewiseCostModel(
		0.0f,
		{
			{100.0f, 10.0f},
			{2000.0f, 4.0f}
		},
		2.0f
	);

	model.gas_heater_prices = PiecewiseCostModel(0.0f, {}, 0.0f);
	model.heatpump_prices = PiecewiseCostModel(0.0f, {}, 0.0f);

	model.pv_prices = PiecewiseCostModel(
		0.0f,
		{
			{50.0f, 2.0f},
			{1000.0f, 1.0f}
		},
		0.5f
	);

	return model;
}

float OpexBreakdown::sum() const {
	return ess_pcs_opex + ess_enclosure_opex + gas_heater_opex + heatpump_opex + pv_opex;
}