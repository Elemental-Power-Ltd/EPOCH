
#include <gtest/gtest.h>
#include "../epoch_lib/Simulation/SiteData.hpp"
#include "../epoch_lib/Simulation/PV.hpp"
#include "../epoch_lib/Simulation/TaskData.hpp"
#include "test_helpers.hpp"

#include <Eigen/Core>

class BasicPVTest : public ::testing::Test {
protected:
    SiteData siteData;
    Renewables renewables;
    TempSum tempsum;

    BasicPVTest(): 
        siteData(make24HourSiteData()),
        renewables(),
        tempsum(siteData)
    {
        // Provide some simple solar input data with 1,2,3,4 at each timestep
        siteData.solar_yields = {
            Eigen::VectorXf::Ones(24),
            Eigen::VectorXf::Ones(24) * 2,
            Eigen::VectorXf::Ones(24) * 3,
            Eigen::VectorXf::Ones(24) * 4
        };

        renewables.yield_scalars = { 1.0f, 1.0f, 1.0f, 1.0f };
    }
};

TEST_F(BasicPVTest, Initialization) {
    BasicPV pv(siteData, renewables);
    pv.AllCalcs(tempsum);
    // Check that PV output is initialized correctly
    auto pvOutput = pv.get_PV_AC_out();
    ASSERT_EQ(pvOutput.size(), 24);
    for (int i = 0; i < 24; ++i) {
        EXPECT_FLOAT_EQ(pvOutput[i], 10.0f); // 1 + 2 + 3 + 4 = 10
    }
}

TEST_F(BasicPVTest, AllCalcs) {
    BasicPV pv(siteData, renewables);
    
    // Set initial electrical demand
    tempsum.Elec_e = Eigen::VectorXf::Constant(24, 15.0f);
    
    pv.AllCalcs(tempsum);
    
    // Check that PV generation is subtracted from electrical demand
    for (int i = 0; i < 24; ++i) {
        EXPECT_FLOAT_EQ(tempsum.Elec_e[i], 5.0f); // 15 - 10 = 5
    }
}

TEST_F(BasicPVTest, Report) {
    BasicPV pv(siteData, renewables);
    ReportData report_data;

    pv.AllCalcs(tempsum);   
    pv.Report(report_data);

    // Check that PV generation is reported correctly
    ASSERT_EQ(report_data.PVdcGen.size(), 24);
    ASSERT_EQ(report_data.PVacGen.size(), 24);
    for (int i = 0; i < 24; ++i) {
        EXPECT_FLOAT_EQ(report_data.PVdcGen[i], 10.0f);
        EXPECT_FLOAT_EQ(report_data.PVacGen[i], 10.0f);
    }
}

TEST_F(BasicPVTest, ZeroGeneration) {
    // Set all solar yields to zero
    for (size_t i = 0; i < siteData.solar_yields.size(); i++) {
        siteData.solar_yields[i].setZero();
    }
    
    BasicPV pv(siteData, renewables);
    
    auto pvOutput = pv.get_PV_AC_out();
    for (int i = 0; i < 24; ++i) {
        EXPECT_FLOAT_EQ(pvOutput[i], 0.0f);
    }
}

TEST_F(BasicPVTest, ScalarEffects) {
    // Modify scalars
    renewables.yield_scalars = { 2.0f, 0.5f, 1.5f, 0.0f };

    BasicPV pv(siteData, renewables);
    pv.AllCalcs(tempsum);
    auto pvOutput = pv.get_PV_AC_out();
    for (int i = 0; i < 24; ++i) {
        EXPECT_FLOAT_EQ(pvOutput[i], 7.5f); // 2*1 + 0.5*2 + 1.5*3 + 0*4 = 7.5
    }
}
