#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "ASHPambient.hpp"
#include "TempSum.hpp"

#include "SiteData.hpp"
#include "TaskComponents.hpp"
#include "../Definitions.hpp"

class AmbientHeatPumpController
{
public:
    AmbientHeatPumpController(const SiteData& siteData, const HeatPumpData& hp, bool suppliesDHW) :
        // Initialise Persistent Values
        mHeatPump(siteData, hp, suppliesDHW)
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
        reportData.ASHP_elec_load = mHeatPump.mDHWload_e + mHeatPump.mCHload_e;
        reportData.ASHP_DHW_output = mHeatPump.mDHWout_h;
        reportData.ASHP_CH_output = mHeatPump.mCHout_h;
        reportData.ASHP_free_heat = mHeatPump.mFreeHeat_h;
    }

private:
    AmbientHeatPump mHeatPump;
};