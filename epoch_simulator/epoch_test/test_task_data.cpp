#include <gtest/gtest.h>
#include "../epoch_lib/Simulation/TaskData.hpp"
#include <cmath>

class TaskDataTest : public ::testing::Test {
protected:
    TaskData taskData = TaskData();
};

TEST_F(TaskDataTest, DefaultInitialization) {
    EXPECT_FLOAT_EQ(taskData.years, 1.0f);
    EXPECT_FLOAT_EQ(taskData.days, 365.0f);
    EXPECT_FLOAT_EQ(taskData.hours, 8760.0f);
    EXPECT_FLOAT_EQ(taskData.timestep_hours, 1.0f);
    EXPECT_FLOAT_EQ(taskData.timewindow, 8760.0f);
}

TEST_F(TaskDataTest, CustomInitialization) {
    TaskData customTaskData(2.0f, 730.0f, 17520.0f, 0.5f, 4380.0f);
    EXPECT_FLOAT_EQ(customTaskData.years, 2.0f);
    EXPECT_FLOAT_EQ(customTaskData.days, 730.0f);
    EXPECT_FLOAT_EQ(customTaskData.hours, 17520.0f);
    EXPECT_FLOAT_EQ(customTaskData.timestep_hours, 0.5f);
    EXPECT_FLOAT_EQ(customTaskData.timewindow, 4380.0f);
}

TEST_F(TaskDataTest, SetParamFloat) {
    float initialScalarRG1 = taskData.ScalarRG1;
    float initialGridImport = taskData.GridImport;
    auto successful_set = taskData.set_param_float("ScalarRG1", 100.0f);
    EXPECT_TRUE(successful_set);
    EXPECT_FLOAT_EQ(*taskData.param_map_float["ScalarRG1"], 100.0f);
    EXPECT_NE(taskData.ScalarRG1, initialScalarRG1);

    auto grid_import_success = taskData.set_param_float("GridImport", 200.0f);
    EXPECT_TRUE(grid_import_success);
    EXPECT_FLOAT_EQ(taskData.GridImport, 200.0f);
    EXPECT_NE(taskData.GridImport, initialGridImport);

    // Test setting a non-existent parameter
    testing::internal::CaptureStderr();
    auto non_existent_success = taskData.set_param_float("NonExistentParam", 300.0f);
    EXPECT_FALSE(non_existent_success);
}

TEST_F(TaskDataTest, SetParamInt) {
    taskData.set_param_int("s7_EV_CP_number", 5);
    EXPECT_EQ(taskData.s7_EV_CP_number, 5);

    taskData.set_param_int("ASHP_HSource", 2);
    EXPECT_EQ(taskData.ASHP_HSource, 2);

    // Test setting a non-existent parameter
    taskData.set_param_int("NonExistentParam", 10);
}

TEST_F(TaskDataTest, CalculateTimesteps) {
    // Default initialization
    EXPECT_EQ(taskData.calculate_timesteps(), 8760);

    // Custom timewindow and timestep_hours
    taskData.set_param_float("timewindow", 24.0f);
    taskData.set_param_float("timestep_hours", 0.5f);
    EXPECT_EQ(taskData.calculate_timesteps(), 48);

    // Test with non-integer result (should round down)
    taskData.set_param_float("timewindow", 25.0f);
    taskData.set_param_float("timestep_hours", 0.6f);
    EXPECT_EQ(taskData.calculate_timesteps(), 41);  // 25 / 0.6 = 41.6666... should round down to 41
}

TEST_F(TaskDataTest, PrintParam) {
    // Test print_param_float
    testing::internal::CaptureStdout();
    taskData.print_param_float("ScalarRG1");
    std::string output = testing::internal::GetCapturedStdout();
    EXPECT_TRUE(output.find("Parameter ScalarRG1 = 599.2") != std::string::npos);

    // Test print_param_int
    testing::internal::CaptureStdout();
    taskData.print_param_int("s7_EV_CP_number");
    output = testing::internal::GetCapturedStdout();
    EXPECT_TRUE(output.find("Parameter s7_EV_CP_number = 0") != std::string::npos);
}