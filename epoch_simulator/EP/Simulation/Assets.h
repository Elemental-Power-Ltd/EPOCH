#pragma once

#include <algorithm>
#include <Eigen/Core>
#include <spdlog/spdlog.h>

#include "Config.h"
#include "../Definitions.h"


class ESS {

public:
    ESS(const Config& config) :
        mChargePower(config.getESS_charge_power()),
        mDischargePower(config.getESS_discharge_power()),
        mCapacity(config.getESS_capacity()),
        mRTE(config.getESS_RTE()),
        mAuxLoad(config.getESS_aux_load()),
        mStartSoC(config.getESS_start_SoC()),

        mTimesteps(config.calculate_timesteps()),
        mTimestep_hours(config.getTimeStep_hours()),

        // TODO - this should likely be an enum
        mChargeMode(1),
        mDischargeMode(1),

        mCharge(Eigen::VectorXf::Zero(mTimesteps)),
        mDischarge(Eigen::VectorXf::Zero(mTimesteps)),
        mRgenOnlyCharge(Eigen::VectorXf::Zero(mTimesteps)),
        mBeforeGridDischarge(Eigen::VectorXf::Zero(mTimesteps)),
        mResultingSoC(Eigen::VectorXf::Zero(mTimesteps)),
        mAvailableChargePower(Eigen::VectorXf::Zero(mTimesteps)),
        mAvailableDischargePower(Eigen::VectorXf::Zero(mTimesteps))
    {
    }

    //These are steps on ESS tab for Opportunitic BESS alg # 1 (Charge mode from Rgen/ Discharge mode = Before grid) 
    // IMPORTANT: BELOW FORMULAE ONLY VALID FOR HOUR TIMESTEPS WHERE 1kWH = 1kW
    void initialise(float initialESUM) {
        //1. Calculate ESS available Discharge Power in TS0: DB4 = MIN(ESS_StartSoC,ESS_DisPwr)
        initialiseESSAvailableDischargePower();
        //2. Calculate ESS available Charge Power in TS0: CB4 = MIN((ESS_Cap-ESS_StartSoC)/ESS_RTE,ESS_ChPwr)
        initialiseESSAvailableChargePower();
        //3. Calculate "Discharge mode = before grid" in TS0:  IB4=IF(ESum!B4>0,MIN(Esum!B4,ESS!DB4),0) NOTE: Dependency on Esum tab step 1, currently, ESUM[0]
        initialiseESSBeforeGridDischarge(initialESUM);
        //4. Calculate "Charge mode = Rgen only" in TS0: EB4=IF(ESum!B4<0,MIN(-Esum!B4,ESS!CB4),0) NOTE: Dependency on Esum tab step 1, currently, -ESUM[0]
        initialiseESSRgenOnlyCharge(initialESUM);
        //5. Calculate BESS actions in TS0 (Charge = B4 / Discharge = AB4 )
        initialiseESSDischarge();
        initialiseESSCharge();
        //6. Apply RTE, and update SoC in "ESS resulting state of charge (SoC)" TS0: BB4 = ESS_StartSoC-(AB4+B4*ESS_RTE)
        initialiseESSResultingSoC();
    }

