#include <gtest/gtest.h>
#include <stdexcept>

#include "test_helpers.hpp"
#include "../epoch_lib/Simulation/DayTariffStats.hpp"

TEST(TariffStats, FixedPrice) {
	// Contains a tariff of Eigen::Ones
	auto sd = make24HourSiteData();

	DayTariffStats tariffStats{ sd, 0 };

	EXPECT_EQ(tariffStats.getDayAverage(0), 1);
	EXPECT_EQ(tariffStats.getDayPercentile(0), 1);
}

TEST(TariffStats, DynamicPrice) {

	auto sd = make24HourSiteData();

	// SiteData is normally Const and we shouldn't modify it, 
	// but it makes for a simple test construction

	// add some higher prices for the second tariff
	sd.import_tariffs[1][9] = 3;
	sd.import_tariffs[1][10] = 3;
	sd.import_tariffs[1][11] = 3;
	sd.import_tariffs[1][12] = 3;
	sd.import_tariffs[1][13] = 3;
	sd.import_tariffs[1][14] = 3;

	size_t tariff_index = 1;
	DayTariffStats tariffStats{ sd, tariff_index };

	// Any tariff in the same day [0-23] should have the same values
	EXPECT_EQ(tariffStats.getDayAverage(0), tariffStats.getDayAverage(23));
	EXPECT_EQ(tariffStats.getDayPercentile(0), tariffStats.getDayPercentile(23));

	// average should now be greater than 1
	EXPECT_GT(tariffStats.getDayAverage(12), 1);

	// We've not changed enough values to shift the 25th percentile
	EXPECT_EQ(tariffStats.getDayPercentile(7), 1);
}

TEST(TariffStats, Test25Hours) {
	// test a SiteData where the total timesteps don't fit into a multiple of 24h

	auto sd25 = makeNHourSiteData(25);
	// we'll use the tariff at index 1 and make some modifications
	size_t tariff_index = 1;
	sd25.import_tariffs[tariff_index][24] = 100;

	DayTariffStats tariffStats{ sd25, tariff_index };

	// we haven't changed the first 24h
	EXPECT_EQ(tariffStats.getDayAverage(0), 1);
	// 25th and final timestep should have an average of 100
	EXPECT_EQ(tariffStats.getDayAverage(24), 100);
}

TEST(TariffStats, Test23Hours) {
	// test a SiteData where the total timesteps don't fit into a multiple of 24h

	auto sd23 = makeNHourSiteData(23);
	size_t tariff_index = 1;

	DayTariffStats tariffStats{ sd23, tariff_index };
	EXPECT_EQ(tariffStats.getDayAverage(22), 1);
}

TEST(TariffStats, TimestepsNonHourly) {
	// test a SiteData where each timestep is not a clean number of hours

	// make a base SiteData with 48 values
	auto sdBase = makeNHourSiteData(48);

	auto newEnd = sdBase.start_ts + std::chrono::hours(53);



	// change the start_ts and end_ts 
	SiteData sd(
		sdBase.start_ts,
		newEnd,
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

	// 48 timesteps span 53 hours
	// each timestep is 1.104166... hours long

	// 24 / (53/48) = 21.7
	// the first 21 timesteps belong to the first day

	// make a modification to day 2
	sd.import_tariffs[0][22] = 100;

	DayTariffStats tariffStats{ sd, 0 };

	// We expect the first day to be unchanged
	EXPECT_EQ(tariffStats.getDayAverage(0), 1.0f);
	EXPECT_EQ(tariffStats.getDayPercentile(0), 1.0f);

	// We expect the second day to have a higher average
	// but percentile will be unchanged
	EXPECT_GT(tariffStats.getDayAverage(22), 1.0f);
	EXPECT_EQ(tariffStats.getDayPercentile(22), 1.0f);

	// We expect the third day to be unchanged
	EXPECT_EQ(tariffStats.getDayAverage(47), 1.0f);
	EXPECT_EQ(tariffStats.getDayPercentile(47), 1.0f);

}