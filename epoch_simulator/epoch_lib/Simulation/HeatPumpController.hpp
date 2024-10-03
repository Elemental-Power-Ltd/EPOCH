#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "ASHPambient.hpp"
#include "TempSum.hpp"

#include "TaskData.hpp"
#include "../Definitions.hpp"

class AmbientHeatPumpController
{
public:
    AmbientHeatPumpController(const HistoricalData& historicalData, const TaskData& taskData) :
        // Initialise Persistent Values
        mHeatPump(historicalData, taskData)
    {}

    void AllCalcs(TempSum& tempSum) {
        mHeatPump.AllCalcs(tempSum);
    }

    void StepCalc(TempSum& tempSum, const float futureEnergy_e, const int t) {
        // Set Electricty Budget for ASHP
        float heatPumpBudget_e;
        if (futureEnergy_e <= 0) {
            heatPumpBudget_e = 0;
        } else {
            heatPumpBudget_e = futureEnergy_e;
        }
        mHeatPump.StepCalc(tempSum, heatPumpBudget_e, t);
    }

    void Report(FullSimulationResult& result) const {
        // NEED TO ADD HEATPUMP RESULTS
        //result.HeatPump_elec_load = mHeatPump.mDHWload_e + mHeatPump.mCHload_e;
        //result.HeatPump_DHWoutput = mHeatPump.mDHWout_h;
        //result.HeatPump_CHoutput = mHeatPump.mCHout_h;
        //result.HeatPump_UsedAmbientHeat = mHeatPump.mFreeHeat_h;


        // TODO - FIXME
        // The way that FullSimulationResult is structured, we assume that we always have all of the vectors
        // The following vectors are specific to a data centre with an ASHP (which we don't have in this case)
        // So we write them as 0 vectors mimicking the length of the other results
        // (consider changing reporting from a struct with fixed vectors to a map of String->year_TS?

        // EVEN BIGGER HACK
        // assume that heatload has already been written (it has)
        // and use that to determine the size of these vectors
        int timesteps = result.Heatload.size();

        result.Data_centre_target_load = Eigen::VectorXf::Zero(timesteps);
        result.Data_centre_actual_load = Eigen::VectorXf::Zero(timesteps);
        result.Data_centre_target_heat = Eigen::VectorXf::Zero(timesteps);
        result.Data_centre_available_hot_heat = Eigen::VectorXf::Zero(timesteps);
    }

private:
    AmbientHeatPump mHeatPump;
};