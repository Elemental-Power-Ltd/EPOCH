#include <gtest/gtest.h>
#include "../epoch_lib/Simulation/TaskData.hpp"
#include "../epoch_lib/Simulation/Costs/Capex.hpp"
#include <cmath>

class TaskDataTest : public ::testing::Test {
protected:
    TaskData taskData = TaskData();
};

TEST_F(TaskDataTest, CalculateEmptyCapex) {
    // an empty TaskData should have 0 CAPEX
    TaskData emptyTask = {};
    auto breakdown = calculate_capex(emptyTask);
    EXPECT_EQ(breakdown.total_capex, 0.0f);
}
