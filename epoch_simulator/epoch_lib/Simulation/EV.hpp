#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskComponents.hpp"
#include "../Definitions.hpp"

class BasicElectricVehicle
{
public:
    BasicElectricVehicle(const HistoricalData& historicalData, const ElectricVehicles& evData) :
        mTimesteps(historicalData.timesteps),
        mFlexRatio(evData.flexible_load_ratio),
        mAvailableEnergy_e(0),
        // Initilaise data vectors with all values to zero
        mTargetLoad_e(Eigen::VectorXf::Zero(mTimesteps)),
        mActualLoad_e(Eigen::VectorXf::Zero(mTimesteps))
    {
        mTargetLoad_e = historicalData.ev_eload_data * evData.scalar_electrical_load;
    }

    void AllCalcs(TempSum& tempSum) {
        // If EV charge point is not balancing, actual loads will be target
        mActualLoad_e = mTargetLoad_e;
        tempSum.Elec_e = tempSum.Elec_e + mActualLoad_e;
    }

    void StepCalc(TempSum& tempSum, const float futureEnergy_e, const size_t t) {
        if (mTargetLoad_e[t] <= 0) {
            mActualLoad_e[t] = 0.0f;
        } else {
            mAvailableEnergy_e = futureEnergy_e - tempSum.Elec_e[t];
            // Apply a floor of flex load, a ceiling of target load or use the available energy
            if (mAvailableEnergy_e <= mTargetLoad_e[t] * mFlexRatio) {
                mActualLoad_e[t] = mTargetLoad_e[t] * mFlexRatio;
            } else if (mAvailableEnergy_e >= mTargetLoad_e[t]) {
                mActualLoad_e[t] = mTargetLoad_e[t];
            }
            else {
                mActualLoad_e[t] = mAvailableEnergy_e;
            }
        }
        tempSum.Elec_e[t] = tempSum.Elec_e[t] + mActualLoad_e[t];
    }

    void Report(ReportData& reportData) {
        // report target load to allow calculation of revenue missed
        reportData.EV_targetload = mTargetLoad_e;
        reportData.EV_actualload = mActualLoad_e;
    }

private:
    const size_t mTimesteps;
    const float mFlexRatio;
    float mAvailableEnergy_e;

    year_TS mTargetLoad_e;
    year_TS mActualLoad_e;
};