#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskData.hpp"
#include "../Definitions.hpp"

class EVbasic_cl
{
public:
    EVbasic_cl(const HistoricalData& historicalData, const TaskData& taskData) :
        // Initialise Persistent Values
        TScount(taskData.calculate_timesteps()),	// Used in init & functions
        FlexRatio(taskData.EV_flex),
        AvailEnergy_e(0),
        // Initilaise data vectors with all values to zero
        TargetLoad_e(Eigen::VectorXf::Zero(TScount)),
        ActualLoad_e(Eigen::VectorXf::Zero(TScount))
    {
        TargetLoad_e = historicalData.ev_eload_data * taskData.Fixed_load2_scalar;
    }

    void AllCalcs(TempSum_cl& TempSum) {
        // If EV charge point is not balancing, actual loads will be target
        ActualLoad_e = TargetLoad_e;
        TempSum.Elec_e = TempSum.Elec_e + ActualLoad_e;
    }

    void StepCalc(TempSum_cl& TempSum, const float FutureEnergy_e, const int t) {
        if (TargetLoad_e[t] <= 0) {
            ActualLoad_e[t] = TargetLoad_e[t];
        } else {
            AvailEnergy_e = FutureEnergy_e - TempSum.Elec_e[t];
            // Apply a floor of flex load, a ceiling of target load or use the available energy
            if (AvailEnergy_e <= TargetLoad_e[t] * FlexRatio) {
                ActualLoad_e[t] = TargetLoad_e[t] * FlexRatio;
            } else if (AvailEnergy_e >= TargetLoad_e[t]) {
                ActualLoad_e[t] = TargetLoad_e[t];
            }
            else {
                ActualLoad_e[t] = AvailEnergy_e;
            }
        }
        TempSum.Elec_e[t] = TempSum.Elec_e[t] + ActualLoad_e[t];
    }

    void Report(FullSimulationResult & Result) {
        // report target load to allow calculation of revenue missed
        //Result.EV_targetload = TargetLoad_e;
        //Result.EV_actualload = ActualLoad_e;
    }

private:
    const int TScount;
    const float FlexRatio;
    float AvailEnergy_e;

    year_TS TargetLoad_e;
    year_TS ActualLoad_e;
};