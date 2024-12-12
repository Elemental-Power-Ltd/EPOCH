#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>
#include <algorithm>

#include "../../../Definitions.hpp"
#include "../../TaskComponents.hpp"

// Battery is only used within an ESS or other component with electricity storage
class Battery {

public:
	Battery(const HistoricalData& historicalData, const EnergyStorageSystem& essData) :
		mCapacity_e(essData.capacity),
		mPreSoC_e(essData.initial_charge), // Init State of Charge in kWhs
		// TODO - reintroduce RTE to TaskData
		mRTLrate(1.0f - 0.86f), // loss rate easier in calcs

		// timestep_hours can be considered a power scalar per timestep
		mChargMax_e(essData.charge_power * historicalData.timestep_hours), // kWh per timestep
		mDischMax_e(essData.discharge_power * historicalData.timestep_hours), // UkWh per timestep
		mAuxLoad_e(essData.capacity / 1200 * historicalData.timestep_hours), // kWh per timestep

		// Initilaise results data vectors with all values to zero
		mHistSoC_e(Eigen::VectorXf::Zero(historicalData.timesteps)),      // Resulting State of Charge per timestep
		mHistCharg_e(Eigen::VectorXf::Zero(historicalData.timesteps)),   // Charge kWh per timestep
		mHistDisch_e(Eigen::VectorXf::Zero(historicalData.timesteps)),   // Discharge kWh per timestep
		mHistRTL_e(Eigen::VectorXf::Zero(historicalData.timesteps))     // Round trip loss kWh per timestep
	{
		mHistAux_e = Eigen::VectorXf::Constant(historicalData.timesteps, mAuxLoad_e);
	}

	float getAvailableCharge() const {
		return std::min(mChargMax_e, (mCapacity_e - mPreSoC_e) / (1 - mRTLrate));
	}

	float getAvailableDischarge() const {
		return std::min(mDischMax_e, mPreSoC_e);
	}

	float GetSoC() { return mPreSoC_e; }

	void doCharge(float Charge_e, size_t t) {
		mHistCharg_e[t] = Charge_e;
		mHistRTL_e[t] = Charge_e * mRTLrate;
		mHistSoC_e[t] = mPreSoC_e + Charge_e - mHistRTL_e[t];
		mPreSoC_e = mHistSoC_e[t];			//for next timestep
	}

	void doDischarge(float DisCharge_e, size_t t) {
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