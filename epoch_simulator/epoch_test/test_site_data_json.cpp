#include <chrono>
#include <string>

#include <Eigen/Dense>
#include <gtest/gtest.h>
#include <nlohmann/json.hpp>

#include "../epoch_lib/Simulation/SiteData.hpp"
#include "../epoch_lib/io/FileHandling.hpp"
#include "../epoch_lib/io/SiteDataJson.hpp"
#include "test_helpers.hpp"

using json = nlohmann::json;

/**
 * Helper function to compare two Eigen::VectorXf with Google Test,
 * checking that they have the same size and matching float elements.
 */
void expectEigenVectorsEqual(const Eigen::VectorXf& a, const Eigen::VectorXf& b) {
    ASSERT_EQ(a.size(), b.size()) << "Eigen vectors differ in size.";
    for (int i = 0; i < a.size(); i++) {
        EXPECT_FLOAT_EQ(a(i), b(i)) << "Mismatch at index " << i;
    }
}

/**
 * Test for round-trip FabricIntervention JSON serialization
 */
TEST(FabricInterventionTest, RoundTrip)
{
    // 1. Construct a FabricIntervention
    FabricIntervention fi;
    fi.cost = 100.0f;
    fi.reduced_hload = toEigen(std::vector<float>{1.0f, 2.0f, 3.0f, 4.0f});

    // 2. Serialize to JSON
    json j = fi;

    // 3. Deserialize back
    FabricIntervention fi2 = j.get<FabricIntervention>();

    // 4. Compare
    EXPECT_FLOAT_EQ(fi.cost, fi2.cost);

    // Compare vectors
    expectEigenVectorsEqual(fi.reduced_hload, fi2.reduced_hload);
}

/**
 * Test for round-trip SiteData JSON serialization
 */
TEST(SiteDataTest, RoundTrip)
{
    // 1. Construct a SiteData
    SiteData sd = make24HourSiteData();

    // 2. Serialize to JSON
    json j = sd;

    // 3. Deserialize back
    SiteData sd2 = j.get<SiteData>();

    // 4. Compare fields

    // Compare timestamps
    EXPECT_EQ(sd.start_ts, sd2.start_ts);
    EXPECT_EQ(sd.end_ts, sd2.end_ts);

    // Compare timestep interval
    EXPECT_EQ(sd.timestep_interval_s.count(), sd2.timestep_interval_s.count());

    // Compare single-dimension vectors
    expectEigenVectorsEqual(sd.building_eload, sd2.building_eload);
    expectEigenVectorsEqual(sd.building_hload, sd2.building_hload);
    expectEigenVectorsEqual(sd.ev_eload, sd2.ev_eload);
    expectEigenVectorsEqual(sd.dhw_demand, sd2.dhw_demand);
    expectEigenVectorsEqual(sd.air_temperature, sd2.air_temperature);
    expectEigenVectorsEqual(sd.grid_co2, sd2.grid_co2);

    // Compare vectors of vectors
    ASSERT_EQ(sd.solar_yields.size(), sd2.solar_yields.size());
    for (size_t i = 0; i < sd.solar_yields.size(); i++) {
        expectEigenVectorsEqual(sd.solar_yields[i], sd2.solar_yields[i]);
    }
    ASSERT_EQ(sd.import_tariffs.size(), sd2.import_tariffs.size());
    for (size_t i = 0; i < sd.import_tariffs.size(); i++) {
        expectEigenVectorsEqual(sd.import_tariffs[i], sd2.import_tariffs[i]);
    }

    // Compare fabric interventions
    ASSERT_EQ(sd.fabric_interventions.size(), sd2.fabric_interventions.size());
    for (size_t i = 0; i < sd.fabric_interventions.size(); i++) {
        EXPECT_FLOAT_EQ(sd.fabric_interventions[i].cost, sd2.fabric_interventions[i].cost);
        expectEigenVectorsEqual(
            sd.fabric_interventions[i].reduced_hload,
            sd2.fabric_interventions[i].reduced_hload
        );
    }

    // Compare heat pump tables
    EXPECT_EQ(sd.ashp_input_table.rows(), sd2.ashp_input_table.rows());
    EXPECT_EQ(sd.ashp_input_table.cols(), sd2.ashp_input_table.cols());
    for (int r = 0; r < sd.ashp_input_table.rows(); r++) {
        for (int c = 0; c < sd.ashp_input_table.cols(); c++) {
            EXPECT_FLOAT_EQ(sd.ashp_input_table(r, c),
                sd2.ashp_input_table(r, c));
        }
    }

    EXPECT_EQ(sd.ashp_output_table.rows(), sd2.ashp_output_table.rows());
    EXPECT_EQ(sd.ashp_output_table.cols(), sd2.ashp_output_table.cols());
    for (int r = 0; r < sd.ashp_output_table.rows(); r++) {
        for (int c = 0; c < sd.ashp_output_table.cols(); c++) {
            EXPECT_FLOAT_EQ(sd.ashp_output_table(r, c),
                sd2.ashp_output_table(r, c));
        }
    }
}


TEST(SiteDataTest, FromFile)
{
    // This file contains {1,2,3,4} for each timeseries
    auto p = std::filesystem::path("./test_files/siteData.json");

    auto sd = readSiteData(p);


    // arbitrarily check a few properties we know about this file
    EXPECT_EQ(sd.grid_co2.size(), 4);
    EXPECT_EQ(sd.grid_co2[0], 1.0f);

    EXPECT_EQ(sd.solar_yields.size(), 3);
    EXPECT_EQ(sd.solar_yields[2].size(), 4);
    EXPECT_EQ(sd.solar_yields[2][3], 4.0f);

    EXPECT_EQ(sd.fabric_interventions.size(), 2);
    EXPECT_EQ(sd.fabric_interventions[0].cost, 10000);

    EXPECT_EQ(sd.ashp_input_table.cols(), 2);
    EXPECT_EQ(sd.ashp_input_table.rows(), 2);
    EXPECT_EQ(sd.ashp_input_table(1,1), 6.0f);
}