    void runTimesteps(const year_TS& ESUM) {
        // main loop for ESS

        for (int timestep = 1; timestep < mTimesteps; timestep++) {
            ////7. For TS1+, Calculate ESS available Discharge Power for TS1 based on final SoC in TS0 and max discharge power DC4=MIN(BB4,ESS_DisPwr) 
            calculateESSAvailableDischargePower(timestep);

            ////8. For TS1+, Calculate ESS available Charge Power for TS1 based on final SoC in TS0 and max charge power CC4=MIN(ESS_Cap-BB4)/ESS_RTE,ESS_ChPwr)
            calculateESSAvailableChargePower(timestep);

            ////9. For TS1+, Calculate "Discharge mode = before" in TS1: IC4 = IF(ESum!C4>0,MIN(ESum!C4,ESS!DC4),0) NOTE: Dependency on Esum tab step 2, currently, ESUM[1]
            calculateESSBeforeGridDischarge(ESUM[timestep], timestep);

            ////10.For TS1+, Calculate "Charge mode = Rgen only" EC4 = IF(Esum!C4<0,MIN(-ESum!C4,ESS!CC4),0) NOTE: Dependency on Esum tab step 2, currently, ESUM[1]
            calculateESSRgenOnlyCharge(ESUM[timestep], timestep);

            ////11.Calculate BESS actions in TS0 (Charge = C4 / Discharge = AC4)
            setESSDischarge(timestep);
            setESSCharge(timestep);

            ////12.For TS2, Caculate BESS actions and update SoC in "ESS resulting state of charge (SoC)" BC4 = BB4+C4*ESS_RTE-AC4
            calculateESSResultingSoC(timestep);

            //13.Repeat actions 7-13 for remaining TS in time window
        }

    }

    void initialiseESSAvailableDischargePower() {
        // calculate kW power from energy kWh (NEEDS attention for TS=! 1.)
        float ESS_start_SoC_power = mStartSoC * mCapacity / mTimestep_hours;
        mAvailableDischargePower[0] = std::min(ESS_start_SoC_power, mDischargePower);
    }

    void initialiseESSAvailableChargePower() {
        // calculate kW power from energy kWh
        float ESS_start_SoC_power = mStartSoC * mCapacity / mTimestep_hours; 
        float chargePotential = (mCapacity - ESS_start_SoC_power) / mRTE;

        mAvailableChargePower[0] = std::min(chargePotential, mChargePower);;
        return;
    }

    void initialiseESSBeforeGridDischarge(float initialESUM) {
        // calculate kW power from energy kWh 
        if (initialESUM > 0) {
            mBeforeGridDischarge[0] = std::min(initialESUM, mAvailableDischargePower[0]);
        } else {
            mBeforeGridDischarge[0] = 0;
        }
    }

    void initialiseESSRgenOnlyCharge(float initialESUM) {
        // calculate kW power from energy kWh 
        if (initialESUM < 0) {
            mRgenOnlyCharge[0] = std::min(-initialESUM, mAvailableChargePower[0]);
        } else {
            mRgenOnlyCharge[0] = 0;
        }
    }

    void initialiseESSDischarge() {
        if (mDischargeMode == 1) {
            mDischarge[0] = mBeforeGridDischarge[0];
        } else {
            mDischarge[0] = 999.9f; // flag that other charge mode engaged.
        } 
    }

    void initialiseESSCharge() {
        if (mChargeMode == 1) {
            mCharge[0] = mRgenOnlyCharge[0];
        }
        else {
            mDischarge[0] = 999.9f; // flag that other charge mode engaged.
        }
    }

    void initialiseESSResultingSoC() {
        // calculate kW power from energy kWh
        float ESS_start_SoC_energy = mStartSoC * mCapacity * mTimestep_hours;
        // calculate resulting SoC energy from discharge / charge actions latter with RTE applied
        mResultingSoC[0] = ESS_start_SoC_energy - (mDischarge[0] + mCharge[0] * mRTE) * mTimestep_hours;
    }

    // Member functions: ESS calculations for TS2+

    void calculateESSAvailableDischargePower(int timestep) {
        // get previous value of resulting SoC
        float prev_resulting_SoC = mResultingSoC[timestep - 1];
        //energy to power
        float ESS_prev_SoC_power = prev_resulting_SoC / mTimestep_hours; 

        // calculate based DC4 = MIN(BB4, ESS_DisPwr)
        mAvailableDischargePower[timestep] = std::min(ESS_prev_SoC_power, mDischargePower);;
    }

