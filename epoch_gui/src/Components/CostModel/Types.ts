// TODO - extract definitions
export interface Segment {
    upper: number; // upper threshold (exclusive or inclusive depending on backend; typically inclusive bound of the segment)
    rate: number;  // cost per unit within this segment
}

export interface PiecewiseCostModel {
    fixed_cost: number;
    segments: Segment[]; // segments should be sorted by ascending `upper`
    final_rate: number;  // rate applied beyond the last segment
}

export interface CapexModel {
	// dhw costs are in £ / litre
	dhw_prices: PiecewiseCostModel;

	// Gas Boiler costs are in £ / kW
	gas_heater_prices: PiecewiseCostModel;
	// grid costs are in £ / kW DC
	grid_prices: PiecewiseCostModel;
	// Heatpump costs are in £ / KW DC
	heatpump_prices: PiecewiseCostModel;

	// ESS
	// - PCS cost varies on the charge power
	// - enclosure costs vary on the capacity
	ess_pcs_prices: PiecewiseCostModel;
	ess_enclosure_prices: PiecewiseCostModel;
	ess_enclosure_disposal_prices: PiecewiseCostModel;

	// Solar panels vary on kWp and location
	pv_panel_prices: PiecewiseCostModel;
	pv_roof_prices: PiecewiseCostModel;
	pv_ground_prices: PiecewiseCostModel;
	pv_BoP_prices: PiecewiseCostModel;
}

export interface OpexModel {
	ess_pcs_prices: PiecewiseCostModel;
	ess_enclosure_prices: PiecewiseCostModel;
	gas_heater_prices: PiecewiseCostModel;
	heatpump_prices: PiecewiseCostModel;
	pv_prices: PiecewiseCostModel;
}

export interface FullCostModel {
	capex_model: CapexModel;
	opex_model: OpexModel;
}
