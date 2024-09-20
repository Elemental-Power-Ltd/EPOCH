#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskData.hpp"
#include "../Definitions.hpp"

class BasicElectricVehicle
{
public:
    BasicElectricVehicle(const HistoricalData& historicalData, const TaskData& taskData) :
        mTimesteps(taskData.calculate_timesteps()),
        mFlexRatio(taskData.EV_flex),
        mAvailableEnergy_e(0),
        // Initilaise data vectors with all values to zero
        mTargetLoad_e(Eigen::VectorXf::Zero(mTimesteps)),
        mActualLoad_e(Eigen::VectorXf::Zero(mTimesteps))
    {
        mTargetLoad_e = historicalData.ev_eload_data * taskData.Fixed_load2_scalar;
    }

    void AllCalcs(TempSum_cl& TempSum) {
        // If EV charge point is not balancing, actual loads will be target
        mActualLoad_e = mTargetLoad_e;
        TempSum.Elec_e = TempSum.Elec_e + mActualLoad_e;
    }

    void StepCalc(TempSum_cl& TempSum, const float futureEnergy_e, const int t) {
        if (mTargetLoad_e[t] <= 0) {
            mActualLoad_e[t] = mTargetLoad_e[t];
        } else {
            mAvailableEnergy_e = futureEnergy_e - TempSum.Elec_e[t];
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
        TempSum.Elec_e[t] = TempSum.Elec_e[t] + mActualLoad_e[t];
    }

    void Report(FullSimulationResult & Result) {
        // report target load to allow calculation of revenue missed
        //Result.EV_targetload = mTargetLoad_e;
        //Result.EV_actualload = mActualLoad_e;
    }

private:
    const int mTimesteps;
    const float mFlexRatio;
    float mAvailableEnergy_e;

    year_TS mTargetLoad_e;
    year_TS mActualLoad_e;
};