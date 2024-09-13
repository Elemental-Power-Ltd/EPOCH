#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "ASHP.hpp"
#include "TempSum.hpp"

#include "TaskData.hpp"
#include "../Definitions.hpp"

class DataC_ASHP_cl
{
public:
    DataC_ASHP_cl(const HistoricalData& historicalData, const TaskData& taskData, ASHPhot_cl extASHPhot) :
        // Initialise Persistent Values
        ptrASHPhot(&extASHPhot),
        TScount(taskData.calculate_timesteps()),
        OptMode(1), // Mode: 1=Target, 2=Price, 3=Carbon
        DataCmaxLoad_e(taskData.Flex_load_max* taskData.timestep_hours),    // Max kWh per TS
        HeatScalar(taskData.ScalarHYield),    // Percentage of waste heat captured for ASHP
        // Initilaise results data vectors with all values to zero
        TargetLoad_e(Eigen::VectorXf::Zero(TScount)),      // DataC Target Elec load TS
        ActualLoad_e(Eigen::VectorXf::Zero(TScount)),      // DataC Actual Elec load TS
        AvailHotHeat_h(Eigen::VectorXf::Zero(TScount)),      // DataC waste heat, usable by the ASHP, TS
        TargetHeat_h(Eigen::VectorXf::Zero(TScount))       // Target heat output for the ASHP
    {
        ASHPmaxElec_e = ptrASHPhot->MaxElec();       // Peak kWh per TS of ASHP

        // Calculate Target Load based on OptMode: 1=Target (default), 2=Price, 3=Carbon
        switch (OptMode) {
        case 2: // Price minimisation mode
            // placeholder for lookahead supplier price mode
        case 3: // Carbon minimisation mode
            // placholder for lookahead grid carbon mode
        default: // Target Power Mode (initially Max Load)							
            TargetLoad_e.setConstant(DataCmaxLoad_e);
        }
    }

    void AllCalcs(TempSum_cl &TempSum) {
        // If Data Centre  is not balancing, actual loads will be target
        ActualLoad_e = TargetLoad_e;
        AvailHotHeat_h = ActualLoad_e * HeatScalar;
        // FUTURE can switch TargetHeat to Pool, DHW or combo
        TargetHeat_h = TempSum.Heat_h;
        ptrASHPhot->AllCalcs(TargetHeat_h, AvailHotHeat_h);

        TempSum.Elec_e = TempSum.Elec_e + ActualLoad_e + ptrASHPhot->Load_e;
        TempSum.Heat_h = TempSum.Heat_h - ptrASHPhot->Heat_h;
    }

    void StepCalc(TempSum_cl &TempSum, const float FutureEnergy_e, const int t) {
        // FUTURE can switch TargetHeat to Pool, DHW or combo
        TargetHeat_h[t] = TempSum.Heat_h[t];
        // Set Electricty Budget for ASHP
        if (FutureEnergy_e <= 0) {
            ActualLoad_e[t] = 0;
            ASHPBudget_e = 0;
        } else if (FutureEnergy_e > TargetLoad_e[t] + ASHPmaxElec_e) {
            // Set Load & Budget to maximums
            ActualLoad_e[t] = TargetLoad_e[t];
            ASHPBudget_e = FutureEnergy_e - TargetLoad_e[t];
        }
        else {
            // Reduce Load & Budget to largest without breaching FutureEnergy
                ThrottleScalar = FutureEnergy_e / (TargetLoad_e[t] + ASHPmaxElec_e);
                ActualLoad_e[t] = TargetLoad_e[t] * ThrottleScalar;
                ASHPBudget_e = FutureEnergy_e - ActualLoad_e[t];
        }
        AvailHotHeat_h[t] = ActualLoad_e[t] * HeatScalar;

        ptrASHPhot->StepCalc(TargetHeat_h[t], AvailHotHeat_h[t], ASHPBudget_e, t);
    }

    void Report(const FullSimulationResult& Result) const {
        // ADD RESULTS
        // Target Load & Actual Load + ASHP stuff
    }

private:
    ASHPhot_cl* ptrASHPhot;

    const int TScount;
    const int OptMode;
    const float DataCmaxLoad_e;
    const float HeatScalar;
    float ASHPmaxElec_e;
    float ASHPBudget_e;
    float ThrottleScalar;

    year_TS TargetLoad_e;
    year_TS ActualLoad_e;
    year_TS AvailHotHeat_h;
    year_TS TargetHeat_h;
};
