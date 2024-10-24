#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>
#include <algorithm>

#include "TaskData.hpp"
#include "../Definitions.hpp"
#include "TempSum.hpp"
#include "Battery.hpp"

class BasicESS {

public:
    BasicESS(const TaskData& taskData) :
        // Initialise Persistent Values
        mESS_mode(taskData.ESS_charge_mode),
        mTimesteps(taskData.calculate_timesteps()),
        // RECODE: mThresholdSoC(taskData.ESS_capacity * taskData.ESS_threshold),
        mThresholdSoC(taskData.ESS_capacity * 0.5f),
        mBattery(taskData)
    {

    }

    float AvailDisch() const {
        return mBattery.getAvailableDischarge();
    }

    void StepCalc(TempSum &TempSum, const float AvailGridImp, const int t) {
        // mESS_mode Consume = 1, Resilient = 2, Threshold = 3, Price = 4, Carbon = 5
        switch (mESS_mode) {
        case 1: // Consume mode
            if (TempSum.Elec_e[t] >= 0) {  // Surplus Demand, discharge ESS
                mEnergyCalc = std::min(TempSum.Elec_e[t], mBattery.getAvailableDischarge());
                mBattery.doDischarge(mEnergyCalc, t);
                TempSum.Elec_e[t] = TempSum.Elec_e[t] - mEnergyCalc;
            }
            else {        // Surplus Generation, charge ESS
                mEnergyCalc = std::min(-TempSum.Elec_e[t], mBattery.getAvailableCharge());
                mBattery.doCharge(mEnergyCalc, t);
                TempSum.Elec_e[t] = TempSum.Elec_e[t] + mEnergyCalc;
            }
            break;

        case 3: // Threshold mode
            if (mBattery.GetSoC() > mThresholdSoC) {   // High SoC = Consume mode (1)
                if (TempSum.Elec_e[t] >= 0) {   // Surplus Demand, discharge ESS
                    mEnergyCalc = std::min(TempSum.Elec_e[t], mBattery.getAvailableDischarge());
                    mBattery.doDischarge(mEnergyCalc, t);
                    TempSum.Elec_e[t] = TempSum.Elec_e[t] - mEnergyCalc;
                }
                else {            // Surplus Generation, charge ESS
                    mEnergyCalc = std::min(-TempSum.Elec_e[t], mBattery.getAvailableCharge());
                    mBattery.doCharge(mEnergyCalc, t);
                    TempSum.Elec_e[t] = TempSum.Elec_e[t] + mEnergyCalc;
                }
            }
            else {                              // Low SoC = Resilient Mode	
                if ((TempSum.Elec_e[t] - AvailGridImp) >= 0) {		// Grid cannot meet Demand, discharge ESS		
                    mEnergyCalc = std::min((TempSum.Elec_e[t] - AvailGridImp), mBattery.getAvailableDischarge());
                    mBattery.doDischarge(mEnergyCalc, t);
                    TempSum.Elec_e[t] = TempSum.Elec_e[t] - mEnergyCalc;
                }
                else {  // Charge ESS from Grid headroom or surplus Generation		
                    mEnergyCalc = std::min(-(TempSum.Elec_e[t] - AvailGridImp), mBattery.getAvailableCharge());
                    mBattery.doCharge(mEnergyCalc, t);
                    TempSum.Elec_e[t] = TempSum.Elec_e[t] + mEnergyCalc;
                }
            }
            break;

        case 4: // Price minimisation mode
            // placeholder for lookahead supplier price mode
            // v0-7 lookahead case = dynamic based on volume forecast, omit for now
            break;

        case 5: // Carbon minimisation mode
            // placholder for lookahead grid carbon mode
            break;

        default: // Resilient Mode case should be default							
            if ((TempSum.Elec_e[t] - AvailGridImp) >= 0) {		// Grid cannot meet Demand, discharge ESS		
                mEnergyCalc = std::min((TempSum.Elec_e[t] - AvailGridImp), mBattery.getAvailableDischarge());
                mBattery.doDischarge(mEnergyCalc, t);
                TempSum.Elec_e[t] = TempSum.Elec_e[t] - mEnergyCalc;
            }
            else {  // Charge ESS from Grid headroom or surplus Generation		
                mEnergyCalc = std::min(-(TempSum.Elec_e[t] - AvailGridImp), mBattery.getAvailableCharge());
                mBattery.doCharge(mEnergyCalc, t);
                TempSum.Elec_e[t] = TempSum.Elec_e[t] + mEnergyCalc;
            }
        }
    }

	void Report(ReportData& reportData) {
        reportData.ESS_charge = mBattery.mHistCharg_e;
        reportData.ESS_discharge = mBattery.mHistDisch_e;
        reportData.ESS_resulting_SoC = mBattery.mHistSoC_e;

        // TODO - make a report method in the battery and call that instead
        reportData.ESS_AuxLoad = mBattery.mHistAux_e;
        reportData.ESS_RTL = mBattery.mHistRTL_e;
	}

private:
    Battery mBattery;
    const int mESS_mode;
    const int mTimesteps;
    const float mThresholdSoC;

    float mEnergyCalc;
};
