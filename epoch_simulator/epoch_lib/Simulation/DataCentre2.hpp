#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "ASHP.hpp"
#include "TempSum.hpp"

#include "TaskData.hpp"
#include "../Definitions.hpp"

class DataCentreNoHot
{
public:
    DataCentreNoHot(const HistoricalData& historicalData, const TaskData& taskData) :
        // Initialise Persistent Values
        mTimesteps(taskData.calculate_timesteps()),
        // Mode: 1=Target, 2=Price, 3=Carbon
        mOptimisationMode(1),
        // Max kWh per TS
        mDataCentreMaxLoad_e(taskData.Flex_load_max* taskData.timestep_hours),

        mTargetLoad_e(Eigen::VectorXf::Zero(mTimesteps)),
        mActualLoad_e(Eigen::VectorXf::Zero(mTimesteps)),
    {
        // Calculate Target Load based on the optimisation mode: 1=Target (default), 2=Price, 3=Carbon
        switch (mOptimisationMode) {
        case 2: // Price minimisation mode
            // placeholder for lookahead supplier price mode
        case 3: // Carbon minimisation mode
            // placholder for lookahead grid carbon mode
        default: // Target Power Mode (initially Max Load)							
            mTargetLoad_e.setConstant(mDataCentreMaxLoad_e);
        }
    }

    void AllCalcs(TempSum& tempSum) {
        // If Data Centre  is not balancing, actual loads will be target
        mActualLoad_e = mTargetLoad_e;
        // update Temp Energy Balances
        tempSum.Elec_e += mActualLoad_e;
    }

    void StepCalc(TempSum& tempSum, const float futureEnergy_e, const int t) {
        if (futureEnergy_e <= 0) {
            mActualLoad_e[t] = 0;
        }
        else if (futureEnergy_e > mTargetLoad_e[t]) {
            // Set Load & Budget to maximums
            mActualLoad_e[t] = mTargetLoad_e[t];
            }
        else {
            // Reduce Load & Budget to largest without breaching FutureEnergy
            mActualLoad_e[t] = futureEnergy_e;
         }
        // Update Temp Energy Balances
        tempSum.Elec_e[t] += mActualLoad_e[t];
    }

    float getTargetLoad(int timestep) {
        return mTargetLoad_e[timestep];
    }

    void Report(FullSimulationResult& result) const {
        result.Data_centre_target_load = mTargetLoad_e;
        result.Data_centre_actual_load = mActualLoad_e;
    }

private:
    const int mTimesteps;
    const int mOptimisationMode;
    const float mDataCentreMaxLoad_e;

    year_TS mTargetLoad_e;
    year_TS mActualLoad_e;
};