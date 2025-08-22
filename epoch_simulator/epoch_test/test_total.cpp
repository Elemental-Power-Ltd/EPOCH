#include <gtest/gtest.h>

#include <filesystem>
#include <memory>

#include "../epoch_lib/Simulation/Simulate.hpp"
#include "../epoch_lib/io/FileHandling.hpp"

namespace fs = std::filesystem;

/**
* These tests run a single simulation of EPOCH to compare against a previously computed result.
* It is not expected that these tests will always stay the same 
* as updates to the internal model will change the results
* 
* Instead, these results should provide a warning against unintended changes to the underlying logic.
*/
class EpochSimulationRun : public ::testing::Test {
protected:
	Simulator simulator;

	EpochSimulationRun() :
		simulator(readSiteData(fs::path{ "./test_files/siteData_MountHotel.json" }), TaskConfig{})
	{}
};


TEST_F(EpochSimulationRun, EmptyTaskData) {
	/**
	* Test against a (near) empty TaskData
	* That is one with a Building, Grid, Gas Heater (and config) but no new components to be installed
	* 
	* The Grid and Gas Heater are oversized to ensure we don't have a shortfall
	*/

	TaskData task = readTaskData(fs::path{"./test_files/taskData_empty.json" });
	auto result = simulator.simulateScenario(task);

	// We haven't installed anything, so we expect all of the results to be 0
	// we allow an absolute error of 0.1f
	EXPECT_NEAR(result.metrics.total_capex, 0.0f, 0.1f);
	EXPECT_NEAR(result.comparison.carbon_balance_scope_1, 0.0f, 0.1f);
	EXPECT_NEAR(result.comparison.carbon_balance_scope_2, 0.0f, 0.1f);
	EXPECT_NEAR(result.comparison.cost_balance, 0.0f, 0.1f);
	EXPECT_NEAR(result.comparison.payback_horizon_years, 0.0f, 0.1f);
	EXPECT_NEAR(result.metrics.total_annualised_cost, 0.0f, 0.1f);
}

TEST_F(EpochSimulationRun, CommonTaskData) {
	/**
	* Test with a TaskData containing all of the common components for a scenario
	* (Building, Grid, Solar Panels, ASHP, ESS, DHW)
	* but none of the unusual ones
	*/
	TaskData task = readTaskData(fs::path{ "./test_files/taskData_common.json" });
	auto result = simulator.simulateScenario(task);

	EXPECT_FLOAT_EQ(result.metrics.total_capex, 1377395.4f);
	EXPECT_FLOAT_EQ(result.comparison.carbon_balance_scope_1, 102757.23f);
	EXPECT_FLOAT_EQ(result.comparison.carbon_balance_scope_2, 71935.516f);
	EXPECT_FLOAT_EQ(result.comparison.cost_balance, 2118.7891f);
	EXPECT_FLOAT_EQ(result.comparison.payback_horizon_years, 16.481588f);
	EXPECT_FLOAT_EQ(result.metrics.total_annualised_cost, 87438.258f);
}

TEST_F(EpochSimulationRun, FullTaskData) {
	/**
	* Test with a TaskData containing every component
	*/
	TaskData task = readTaskData(fs::path{ "./test_files/taskData_full.json" });
	auto result = simulator.simulateScenario(task);

	EXPECT_FLOAT_EQ(result.metrics.total_capex, 1296895.4f);
	EXPECT_FLOAT_EQ(result.comparison.carbon_balance_scope_1, 144888.22f);
	EXPECT_FLOAT_EQ(result.comparison.carbon_balance_scope_2, -11578.438f);
	EXPECT_FLOAT_EQ(result.comparison.cost_balance, 174644.94f);
	EXPECT_FLOAT_EQ(result.comparison.payback_horizon_years, 5.2368517f);
	EXPECT_FLOAT_EQ(result.metrics.total_annualised_cost, 78988.258f);
}
