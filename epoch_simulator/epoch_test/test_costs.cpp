#include <gtest/gtest.h>

#include "../epoch_lib/Simulation/Costs/CostData.hpp"


class PiecewiseCostTest : public ::testing::Test {
protected:
	PiecewiseCostModel piecewiseCostModel;

	PiecewiseCostTest() :
		piecewiseCostModel( 500.0f, { {50.0f, 3.0f}, {100.0f, 2.0f} }, 1.0f )
	{}
};



TEST_F(PiecewiseCostTest, ThreeTierZeroUnits) {
	// Costing 0 units should return the fixed price
	float cost = calculate_piecewise_costs(piecewiseCostModel, 0);
	EXPECT_EQ(cost, piecewiseCostModel.fixed_cost);
}

TEST_F(PiecewiseCostTest, ThreeTierThresholdSmallBoundary) {
	// Check that we correctly handle units either side of the small threshold
	// The price should continue increasing as we increase the number of units
	float underSmallBoundary = 49.0f;
	float onSmallBoundary = 50.0f;
	float overSmallBoundary = 51.0f;


	float underCost = calculate_piecewise_costs(piecewiseCostModel, underSmallBoundary);
	float onCost = calculate_piecewise_costs(piecewiseCostModel, onSmallBoundary);
	float overCost = calculate_piecewise_costs(piecewiseCostModel, overSmallBoundary);

	EXPECT_LT(underCost, onCost);
	EXPECT_LT(onCost, overCost);
}

TEST_F(PiecewiseCostTest, ThreeTierThresholdMidBoundary) {
	// Check that we correctly handle units either side of the mid threshold
	// The price should continue increasing as we increase the number of units
	float underMidBoundary = 99.0f;
	float onMidBoundary = 100.0f;
	float overMidBoundary = 101.0f;


	float underCost = calculate_piecewise_costs(piecewiseCostModel, underMidBoundary);
	float onCost = calculate_piecewise_costs(piecewiseCostModel, onMidBoundary);
	float overCost = calculate_piecewise_costs(piecewiseCostModel, overMidBoundary);

	EXPECT_LT(underCost, onCost);
	EXPECT_LT(onCost, overCost);
}

TEST_F(PiecewiseCostTest, NoSegments) {
	// A cost model with no intermediate segments should be equal to
	// fixed_cost + (final_rate * units)
	// in all cases

	PiecewiseCostModel model{ 120.0f, {}, 4.0f };

	// 0 units should equal the fixed_cost
	EXPECT_FLOAT_EQ(calculate_piecewise_costs(model, 0.0f), 120.0f);

	EXPECT_FLOAT_EQ(calculate_piecewise_costs(model, 9.5f), 120.0f + 9.5f * 4.0f);
	EXPECT_FLOAT_EQ(calculate_piecewise_costs(model, 400.0f), 120.0f + 400.0f * 4.0f);

}


TEST_F(PiecewiseCostTest, SingleSegment) {
	// A cost model with no intermediate segments should be equal to
	// fixed_cost + (final_rate * units)
	// in all cases

	PiecewiseCostModel model{ 10.0f, {{100.0f, 3.0f}}, 2.0f };

	// test within the first segment
	EXPECT_FLOAT_EQ(calculate_piecewise_costs(model, 50.0f), 10.0f + (50.0f * 3.0f));

	// test on the boundary of the segment
	EXPECT_FLOAT_EQ(calculate_piecewise_costs(model, 100.0f), 10.0f + (100.0f * 3.0f));

	// test into the final rate
	EXPECT_FLOAT_EQ(calculate_piecewise_costs(model, 150.0f), 10.0f + (100.0f * 3.0f) + (50.0f * 2.0f));

}
