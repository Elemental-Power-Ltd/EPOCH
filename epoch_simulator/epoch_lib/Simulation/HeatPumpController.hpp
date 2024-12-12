#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "ASHPambient.hpp"
#include "TempSum.hpp"

#include "TaskComponents.hpp"
#include "../Definitions.hpp"

class AmbientHeatPumpController
{
public:
    AmbientHeatPumpController(const HistoricalData& historicalData, const HeatPumpData& hp) :
        // Initialise Persistent Values
        mHeatPump(historicalData, hp)
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

    void Report(ReportData& reportData) const {
        // TODO - NEED TO ADD HEATPUMP RESULTS
        //result.HeatPump_elec_load = mHeatPump.mDHWload_e + mHeatPump.mCHload_e;
        //result.HeatPump_DHWoutput = mHeatPump.mDHWout_h;
        //result.HeatPump_CHoutput = mHeatPump.mCHout_h;
        //result.HeatPump_UsedAmbientHeat = mHeatPump.mFreeHeat_h;
    }

private:
    AmbientHeatPump mHeatPump;
};