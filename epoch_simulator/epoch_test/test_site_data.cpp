#include <gtest/gtest.h>
#include "test_helpers.hpp"
#include "../epoch_lib/Simulation/SiteData.hpp"

TEST(SiteDataValidationTest, ValidSiteData) {
    // should produce a valid SiteData
    EXPECT_NO_THROW({
        auto sd = make24HourSiteData();
        });
}

TEST(SiteDataValidationTest, InvalidStartEndTimestamps) {
    auto sdBase = make24HourSiteData();
    // Make a valid 24-hour SiteData, then swap the timestamps
    EXPECT_THROW({
        SiteData broken(
            sdBase.end_ts, // start_ts > end_ts
            sdBase.start_ts,
            TaskData{},
            sdBase.building_eload,
            sdBase.building_hload,
            sdBase.ev_eload,
            sdBase.dhw_demand,
            sdBase.air_temperature,
            sdBase.grid_co2,
            sdBase.solar_yields,
            sdBase.import_tariffs,
            sdBase.fabric_interventions,
            sdBase.ashp_input_table,
            sdBase.ashp_output_table
        );
        }, std::runtime_error);
}

TEST(SiteDataValidationTest, MismatchedVectorSizes) {
    // Check we can't construct a SiteData with a mismatched vector
    // (hload as an example)
    auto sdBase = make24HourSiteData();
    auto badHLoad = Eigen::VectorXf::Ones(25);
    EXPECT_THROW({
        SiteData broken(
            sdBase.start_ts,
            sdBase.end_ts,
            TaskData{},
            sdBase.building_eload,
            badHLoad, // wrong size
            sdBase.ev_eload,
            sdBase.dhw_demand,
            sdBase.air_temperature,
            sdBase.grid_co2,
            sdBase.solar_yields,
            sdBase.import_tariffs,
            sdBase.fabric_interventions,
            sdBase.ashp_input_table,
            sdBase.ashp_output_table
        );
        }, std::runtime_error);
}

TEST(SiteDataValidationTest, MismatchedSolarYields) {
    // check we also can't pass in mismatched solar yields
    auto sdBase = make24HourSiteData();
    auto badSolar = sdBase.solar_yields;
    badSolar[0] = Eigen::VectorXf::Ones(23);

    EXPECT_THROW({
        SiteData broken(
            sdBase.start_ts,
            sdBase.end_ts,
            TaskData{},
            sdBase.building_eload,
            sdBase.building_hload,
            sdBase.ev_eload,
            sdBase.dhw_demand,
            sdBase.air_temperature,
            sdBase.grid_co2,
            badSolar, // mismatch
            sdBase.import_tariffs,
            sdBase.fabric_interventions,
            sdBase.ashp_input_table,
            sdBase.ashp_output_table
        );
        }, std::runtime_error);
}

TEST(SiteDataValidationTest, EmptyImportTariffs) {
    // Check that we can't provide 0 import tariffs
    auto sdBase = make24HourSiteData();
    std::vector<year_TS> noTariffs{};

    EXPECT_THROW({
        SiteData broken(
            sdBase.start_ts,
            sdBase.end_ts,
            TaskData{},
            sdBase.building_eload,
            sdBase.building_hload,
            sdBase.ev_eload,
            sdBase.dhw_demand,
            sdBase.air_temperature,
            sdBase.grid_co2,
            sdBase.solar_yields,
            noTariffs, // empty
            sdBase.fabric_interventions,
            sdBase.ashp_input_table,
            sdBase.ashp_output_table
        );
        }, std::runtime_error);
}

TEST(SiteDataValidationTest, MismatchedImportTariffs) {
    // Check tariff lengths can't be mismatched
    auto sdBase = make24HourSiteData();
    auto badTariffs = sdBase.import_tariffs;
    badTariffs[0] = Eigen::VectorXf::Ones(23);

    EXPECT_THROW({
        SiteData broken(
            sdBase.start_ts,
            sdBase.end_ts,
            TaskData{},
            sdBase.building_eload,
            sdBase.building_hload,
            sdBase.ev_eload,
            sdBase.dhw_demand,
            sdBase.air_temperature,
            sdBase.grid_co2,
            sdBase.solar_yields,
            badTariffs, // mismatch
            sdBase.fabric_interventions,
            sdBase.ashp_input_table,
            sdBase.ashp_output_table
        );
        }, std::runtime_error);
}

TEST(SiteDataValidationTest, MismatchedFabricInterventions) {
    // also check fabric interventions
    auto sdBase = make24HourSiteData();
    auto fi = sdBase.fabric_interventions[0];
    fi.reduced_hload = Eigen::VectorXf::Ones(25); // mismatch
    std::vector<FabricIntervention> badInterventions{ fi };

    EXPECT_THROW({
        SiteData broken(
            sdBase.start_ts,
            sdBase.end_ts,
            TaskData{},
            sdBase.building_eload,
            sdBase.building_hload,
            sdBase.ev_eload,
            sdBase.dhw_demand,
            sdBase.air_temperature,
            sdBase.grid_co2,
            sdBase.solar_yields,
            sdBase.import_tariffs,
            badInterventions, // mismatch
            sdBase.ashp_input_table,
            sdBase.ashp_output_table
        );
        }, std::runtime_error);
}

TEST(SiteDataValidationTest, MismatchedLookupTables) {
    // Check we don't accept different sized heatpump tables
    auto sdBase = make24HourSiteData();

    Eigen::MatrixXf badIn(2, 2);
    badIn << 1, 2, 3, 4;

    Eigen::MatrixXf badOut(3, 3);
    badOut << 1, 2, 3, 4, 5, 6, 7, 8, 9;

    EXPECT_THROW({
        SiteData broken(
            sdBase.start_ts,
            sdBase.end_ts,
            TaskData{},
            sdBase.building_eload,
            sdBase.building_hload,
            sdBase.ev_eload,
            sdBase.dhw_demand,
            sdBase.air_temperature,
            sdBase.grid_co2,
            sdBase.solar_yields,
            sdBase.import_tariffs,
            sdBase.fabric_interventions,
            badIn, // mismatch
            badOut // mismatch
        );
        }, std::runtime_error);
}

TEST(SiteDataValidationTest, TooSmallTables) {
    // Check the heatpump table must be at least 2x2
    auto sdBase = make24HourSiteData();
    Eigen::MatrixXf tooSmall(1, 1);
    tooSmall << 42.0f;

    EXPECT_THROW({
        SiteData broken(
            sdBase.start_ts,
            sdBase.end_ts,
            TaskData{},
            sdBase.building_eload,
            sdBase.building_hload,
            sdBase.ev_eload,
            sdBase.dhw_demand,
            sdBase.air_temperature,
            sdBase.grid_co2,
            sdBase.solar_yields,
            sdBase.import_tariffs,
            sdBase.fabric_interventions,
            tooSmall,
            tooSmall
        );
        }, std::runtime_error);
}
