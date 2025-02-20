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
	// put SiteData into a unique_ptr and use a test fixture so we only have to read it once
	static std::unique_ptr<SiteData> mountSiteData;

	static void SetUpTestSuite() {
		fs::path path{ "./test_files/siteData_MountHotel.json" };
		mountSiteData = std::make_unique<SiteData>(readSiteData(path));
	}
};

std::unique_ptr<SiteData> EpochSimulationRun::mountSiteData = nullptr;

TEST_F(EpochSimulationRun, EmptyTaskData) {
	/**
	* Test against a (near) empty TaskData
	* That is one with a Building, Grid (and config) but no new components to be installed
	*/

	TaskData task = readTaskData(fs::path{"./test_files/taskData_empty.json" });

	auto sim = Simulator();

	auto result = sim.simulateScenario(*mountSiteData, task);

	// We haven't installed anything, so we expect all of the results to be 0
	EXPECT_FLOAT_EQ(result.project_CAPEX, 0);
	EXPECT_FLOAT_EQ(result.scenario_carbon_balance_scope_1, 0);
	EXPECT_FLOAT_EQ(result.scenario_carbon_balance_scope_2, 0);
	EXPECT_FLOAT_EQ(result.scenario_cost_balance, 0);
	EXPECT_FLOAT_EQ(result.payback_horizon_years, 0);
	EXPECT_FLOAT_EQ(result.total_annualised_cost, 0);
}

TEST_F(EpochSimulationRun, CommonTaskData) {
	/**
	* Test with a TaskData containing all of the common components for a scenario
	* (Building, Grid, Solar Panels, ASHP, ESS, DHW)
	* but none of the unusual ones
	*/
	TaskData task = readTaskData(fs::path{ "./test_files/taskData_common.json" });

	auto sim = Simulator();

	auto result = sim.simulateScenario(*mountSiteData, task);

	EXPECT_FLOAT_EQ(result.project_CAPEX, 1238945.4f);
	EXPECT_FLOAT_EQ(result.scenario_carbon_balance_scope_1, 85420.227f);
	EXPECT_FLOAT_EQ(result.scenario_carbon_balance_scope_2, 73841.875f);
	EXPECT_FLOAT_EQ(result.scenario_cost_balance, 14127.625f);
	EXPECT_FLOAT_EQ(result.payback_horizon_years, 87.696648f);
	EXPECT_FLOAT_EQ(result.total_annualised_cost, 74830.258f);
}

TEST_F(EpochSimulationRun, FullTaskData) {
	/**
	* Test with a TaskData containing every component
	*/
	TaskData task = readTaskData(fs::path{ "./test_files/taskData_full.json" });

	auto sim = Simulator();

	auto result = sim.simulateScenario(*mountSiteData, task);

	EXPECT_FLOAT_EQ(result.project_CAPEX, 1249445.4f);
	EXPECT_FLOAT_EQ(result.scenario_carbon_balance_scope_1, 135397.08f);
	EXPECT_FLOAT_EQ(result.scenario_carbon_balance_scope_2, -8940.9922f);
	EXPECT_FLOAT_EQ(result.scenario_cost_balance, 181001.09f);
	EXPECT_FLOAT_EQ(result.payback_horizon_years, 6.9029713f);
	EXPECT_FLOAT_EQ(result.total_annualised_cost, 75530.258f);
}