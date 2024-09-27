#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "ASHP.hpp"
#include "TempSum.hpp"

#include "TaskData.hpp"
#include "../Definitions.hpp"

class DataCentre
{
public:
    DataCentre(const HistoricalData& historicalData, const TaskData& taskData) :
        // Initialise Persistent Values
        mHeatPump(historicalData, taskData),
        mTimesteps(taskData.calculate_timesteps()),
        // Mode: 1=Target, 2=Price, 3=Carbon
        mOptimisationMode(1),
        // Max kWh per TS
        mDataCentreMaxLoad_e(taskData.Flex_load_max * taskData.timestep_hours),
        // Percentage of waste heat captured for ASHP
        mHeatScalar(taskData.ScalarHYield),

        mTargetLoad_e(Eigen::VectorXf::Zero(mTimesteps)),
        mActualLoad_e(Eigen::VectorXf::Zero(mTimesteps)),
        mAvailableHotHeat_h(Eigen::VectorXf::Zero(mTimesteps)),
        mTargetHeat_h(Eigen::VectorXf::Zero(mTimesteps))
    {
        mHeatPumpMaxElectricalLoad_e = mHeatPump.MaxElec();

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
        mAvailableHotHeat_h = mActualLoad_e * mHeatScalar;
        // FUTURE can switch TargetHeat to Pool, DHW or combo
        // mTargetHeat_h = tempSum.Heat_h; REMOVED to support DHW & CH
        mHeatPump.AllCalcs(tempSum, mAvailableHotHeat_h);

        // update Temp Energy Balances
        tempSum.Elec_e += mActualLoad_e;
    }

	void StepCalc(TempSum& tempSum, const float futureEnergy_e, const int t) {
		// Switch to Pool, DHW, CH done in HeatPump
		// mTargetHeat_h[t] = tempSum.Heat_h[t];REMOVED to support DHW & CH

		// Set Electricty Budget for ASHP
        float heatPumpBudget_e;
		if (futureEnergy_e <= 0) {
			mActualLoad_e[t] = 0;
            heatPumpBudget_e = 0;
		}
		else if (futureEnergy_e > (mTargetLoad_e[t] + mHeatPumpMaxElectricalLoad_e)) {
			// Set Load & Budget to maximums
			mActualLoad_e[t] = mTargetLoad_e[t];
            heatPumpBudget_e = futureEnergy_e - mTargetLoad_e[t];
		}
		else {
			// Reduce Load & Budget to largest without breaching FutureEnergy
			float throttleScalar = futureEnergy_e / (mTargetLoad_e[t] + mHeatPumpMaxElectricalLoad_e);
			mActualLoad_e[t] = mTargetLoad_e[t] * throttleScalar;
            heatPumpBudget_e = futureEnergy_e - mActualLoad_e[t];
		}
		// Set hot heat (beyond ambient) available from DataCentre
        mAvailableHotHeat_h[t] = mActualLoad_e[t] * mHeatScalar;

		mHeatPump.StepCalc(tempSum, mAvailableHotHeat_h[t], heatPumpBudget_e, t);
        
        // Update Temp Energy Balances
        tempSum.Elec_e[t] += mActualLoad_e[t];
	}

    float getTargetLoad(int timestep) {
        return mTargetLoad_e[timestep];
    }

    void Report(FullSimulationResult& result) const {
        result.Data_centre_target_load = mTargetLoad_e;
        result.Data_centre_actual_load = mActualLoad_e;
        result.Data_centre_target_heat = mTargetHeat_h;
        result.Data_centre_available_hot_heat = mAvailableHotHeat_h;
        
        // NEED TO ADD HEATPUMP RESULTS
        //result.HeatPump_elec_load = mHeatPump.DHWload_e + mHeatPump.CHload_e;
        //result.HeatPump_DHWoutput = mHeatPump.DHWout_h;
        //result.HeatPump_CHoutput = mHeatPump.CHout_h;
        //result.HeatPump_UsedAmbientHeat = mHeatPump.FreeHeat_h;
        //result.HeatPump_UsedHotHeat = mHeatPump.UsedHotHeat_h;
    }

private:
    HotRoomHeatPump mHeatPump;

    const int mTimesteps;
    const int mOptimisationMode;
    const float mDataCentreMaxLoad_e;
    const float mHeatScalar;
    float mHeatPumpMaxElectricalLoad_e;

    year_TS mTargetLoad_e;
    year_TS mActualLoad_e;
    year_TS mAvailableHotHeat_h;
    year_TS mTargetHeat_h;
};
