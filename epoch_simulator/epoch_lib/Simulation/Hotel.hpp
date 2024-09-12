#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskData.hpp"
#include "../Definitions.hpp"

class Hotel_cl {

public:
    Hotel_cl(const HistoricalData& historicalData, const TaskData& taskData) :
        TScount(taskData.calculate_timesteps()),	// Used in init & functions
        // Initilaise data vectors with all values to zero
        TargetLoad_e(Eigen::VectorXf::Zero(TScount)),
        TargetHeat_h(Eigen::VectorXf::Zero(TScount)),
        //TargetPool_h(Eigen::VectorXf::Zero(BattData.TS_max))
        TargetDHW_h(Eigen::VectorXf::Zero(TScount))
    {
        TargetLoad_e = historicalData.hotel_eload_data * taskData.Fixed_load1_scalar;
        TargetHeat_h = historicalData.heatload_data;
        // Leave DHW as Zero for now
    }

    year_TS ElecLoad() const { return TargetLoad_e; }

    year_TS HeatLoad() const { return TargetHeat_h; }

    year_TS DHWLoad() const { return TargetDHW_h; }

    void Report(FullSimulationResult& Result) {
        // report target load to allow calculation of revenue missed
        //Result.Hotel_load = TargetLoad_e;
        //Result.Heatload = TargetHeat_h + TargetDHW_h;
    }

private:
    const int TScount;

    year_TS TargetLoad_e;
    year_TS TargetHeat_h;
    year_TS TargetDHW_h;
    //year_TS TargetPool_h;
};