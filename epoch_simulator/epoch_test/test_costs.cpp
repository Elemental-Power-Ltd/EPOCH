#include <gtest/gtest.h>

#include "../epoch_lib/Simulation/Costs/CostData.hpp"


class ThreeTierCostTest : public ::testing::Test {
protected:
	ThreeTierCostData threeTierCostData;

	ThreeTierCostTest() :
		threeTierCostData(ThreeTierCostData(500.0f, 50.0f, 100.0f, 3.0f, 2.0f, 1.0f)) {}
};



TEST_F(ThreeTierCostTest, ThreeTierZeroUnits) {
	// Costing 0 units should return the fixed price
	float cost = calculate_three_tier_costs(threeTierCostData, 0);
	EXPECT_EQ(cost, threeTierCostData.fixed);
}

TEST_F(ThreeTierCostTest, ThreeTierThresholdSmallBoundary) {
	// Check that we correctly handle units either side of the small threshold
	// The price should continue increasing as we increase the number of units
	float underSmallBoundary = 49.0f;
	float onSmallBoundary = 50.0f;
	float overSmallBoundary = 51.0f;


	float underCost = calculate_three_tier_costs(threeTierCostData, underSmallBoundary);
	float onCost = calculate_three_tier_costs(threeTierCostData, onSmallBoundary);
	float overCost = calculate_three_tier_costs(threeTierCostData, overSmallBoundary);

	EXPECT_LT(underCost, onCost);
	EXPECT_LT(onCost, overCost);
}

TEST_F(ThreeTierCostTest, ThreeTierThresholdMidBoundary) {
	// Check that we correctly handle units either side of the mid threshold
	// The price should continue increasing as we increase the number of units
	float underMidBoundary = 99.0f;
	float onMidBoundary = 100.0f;
	float overMidBoundary = 101.0f;


	float underCost = calculate_three_tier_costs(threeTierCostData, underMidBoundary);
	float onCost = calculate_three_tier_costs(threeTierCostData, onMidBoundary);
	float overCost = calculate_three_tier_costs(threeTierCostData, overMidBoundary);

	EXPECT_LT(underCost, onCost);
	EXPECT_LT(onCost, overCost);
}