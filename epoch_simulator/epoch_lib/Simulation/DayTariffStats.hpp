#pragma once

#include <chrono>
#include <vector>
#include <cmath>
#include <algorithm>
#include "SiteData.hpp"
#include "TaskData.hpp"

/**
* This class computes a daily average and percentile for the given import tariff
* 
* The logic has to deal with two awkward situations:
* - There might not be a whole number of timesteps in a day
* - There might not be a whole number of days in the timeseries
* 
* The one deliberate omission at the moment is that we don't ensure days start a midnight
* All of the days are groups of 24 hours starting at start_ts
* (this means we don't have to worry about time zones)
*/
class DayTariffStats
{
public:
    explicit DayTariffStats(const SiteData& siteData, size_t tariffIndex) {
        mImportTariff = siteData.import_tariffs[tariffIndex];

        // Determine the total number of days
        double totalHours = siteData.timesteps * siteData.timestep_hours;
        int totalDays = static_cast<int>(std::ceil(totalHours / 24.0));

        // We store the tariffs for each day in their own std::vector
        // then calculate the avg and percentile for each of these vectors
        std::vector<std::vector<float>> dailyValues(totalDays);

        mDayIndexForTimestep.resize(siteData.timesteps);

        for (size_t i = 0; i < siteData.timesteps; ++i) {
            double hoursSinceStart = i * siteData.timestep_hours;
            int dayIndex = static_cast<int>(std::floor(hoursSinceStart / 24.0));
            dailyValues[dayIndex].push_back(mImportTariff[i]);
            mDayIndexForTimestep[i] = dayIndex;
        }

        mDailyAverages.resize(totalDays);
        mDailyPercentiles.resize(totalDays);

        for (int day = 0; day < totalDays; ++day) {

            auto& dayValues = dailyValues[day];

            // compute the average (with a double to mitigate some floating point errors)
            double sum = std::accumulate(dayValues.begin(), dayValues.end(), 0.0);
            mDailyAverages[day] = static_cast<float>(sum) / static_cast<float>(dayValues.size());

            // compute the percentile
            int idx = static_cast<int>(std::floor(mPercentile * dayValues.size()));
            // Clamp to prevent index out of bounds
            if (idx >= static_cast<int>(dayValues.size())) {
                idx = static_cast<int>(dayValues.size()) - 1;
            }
            // this re-orders the vector but we don't care because we no longer need it
            std::nth_element(dayValues.begin(), dayValues.begin() + idx, dayValues.end());
            mDailyPercentiles[day] = dayValues[idx];
        }
    }

    /**
    * Get the daily average tariff price for the day the given timestep belongs to
    */
    float getDayAverage(size_t timestep) const
    {
        int dayIndex = mDayIndexForTimestep[timestep];
        return mDailyAverages[dayIndex];
    }

    /**
    * Get the daily percentile tariff price for the day the given timestep belongs to
    */
    float getDayPercentile(size_t timestep) const
    {
        int dayIndex = mDayIndexForTimestep[timestep];
        return mDailyPercentiles[dayIndex];
    }

private:
    year_TS mImportTariff;

    // Maps each timestep to its corresponding day index
    std::vector<int> mDayIndexForTimestep;

    // Computed daily statistics
    std::vector<float> mDailyAverages;
    std::vector<float> mDailyPercentiles;

    // Percentile to track when prices are low (default 0.25)
    const float mPercentile = 0.25f;
};
