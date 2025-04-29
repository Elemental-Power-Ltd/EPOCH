#include <gtest/gtest.h>
#include <Eigen/Dense>

#include "test_helpers.hpp"

#include "../epoch_lib/Simulation/Simulate.hpp"
#include "../epoch_lib/Simulation/TaskData.hpp"
#include "../epoch_lib/Simulation/Hotel.hpp"

class FabricInterventionTest : public ::testing::Test {
protected:
	SiteData siteData;

	FabricInterventionTest() :
		siteData(make24HourSiteData())
	{
		// Construct a fabric intervention that halves the energy for �100
		FabricIntervention reducedEnergy = { 100.0f, Eigen::VectorXf::Constant(24, 0.5f) };
		siteData.fabric_interventions[0] = reducedEnergy;

	}
};

// Test we correctly calculate the cost of this fabric intervention
TEST_F(FabricInterventionTest, calculateCapex) {

	// set up a basic TaskData to use the fixture's fabric intervention
	TaskData taskData{};
	taskData.grid = GridData();
	taskData.building = Building();
	// 1 based indexing here, 0 is the base building_hload
	taskData.building->fabric_intervention_index = 1;


	Simulator sim{ siteData };
	auto capex = sim.calculateCapex(taskData);

	EXPECT_EQ(capex.building_fabric_capex, 100.0f);
}


TEST_F(FabricInterventionTest, reduceHeat) {

	// Run with the default building_hload (a 24x1 vector)

	TempSum defaultTempSum{ siteData };

	auto defaultBuilding = Building();
	// explicitly state that we're using building_hload
	defaultBuilding.fabric_intervention_index = 0;

	auto defaultHotel = Hotel{ siteData, defaultBuilding };

	defaultHotel.AllCalcs(defaultTempSum);


	// Run with our intervention (a 24x0.5 vector)

	TempSum interventionTempSum{ siteData };

	auto interventionBuilding = Building();
	// use the fabric intervention for this fixture
	interventionBuilding.fabric_intervention_index = 1;

	auto interventionHotel = Hotel{ siteData, interventionBuilding };

	interventionHotel.AllCalcs(interventionTempSum);

	// We expect our intervention to require less heat
	EXPECT_LT(interventionTempSum.Heat_h.sum(), defaultTempSum.Heat_h.sum());
}