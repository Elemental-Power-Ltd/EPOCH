#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskData.hpp"
#include "../Definitions.hpp"

class Hotel {

public:
    Hotel(const HistoricalData& historicalData, const TaskData& taskData) :
        mTimesteps(taskData.calculate_timesteps()),	// Used in init & functions
        // Initilaise data vectors with all values to zero
        mTargetLoad_e(historicalData.hotel_eload_data* taskData.Fixed_load1_scalar),
        mTargetHeat_h(historicalData.heatload_data),
        // Leave DHW as Zero for now
        mTargetDHW_h(Eigen::VectorXf::Zero(mTimesteps))

        //TargetPool_h(Eigen::VectorXf::Zero(BattData.TS_max))
    {
    }

    year_TS ElecLoad() const { return mTargetLoad_e; }

    year_TS HeatLoad() const { return mTargetHeat_h; }

    year_TS DHWLoad() const { return mTargetDHW_h; }

    void Report(FullSimulationResult& Result) {
        // report target load to allow calculation of revenue missed
        Result.Hotel_load = mTargetLoad_e;
        Result.Heatload = mTargetHeat_h + mTargetDHW_h;
    }

private:
    const int mTimesteps;

    year_TS mTargetLoad_e;
    year_TS mTargetHeat_h;
    year_TS mTargetDHW_h;
    //year_TS TargetPool_h;
};