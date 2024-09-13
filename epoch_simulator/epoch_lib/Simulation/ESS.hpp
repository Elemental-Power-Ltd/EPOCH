#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>
#include <algorithm>

#include "TaskData.hpp"
#include "../Definitions.hpp"
#include "TempSum.hpp"
#include "Battery.hpp"

class ESSbasic_cl {

public:
    ESSbasic_cl(const TaskData& taskData, Battery& extBattery) :
        // Initialise Persistent Values
        ESS_mode(taskData.ESS_charge_mode),
        TScount(taskData.calculate_timesteps()),
        // RECODE: ThresholdSoC(taskData.ESS_capacity * taskData.ESS_threshold),
        ThresholdSoC(taskData.ESS_capacity * 0.5f)
    {
        ptrBattery = &extBattery;
    }

    float AvailDisch() const {
        return ptrBattery->AvailDisch();
    }

    void StepCalc(TempSum_cl &TempSum, const float AvailGridImp, const int t) {
        // ESS_mode Consume = 1, Resilient = 2, Threshold = 3, Price = 4, Carbon = 5
        switch (ESS_mode) {
        case 1: // Consume mode
            if (TempSum.Elec_e[t] >= 0) {  // Surplus Demand, discharge ESS
                Ecalc = std::min(TempSum.Elec_e[t], ptrBattery->AvailDisch());
                ptrBattery->DoDisch(Ecalc, t);
                TempSum.Elec_e[t] = TempSum.Elec_e[t] - Ecalc;
            }
            else {        // Surplus Generation, charge ESS
                Ecalc = std::min(-TempSum.Elec_e[t], ptrBattery->AvailCharg());
                ptrBattery->DoCharg(Ecalc, t);
                TempSum.Elec_e[t] = TempSum.Elec_e[t] + Ecalc;
            }
            break;

        case 3: // Threshold mode
            if (ptrBattery->GetSoC() > ThresholdSoC) {   // High SoC = Consume mode (1)
                if (TempSum.Elec_e[t] >= 0) {   // Surplus Demand, discharge ESS
                    Ecalc = std::min(TempSum.Elec_e[t], ptrBattery->AvailDisch());
                    ptrBattery->DoDisch(Ecalc, t);
                    TempSum.Elec_e[t] = TempSum.Elec_e[t] - Ecalc;
                }
                else {            // Surplus Generation, charge ESS
                    Ecalc = std::min(-TempSum.Elec_e[t], ptrBattery->AvailCharg());
                    ptrBattery->DoCharg(Ecalc, t);
                    TempSum.Elec_e[t] = TempSum.Elec_e[t] + Ecalc;
                }
            }
            else {                              // Low SoC = Resilient Mode	
                if ((TempSum.Elec_e[t] - AvailGridImp) >= 0) {		// Grid cannot meet Demand, discharge ESS		
                    Ecalc = std::min((TempSum.Elec_e[t] - AvailGridImp), ptrBattery->AvailDisch());
                    ptrBattery->DoDisch(Ecalc, t);
                    TempSum.Elec_e[t] = TempSum.Elec_e[t] - Ecalc;
                }
                else {  // Charge ESS from Grid headroom or surplus Generation		
                    Ecalc = std::min(-(TempSum.Elec_e[t] - AvailGridImp), ptrBattery->AvailCharg());
                    ptrBattery->DoCharg(Ecalc, t);
                    TempSum.Elec_e[t] = TempSum.Elec_e[t] + Ecalc;
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
                Ecalc = std::min((TempSum.Elec_e[t] - AvailGridImp), ptrBattery->AvailDisch());
                ptrBattery->DoDisch(Ecalc, t);
                TempSum.Elec_e[t] = TempSum.Elec_e[t] - Ecalc;
            }
            else {  // Charge ESS from Grid headroom or surplus Generation		
                Ecalc = std::min(-(TempSum.Elec_e[t] - AvailGridImp), ptrBattery->AvailCharg());
                ptrBattery->DoCharg(Ecalc, t);
                TempSum.Elec_e[t] = TempSum.Elec_e[t] + Ecalc;
            }
        }
    }

    void Report(FullSimulationResult& Result) {
        Result.ESS_charge = ptrBattery->mHistCharg_e;
        Result.ESS_discharge = ptrBattery->mHistDisch_e;
        Result.ESS_resulting_SoC = ptrBattery->mHistSoC_e;
        // ADD ESS Losses
        // Result.ESS_AuxLoad = ptrBattery->mHistAux_e;
        // Result.ESS_RTL = ptrBattery->mHistRTL_e;
    }
private:
    Battery *ptrBattery;
    const int ESS_mode;
    const int TScount;
    const float ThresholdSoC;

    float Ecalc;
};
