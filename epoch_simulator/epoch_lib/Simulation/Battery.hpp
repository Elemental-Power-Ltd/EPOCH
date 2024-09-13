#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>
#include <algorithm>

#include "../Definitions.hpp"

// Battery is only used within an ESS or other component with electricity storage
class Battery {

public:
	Battery(const TaskData& taskData) :
		mCapacity_e(taskData.ESS_capacity),
		mPreSoC_e(taskData.ESS_start_SoC * taskData.ESS_capacity), // Init State of Charge in kWhs
		// TODO - reintroduce RTE to TaskData
		mRTLrate(1.0f - 0.86f), // loss rate easier in calcs

		// timestep_hours can be considered a power scalar per timestep
		mChargMax_e(taskData.ESS_charge_power * taskData.timestep_hours), // kWh per timestep
		mDischMax_e(taskData.ESS_discharge_power * taskData.timestep_hours), // UkWh per timestep
		mAuxLoad_e(taskData.ESS_capacity / 1200 * taskData.timestep_hours), // kWh per timestep

		// Initilaise results data vectors with all values to zero
		mHistSoC_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),      // Resulting State of Charge per timestep
		mHistCharg_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),   // Charge kWh per timestep
		mHistDisch_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),   // Discharge kWh per timestep
		mHistRTL_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),     // Round trip loss kWh per timestep
		mHistAux_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps()))     // Auxiliary Load kWh per timestep

	{
		// Auxiliary same every timestep: is there a vector function for this?
		for (int t = 1; t <= taskData.calculate_timesteps(); t++) {
			mHistAux_e[t] = mAuxLoad_e;
		}
	}

	float AvailCharg() const {
		return std::min(mChargMax_e, (mCapacity_e - mPreSoC_e) / (1 - mRTLrate));
	}

	float AvailDisch() const {
		return std::min(mDischMax_e, mPreSoC_e);
	}

	float GetSoC() { return mPreSoC_e; }

	void DoCharg(float Charge_e, int t) {
		mHistCharg_e[t] = Charge_e;
		mHistRTL_e[t] = Charge_e * mRTLrate;
		mHistSoC_e[t] = mPreSoC_e + Charge_e - mHistRTL_e[t];
		mPreSoC_e = mHistSoC_e[t];			//for next timestep
	}

	void DoDisch(float DisCharge_e, int t) {
		mHistDisch_e[t] = DisCharge_e;
		mHistSoC_e[t] = mPreSoC_e - DisCharge_e;
		mPreSoC_e = mHistSoC_e[t];			//for next timestep
	}

	// Public output data, create private Battery object in parent
	year_TS mHistSoC_e;
	year_TS mHistCharg_e;
	year_TS mHistDisch_e;
	year_TS mHistAux_e;
	year_TS mHistRTL_e;

private:
	const float mCapacity_e;
	const float mChargMax_e;
	const float mDischMax_e;
	const float mRTLrate;
	const float mAuxLoad_e;
	float mPreSoC_e;
};