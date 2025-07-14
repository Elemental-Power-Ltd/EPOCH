
#include <gtest/gtest.h>

#include "test_helpers.hpp"

#include "../epoch_lib/Simulation/TaskData.hpp"
#include "../epoch_lib/Simulation/Costs/Capex.hpp"

class FundingTest : public ::testing::Test {
protected:
	// Construct a default SiteData containing a GasHeater
	SiteData siteData = make24HourSiteData();
	TaskData taskData = TaskData();
};

// Test that the boiler upgrade scheme applies when the config is set
TEST_F(FundingTest, ReceivesBoilerUpgradeFunding) {

	TaskData scenario = {};
	scenario.heat_pump = HeatPumpData();
	// We set a high power to make sure this heat pump costs more than £7,500
	scenario.heat_pump->heat_power = 30.0f;

	// check we apply the funding when the config is true
	scenario.config.use_boiler_upgrade_scheme = true;
	auto capex_with_funding = calculate_capex_with_discounts(siteData, scenario);
	EXPECT_EQ(capex_with_funding.boiler_upgrade_scheme_funding, 7500.0f);

	// now check that we don't apply the funding if the config is false
	scenario.config.use_boiler_upgrade_scheme = false;
	auto capex_without_funding = calculate_capex_with_discounts(siteData, scenario);
	EXPECT_LT(capex_with_funding.total_capex, capex_without_funding.total_capex);
}

// Test that we don't award the grant when there was never a boiler to replace
TEST_F(FundingTest, BaselineWithoutBoiler) {
	TaskData baseline = {};
	baseline.heat_pump = HeatPumpData();
	SiteData sd = make24HourSiteData(baseline);

	TaskData scenario = {};
	scenario.heat_pump = HeatPumpData();

	scenario.config.use_boiler_upgrade_scheme = true;
	auto capex = calculate_capex_with_discounts(sd, scenario);

	// The baseline doesn't have a boiler, scenario is not eligible
	EXPECT_EQ(capex.boiler_upgrade_scheme_funding, 0.0f);
}

// Test that we don't award the grant when the boiler is kept
TEST_F(FundingTest, ScenarioKeepsBoiler) {
	TaskData scenario = {};
	scenario.heat_pump = HeatPumpData();
	scenario.gas_heater = GasCHData();

	scenario.config.use_boiler_upgrade_scheme = true;
	auto capex = calculate_capex_with_discounts(siteData, scenario);

	// The scenario kept the boiler and so is not eligible
	EXPECT_EQ(capex.boiler_upgrade_scheme_funding, 0.0f);
}


// Test that we don't award more than the boiler cost
TEST_F(FundingTest, PartialBoilerUpgradeFunding) {
	TaskData scenario = {};
	scenario.heat_pump = HeatPumpData();
	// A 2kw heatpump should cost £5600 with the default price data
	scenario.heat_pump->heat_power = 2.0f;

	scenario.config.use_boiler_upgrade_scheme = true;
	auto capex = calculate_capex_with_discounts(siteData, scenario);

	EXPECT_LT(capex.heatpump_capex, 7500.0f);
	EXPECT_EQ(capex.heatpump_capex, capex.boiler_upgrade_scheme_funding);
}


TEST_F(FundingTest, GeneralGrant) {
	TaskData scenario = {};
	scenario.grid = GridData();
	scenario.building = Building();

	// add some expensive components
	scenario.heat_pump = HeatPumpData();
	scenario.heat_pump->heat_power = 50.0f;

	scenario.domestic_hot_water = DomesticHotWater();
	scenario.domestic_hot_water->cylinder_volume = 1000.0f;

	SolarData solar1;
	solar1.yield_scalar = 200.0f;
	solar1.yield_index = 0;

	SolarData solar2;
	solar2.yield_scalar = 100.0f;
	solar2.yield_index = 1;

	scenario.solar_panels = { solar1, solar2 };

	auto capex_without_funding = calculate_capex_with_discounts(siteData, scenario);

	scenario.config.general_grant_funding = 50000.0f;
	auto capex_with_funding = calculate_capex_with_discounts(siteData, scenario);

	EXPECT_LT(capex_with_funding.total_capex, capex_without_funding.total_capex);


	scenario.config.general_grant_funding = 1000000000.0f;
	auto capex_with_billion_grant = calculate_capex_with_discounts(siteData, scenario);
	EXPECT_EQ(capex_with_billion_grant.total_capex, 0.0f);

}