    void calculateESSAvailableChargePower(int timestep) {
        // calculate kW power from energy kWh
        float prev_resulting_SoC = mResultingSoC[timestep - 1];
        //energy to power
        float ESS_prev_SoC_power = prev_resulting_SoC / mTimestep_hours;
        // get previous value of resulting SoC
        float charge_potential = (mCapacity - ESS_prev_SoC_power) / mRTE;

        // CC4 = MIN(ESS_Cap - BB4) / ESS_RTE, ESS_ChPwr)
        mAvailableChargePower[timestep] = std::min(charge_potential, mChargePower);;
    }

    void calculateESSBeforeGridDischarge(float ESUM, int timestep) {

        float ESSDischarge = mAvailableDischargePower[timestep];

        float beforeGridDischarge;
        if (ESUM > 0) {
            beforeGridDischarge = std::min(ESUM, ESSDischarge);
        } else {
            beforeGridDischarge = 0;
        }

        // calculate kW power from energy kWh 
        //TS2: IC4 = IF(ESum!C4 > 0, MIN(ESum!C4, ESS!DC4), 0) NOTE : Dependency on Esum tab step 2, currently, ESUM[2]
        mBeforeGridDischarge[timestep] = beforeGridDischarge;
    }

    void calculateESSRgenOnlyCharge(float ESUM, int timestep) {
        //EC4 = IF(Esum!C4<0,MIN(-ESum!C4,ESS!CC4),0)
        if (ESUM < 0) {
            mRgenOnlyCharge[timestep] = std::min(-ESUM, mAvailableChargePower[timestep]);
        } else {
            mRgenOnlyCharge[timestep] = 0.0f;
        }
    }

    void setESSDischarge(int timestep) {
        if (mDischargeMode == 1) {
            mDischarge[timestep] = mBeforeGridDischarge[timestep];
        } else {
            spdlog::warn("err: discharge_mode does not yet exist");
        }
    }

    void setESSCharge(int timestep) {
        if (mChargeMode == 1) {
            mCharge[timestep] = mRgenOnlyCharge[timestep];
        } else {
            spdlog::warn("err: charge_mode does not yet exist");
        }
    }

    //12.For TS2, Caculate BESS actions and update SoC in "ESS resulting state of charge (SoC)" BC4 = BB4+C4*ESS_RTE-AC4
    // these functions account for headroom built in to Grid_connection to take import/export power peaks intratimestep

    void calculateESSResultingSoC(int timestep) {
        // calculate kW power from energy kWh
        float ESS_end_SoC_energy = mResultingSoC[timestep - 1] + 
            (mTimestep_hours * ((mCharge[timestep] * mRTE) - ((mDischarge[timestep]))));
        // calculate resulting SoC energy from discharge / charge actions 
        // latter with RTE applied convert from power to energy.
        mResultingSoC[timestep] = ESS_end_SoC_energy;
    }

    year_TS getESSAvailableDischargePower() const {
        return mAvailableDischargePower;
    }

    year_TS getESSAvailableChargePower() const {
        return mAvailableChargePower;
    }

    year_TS getESSRgenOnlyCharge() const {
        return mRgenOnlyCharge;
    }

    year_TS getESSDischarge() const {
        return mDischarge;
    }

    year_TS getESSCharge() const {
        return mCharge;
    }

    year_TS getESSResultingSoC() const {
        return mResultingSoC;
    }


private:
    const float mChargePower;
    const float mDischargePower;
    const float mCapacity;
    const float mRTE;
    const float mAuxLoad;
    const float mStartSoC;

    const int mTimesteps;
    const float mTimestep_hours;

    int mChargeMode;
    int mDischargeMode;

    year_TS mCharge;
    year_TS mDischarge;
    year_TS mRgenOnlyCharge;
    year_TS mBeforeGridDischarge;
    year_TS mAvailableChargePower;
    year_TS mAvailableDischargePower;
    year_TS mResultingSoC;

};
