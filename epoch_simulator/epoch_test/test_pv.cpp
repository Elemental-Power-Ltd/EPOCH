
#include <gtest/gtest.h>
#include "../epoch_lib/Definitions.hpp"
#include "../epoch_lib/Simulation/PV.hpp"
#include "../epoch_lib/Simulation/TaskData.hpp"

#include <Eigen/Core>

class BasicPVTest : public ::testing::Test {
protected:
    HistoricalData historicalData;
    TaskData taskData;
    TempSum tempsum;

    BasicPVTest() : taskData ( /* years_val = */ 1.0f / 365.0f, 
        /*days_val*/ 1.0f, 
        /*hours_val*/ 24.0f, 
        /*timestep_hours_val*/ 1.0f, 
        /*timewindow_val*/24.0), historicalData (), tempsum(taskData) {
        // Set up test data

        taskData.ScalarRG1 = 1.0f;
        taskData.ScalarRG2 = 1.0f;
        taskData.ScalarRG3 = 1.0f;
        taskData.ScalarRG4 = 1.0f;
        
        historicalData = HistoricalData();
        historicalData.RGen_data_1 = Eigen::VectorXf::Ones(24);
        historicalData.RGen_data_2 = Eigen::VectorXf::Ones(24) * 2;
        historicalData.RGen_data_3 = Eigen::VectorXf::Ones(24) * 3;
        historicalData.RGen_data_4 = Eigen::VectorXf::Ones(24) * 4;
    }
};

TEST_F(BasicPVTest, Initialization) {
    BasicPV pv(historicalData, taskData);
    pv.AllCalcs(tempsum);
    // Check that PV output is initialized correctly
    auto pvOutput = pv.get_PV_AC_out();
    ASSERT_EQ(pvOutput.size(), 24);
    for (int i = 0; i < 24; ++i) {
        EXPECT_FLOAT_EQ(pvOutput[i], 10.0f); // 1 + 2 + 3 + 4 = 10
    }
}

TEST_F(BasicPVTest, AllCalcs) {
    BasicPV pv(historicalData, taskData);
    
    // Set initial electrical demand
    tempsum.Elec_e = Eigen::VectorXf::Constant(24, 15.0f);
    
    pv.AllCalcs(tempsum);
    
    // Check that PV generation is subtracted from electrical demand
    for (int i = 0; i < 24; ++i) {
        EXPECT_FLOAT_EQ(tempsum.Elec_e[i], 5.0f); // 15 - 10 = 5
    }
}

TEST_F(BasicPVTest, Report) {
    BasicPV pv(historicalData, taskData);
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
    // Set all historical data to zero
    historicalData.RGen_data_1.setZero();
    historicalData.RGen_data_2.setZero();
    historicalData.RGen_data_3.setZero();
    historicalData.RGen_data_4.setZero();
    
    BasicPV pv(historicalData, taskData);
    
    auto pvOutput = pv.get_PV_AC_out();
    for (int i = 0; i < 24; ++i) {
        EXPECT_FLOAT_EQ(pvOutput[i], 0.0f);
    }
}

TEST_F(BasicPVTest, ScalarEffects) {
    // Modify scalars
    taskData.ScalarRG1 = 2.0f;
    taskData.ScalarRG2 = 0.5f;
    taskData.ScalarRG3 = 1.5f;
    taskData.ScalarRG4 = 0.0f;
    
    BasicPV pv(historicalData, taskData);
    pv.AllCalcs(tempsum);
    auto pvOutput = pv.get_PV_AC_out();
    for (int i = 0; i < 24; ++i) {
        EXPECT_FLOAT_EQ(pvOutput[i], 7.5f); // 2*1 + 0.5*2 + 1.5*3 + 0*4 = 7.5
    }
}