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

    void Report(FullSimulationResult& Result) const {
        // NEED TO ADD HEATPUMP RESULTS
        //result.HeatPump_elec_load = mHeatPump.DHWload_e + mHeatPump.CHload_e;
        //result.HeatPump_DHWoutput = mHeatPump.DHWout_h;
        //result.HeatPump_CHoutput = mHeatPump.CHout_h;
        //result.HeatPump_UsedAmbientHeat = mHeatPump.FreeHeat_h;
    }

private:
    AmbientHeatPump mHeatPump;
};