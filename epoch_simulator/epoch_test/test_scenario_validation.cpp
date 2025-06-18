#include <gtest/gtest.h>

#include "../epoch_lib/Simulation/SiteData.hpp"
#include "../epoch_lib/Simulation/TaskData.hpp"
#include "../epoch_lib/Simulation/Simulate.hpp"
#include "test_helpers.hpp"


class SimulatorTest : public ::testing::Test {
protected:
    Simulator simulator;

    // These tests all work with a boring but technically valid set of SiteData
    SimulatorTest():
        simulator(make24HourSiteData())
    {}
};

// test a valid scenario
TEST_F(SimulatorTest, ValidateScenario_ValidData_NoThrow) {
    TaskData taskData = makeValidTaskData();

    EXPECT_NO_THROW(simulator.validateScenario(taskData));
}

// test with fabric_intervention_index out of range
TEST_F(SimulatorTest, ValidateScenario_FabricIndexOutOfRange_Throws) {
    TaskData taskData = makeValidTaskData();
    taskData.building->fabric_intervention_index = 2;

    EXPECT_THROW(simulator.validateScenario(taskData), std::runtime_error);
}

// test with tariff_index out of range
TEST_F(SimulatorTest, ValidateScenario_TariffIndexOutOfRange_Throws) {
    TaskData taskData = makeValidTaskData();
    // siteData contains two tariffs
    taskData.grid->tariff_index = 2;

    EXPECT_THROW(simulator.validateScenario(taskData), std::runtime_error);
}

// test with solar_index out of range
TEST_F(SimulatorTest, ValidateScenario_SolarIndexOutOfRange_Throws) {
    // taskData and siteData have 2 solar_yields
    TaskData taskData = makeValidTaskData();
    taskData.solar_panels[1].yield_index = 2;

    EXPECT_THROW(simulator.validateScenario(taskData), std::runtime_error);
}

// test with mismatched solar
TEST_F(SimulatorTest, ValidateScenario_FewerYieldScalars_NoThrow) {

    TaskData taskData = makeValidTaskData();

    SolarData singleSolar;
    singleSolar.yield_scalar = 1.0f;
    singleSolar.yield_index = 1;

    // fewer solar_panels than solar_yields is permitted
    taskData.solar_panels = {singleSolar};  

    EXPECT_NO_THROW(simulator.validateScenario(taskData));
}

// an empty TaskData should be always be valid
TEST_F(SimulatorTest, ValidateScenario_NoComponents_NoThrow) {
    TaskData taskData;
    EXPECT_NO_THROW(simulator.validateScenario(taskData));
}

// test we can use a fabric intervention
TEST_F(SimulatorTest, ValidateScenario_FabricIndexEqualsOne_Succeeds) {
    TaskData taskData = makeValidTaskData();
    // site data has 1 fabric intervention in addition to building_hload
    // we should be able to use it
    taskData.building->fabric_intervention_index = 1;

    EXPECT_NO_THROW(simulator.validateScenario(taskData));
}

