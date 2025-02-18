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

TEST_F(TaskDataTest, CalculateEmptiesEqualHash) {
    TaskData td1 = {};
    TaskData td2 = {};
    auto hasher = std::hash<TaskData>{};
    EXPECT_EQ(hasher(td1), hasher(td2));

    EXPECT_EQ(td1, td2);
}

TEST_F(TaskDataTest, CalculateNonEmptiesEqualHash) {
    TaskData td1 = {};
    TaskData td2 = {};
    td1.building = {1.0, 1.0, 0};
    td2.building = {2.0, 1.0, 0};
    auto hasher = std::hash<TaskData>{};
    EXPECT_NE(hasher(td1), hasher(td2));

    EXPECT_NE(td1, td2);
}