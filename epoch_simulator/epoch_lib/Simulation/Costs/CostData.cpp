#include "CostData.hpp"

float calculate_three_tier_costs(const ThreeTierCostData& tierData, float numUnits) {
	// This is a generalised method to apply a three-tiered pricing structure to costs

	// First apply the fixed cost
	float total_cost = tierData.fixed;

	// Then apply a piece-wise costing model

	// Anything below the small threshold is charged at the small cost rate
	// Anything between small and medium is charged then charged the medium rate for everything above the small threshold
	// Anything above the medium threshold is charged the large cost rate for everything above the medium threshold

	// The units in the function can be arbitrary
	// The important part is that the thresholds in the tierData are the same units are t

	if (numUnits < tierData.small_threshold) {
		total_cost += tierData.small_cost * numUnits;
	}
	else if (tierData.small_threshold < numUnits && numUnits < tierData.mid_threshold) {
		total_cost += tierData.small_cost * tierData.small_threshold;
		total_cost += tierData.mid_cost * (numUnits - tierData.small_threshold);
	}
	else if (numUnits > tierData.mid_threshold) {
		total_cost += tierData.small_cost * tierData.small_threshold;
		total_cost += tierData.mid_cost * (tierData.mid_threshold - tierData.small_threshold);
		total_cost += tierData.large_cost * (numUnits - tierData.mid_threshold);
	}

	return total_cost;
}