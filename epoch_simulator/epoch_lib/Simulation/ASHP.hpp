#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>
#include <algorithm>

#include "TaskData.hpp"
#include "../Definitions.hpp"
#include "ASHPperf.hpp"
#include "TempSum.hpp"

// ASHPhot is only used within a DataCentre or alternative heat waste object
class HotRoomHeatPump {

public:
	HotRoomHeatPump(const HistoricalData& historicalData, const TaskData& taskData) :
		// Initialise Persistent Values
		DHW_OUT_TEMP(60),	// FUTURE: removed when taskData.ASHP_DHWtemp available
		mASHPperfDHW(taskData, DHW_OUT_TEMP),	// lookup object for DHW performance
		mASHPperfCH(taskData, taskData.ASHP_RadTemp),	// lookup object for CH performance
		mTimesteps(taskData.calculate_timesteps()),
		mPowerScalar(taskData.timestep_hours),
		mHotTemp(taskData.ASHP_HotTemp),
		mDHWflag(1),	// FUTURE: read value from (new) taskData value or use ASHP_DHWtemp not zero
		mCHflag(1),		// FUTURE: read value from (new) taskData value or use ASHP_RadTemp not zero
		mAmbientTemperature(historicalData.airtemp_data),	// Ambient Temperature
		mHeatPumpMax_h(1.0f),
		mHeatPumpMax_e(1.0f),
		mAvailHotHeatTemp_h(0.0f),
		mMaxElec_e(0.0f),

		// Initilaise results data vectors with all values to zero
		mDHWload_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),	// ASHP electrical load
		mDHWout_h(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),	// ASHP heat output
		mCHload_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),	// ASHP electrical load
		mCHout_h(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),		// ASHP heat output
		mFreeHeat_h(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),		// ASHP heat from ambient
		FreeHeatTemp_h(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),	// ASHP heat: temp value for calcs
		mUsedHotHeat_h(Eigen::VectorXf::Zero(taskData.calculate_timesteps()))	// ASHP heat from Hotroom

	{
		mResidualCapacity = Eigen::VectorXf::Constant(taskData.calculate_timesteps(), 1.0f);// Remaining heatpump capacity
		mHeatPumpMaxAmbient.Heat_h = 0;	// For mASHPperf->Lookup results
		mHeatPumpMaxAmbient.Load_e = 0;
		mHeatPumpMaxHotRoom.Heat_h = 0;
		mHeatPumpMaxHotRoom.Load_e = 0;
	}

	const float MaxElec() {
		// Peak kWh per timestep of ASHP
		mMaxElec_e = std::max(mASHPperfDHW.MaxElecLoad(), mASHPperfCH.MaxElecLoad());
		return mMaxElec_e;
	}

	void AllCalcs(TempSum& tempSum, const year_TS& AvailHotHeat_h) {
		// Applies fixed precedence: hot water is served before central heating

		mASHPperfDHW.Lookup(mHotTemp, mHeatPumpMaxHotRoom);		// 2nd Arg is return values struct

		for (int t = 0; t < mTimesteps; t++) {
			if (mDHWflag == 1) {
				// Lookup performances for DHW (hot water) output temperature
				mASHPperfDHW.Lookup(mAmbientTemperature[t], mHeatPumpMaxAmbient);	// 2nd Arg is return values struct

				// Output = lower of Hotroom lookup value & Ambient + hotroom energy value (Conservation of Energy)
				if ((mHeatPumpMaxAmbient.Heat_h + AvailHotHeat_h[t]) >= mHeatPumpMaxHotRoom.Heat_h) {
					mHeatPumpMax_h = mHeatPumpMaxHotRoom.Heat_h;
					mHeatPumpMax_e = mHeatPumpMaxHotRoom.Load_e;
				} else {
					mHeatPumpMax_h = mHeatPumpMaxAmbient.Heat_h + AvailHotHeat_h[t];
					// Apply higher of energy input values if applying (Conservation of Energy)
					mHeatPumpMax_e = std::max(mHeatPumpMaxAmbient.Load_e, mHeatPumpMaxHotRoom.Load_e);
				}
				// Adjust output and load to meet heating demand
				if (mHeatPumpMax_h <= 0) {	// If no HeatPump capacity, set values to zero
					mDHWout_h[t] = 0;
					mDHWload_e[t] = 0;
					mResidualCapacity[t] = 0;
				} else if (tempSum.DHW_load_h[t] <= mHeatPumpMax_h) {	// Adjust values to load
					mDHWout_h[t] = tempSum.DHW_load_h[t];
					mDHWload_e[t] = mHeatPumpMax_e * mDHWout_h[t] / mHeatPumpMax_h;
					mResidualCapacity[t] = 1 - mDHWout_h[t] / mHeatPumpMax_h;
				} else {	// ASHP cannot meet heating target, so will do maximum capacity
					mDHWout_h[t] = mHeatPumpMax_h;
					mDHWload_e[t] = mHeatPumpMax_e;
					mResidualCapacity[t] = 0;
				}
			}
			mFreeHeat_h[t] = std::max(mDHWout_h[t] - mDHWload_e[t] - AvailHotHeat_h[t], 0.0f);	// How much heat from ambient
			mUsedHotHeat_h[t] = mDHWout_h[t] - mDHWload_e[t] - mFreeHeat_h[t];

			if (mCHflag == 1) {

				// Lookup performances for CH (central heating) output temperature
				mASHPperfCH.Lookup(mAmbientTemperature[t], mHeatPumpMaxAmbient);// 2nd Arg is return values struct

				mAvailHotHeatTemp_h = AvailHotHeat_h[t] - mUsedHotHeat_h[t];
				// Use lower of Hotroom temperature values & Ambient + hotroom energy values (Conservation of Energy)
				if ((mHeatPumpMaxAmbient.Heat_h + AvailHotHeat_h[t]) >= mHeatPumpMaxHotRoom.Heat_h) {
					mHeatPumpMax_h = mHeatPumpMaxHotRoom.Heat_h * mResidualCapacity[t];
					mHeatPumpMax_e = mHeatPumpMaxHotRoom.Load_e * mResidualCapacity[t];
				}
				else {
					mHeatPumpMax_h = (mHeatPumpMaxAmbient.Heat_h + AvailHotHeat_h[t]) * mResidualCapacity[t];
					mHeatPumpMax_e = mHeatPumpMaxAmbient.Load_e * mResidualCapacity[t];
				}
				// Adjust output and load to meet heating demand
				if (mHeatPumpMax_h <= 0) {	// If no HeatPump capacity, set values to zero
					mCHout_h[t] = 0;
					mCHload_e[t] = 0;
					mResidualCapacity[t] = 0;
				}
				else if (tempSum.Heat_h[t] <= mHeatPumpMax_h) {	// Adjust values to load
					mCHout_h[t] = tempSum.Heat_h[t];
					mCHload_e[t] = mHeatPumpMax_e * mCHout_h[t] / mHeatPumpMax_h;
					mResidualCapacity[t] = mResidualCapacity[t] * (1 - mCHout_h[t] / mHeatPumpMax_h);
				}
				else {	// ASHP cannot meet heating target, so will do maximum capacity
					mCHout_h[t] = mHeatPumpMax_h;
					mCHload_e[t] = mHeatPumpMax_e;
					mResidualCapacity[t] = 0;
				}
				FreeHeatTemp_h[t] = std::max(mCHout_h[t] - mCHload_e[t] - AvailHotHeat_h[t], 0.0f);	// How much heat from ambient
				mFreeHeat_h[t] += FreeHeatTemp_h[t];
				mUsedHotHeat_h[t] = mUsedHotHeat_h[t] + mCHout_h[t] - mCHload_e[t] - FreeHeatTemp_h[t];
			}
		}
		tempSum.Elec_e = tempSum.Elec_e + mDHWload_e + mCHload_e;
		tempSum.DHW_load_h = tempSum.DHW_load_h - mDHWout_h;
		tempSum.Heat_h = tempSum.Heat_h - mCHout_h;
	}

	void StepCalc(TempSum& tempSum, const float AvailHotHeat_h, const float ElecBudget_e, int t) {
		if(ElecBudget_e <= 0) {
			// No electricty available for the ASHP (balancing object)
			mDHWout_h[t] = 0.0f;
			mDHWload_e[t] = 0.0f;
			mCHout_h[t] = 0.0f;
			mCHload_e[t] = 0.0f;
			mResidualCapacity[t] = 0.0f;
			mElecResidual_e = 0.0f;
		}
		else {
			if (mDHWflag == 1) {
				// Lookup performances for DHW (hot water) output temperature
				mASHPperfDHW.Lookup(mAmbientTemperature[t], mHeatPumpMaxAmbient);	// 2nd Arg is return values struct
				mASHPperfDHW.Lookup(mHotTemp, mHeatPumpMaxHotRoom);		// 2nd Arg is return values struct

				// Max values = lower of Hotroom lookup value & Ambient + hotroom energy value (Conservation of Energy)
				if ((mHeatPumpMaxAmbient.Heat_h + AvailHotHeat_h) >= mHeatPumpMaxHotRoom.Heat_h) {
					mHeatPumpMax_h = mHeatPumpMaxHotRoom.Heat_h;
					mHeatPumpMax_e = mHeatPumpMaxHotRoom.Load_e;
				}
				else {
					mHeatPumpMax_h = mHeatPumpMaxAmbient.Heat_h + AvailHotHeat_h;
					// Apply higher of energy input values if applying (Conservation of Energy)
					mHeatPumpMax_e = std::max(mHeatPumpMaxAmbient.Load_e, mHeatPumpMaxHotRoom.Load_e);
				}
				// Adjust output and load to meet heating demand
				if (mHeatPumpMax_h <= 0) {	// If no HeatPump capacity, set values to zero
					mDHWout_h[t] = 0;
					mDHWload_e[t] = 0;
					mResidualCapacity[t] = 0;
				}
				else if (tempSum.DHW_load_h[t] <= mHeatPumpMax_h) {	// Adjust values to load
					mDHWout_h[t] = tempSum.DHW_load_h[t];
					mDHWload_e[t] = mHeatPumpMax_e * mDHWout_h[t] / mHeatPumpMax_h;
					mResidualCapacity[t] = 1 - mDHWout_h[t] / mHeatPumpMax_h;
				}
				else {	// ASHP cannot meet heating target, so will do maximum capacity
					mDHWout_h[t] = mHeatPumpMax_h;
					mDHWload_e[t] = mHeatPumpMax_e;
					mResidualCapacity[t] = 0;
				}
				// Adjust output and load to meet available electricity
				if (mDHWload_e[t] > ElecBudget_e) {
					// Check whether the ASHP load exceeds the electricity budget, if so, reduce proportionally
					mDHWout_h[t] = mDHWout_h[t] * ElecBudget_e / mDHWload_e[t];
					mDHWload_e[t] = ElecBudget_e;
					mResidualCapacity[t] = (1 - mDHWout_h[t] / mHeatPumpMax_h) * ElecBudget_e / mDHWload_e[t];
				}
				mFreeHeat_h[t] = mDHWout_h[t] - mDHWload_e[t] - AvailHotHeat_h;	// How much heat from ambient		
				if (mFreeHeat_h[t] < 0) { mFreeHeat_h[t] = 0; }	// Prevent -ve values (not all AvailHotHeat_h required)
				mUsedHotHeat_h[t] = mDHWout_h[t] - mDHWload_e[t] - mFreeHeat_h[t];
				mElecResidual_e = ElecBudget_e - mDHWload_e[t];
			}
		}
		if (mElecResidual_e <= 0) {
			// No electricty remains for the ASHP CH
			mCHout_h[t] = 0;
			mCHload_e[t] = 0;
			mResidualCapacity[t] = 0;
		} else {
			if (mCHflag == 1) {
				// Lookup performances for CH (central heating) output temperature
				mASHPperfCH.Lookup(mAmbientTemperature[t], mHeatPumpMaxAmbient);	// 2nd Arg is return values struct
				mASHPperfCH.Lookup(mHotTemp, mHeatPumpMaxHotRoom);		// 2nd Arg is return values struct
				
				mAvailHotHeatTemp_h = AvailHotHeat_h - mUsedHotHeat_h[t];
				// Max values = lower of Hotroom lookup value & Ambient + hotroom energy value (Conservation of Energy)
				if ((mHeatPumpMaxAmbient.Heat_h + mAvailHotHeatTemp_h) >= mHeatPumpMaxHotRoom.Heat_h) {
					mHeatPumpMax_h = mHeatPumpMaxHotRoom.Heat_h;
					mHeatPumpMax_e = mHeatPumpMaxHotRoom.Load_e;
				}
				else {
					mHeatPumpMax_h = mHeatPumpMaxAmbient.Heat_h + mAvailHotHeatTemp_h;
					// Apply higher of energy input values if applying (Conservation of Energy)
					mHeatPumpMax_e = std::max(mHeatPumpMaxAmbient.Load_e, mHeatPumpMaxHotRoom.Load_e);
				}
				// Adjust output and load to meet heating demand
				if (mHeatPumpMax_h <= 0) {	// If no HeatPump capacity, set values to zero
					mCHout_h[t] = 0;
					mCHload_e[t] = 0;
					mResidualCapacity[t] = 0;
				}
				else if (tempSum.Heat_h[t] <= mHeatPumpMax_h) {	// Adjust values to load
					mCHout_h[t] = tempSum.Heat_h[t];
					mCHload_e[t] = mHeatPumpMax_e * mCHout_h[t] / mHeatPumpMax_h;
					mResidualCapacity[t] = mResidualCapacity[t] * (1 - mCHout_h[t] / mHeatPumpMax_h);
				}
				else {	// ASHP cannot meet heating target, so do maximum capacity
					mCHout_h[t] = mHeatPumpMax_h;
					mCHload_e[t] = mHeatPumpMax_e;
					mResidualCapacity[t] = 0;
				}
				// Adjust output and load to meet available electricity
				if (mCHload_e[t] > mElecResidual_e) {
					// Check whether the ASHP load exceeds the electricity budget, if so, reduce proportionally
					mCHout_h[t] = mCHout_h[t] * ElecBudget_e / mCHload_e[t];
					mCHload_e[t] = ElecBudget_e;
					mResidualCapacity[t] = (1 - mCHout_h[t] / mHeatPumpMax_h) * ElecBudget_e / mCHload_e[t];
				}
				FreeHeatTemp_h[t] = mCHout_h[t] - mCHload_e[t] - mAvailHotHeatTemp_h;	// How much heat from ambient		
				if (FreeHeatTemp_h[t] < 0) { FreeHeatTemp_h[t] = 0; }	// Prevent -ve values (not all AvailHotHeat_h required)
				mUsedHotHeat_h[t] = mUsedHotHeat_h[t] + mDHWout_h[t] - mDHWload_e[t] - FreeHeatTemp_h[t];
				mElecResidual_e = mElecResidual_e - mCHload_e[t];
			}
		}
		tempSum.Elec_e[t] = tempSum.Elec_e[t] + mDHWload_e[t] + mCHload_e[t];
		tempSum.DHW_load_h[t] = tempSum.DHW_load_h[t] - mDHWout_h[t];
		tempSum.Heat_h[t] = tempSum.Heat_h[t] - mCHout_h[t];
	}

	// Public output data, create private ASHP object in parent
	year_TS mDHWload_e;
	year_TS mDHWout_h;
	year_TS mCHload_e;
	year_TS mCHout_h;
	year_TS mFreeHeat_h;
	year_TS mUsedHotHeat_h;

private:
	const int DHW_OUT_TEMP;
	
	ASHPperf_cl mASHPperfDHW;
	ASHPperf_cl mASHPperfCH;

	const int mTimesteps;
	const float mPowerScalar;
	const int mHotTemp;
	const int mDHWflag;
	const int mCHflag;
	float mHeatPumpMax_h;
	float mHeatPumpMax_e;
	float mElecResidual_e;
	float mAvailHotHeatTemp_h;
	float mMaxElec_e;

	const year_TS mAmbientTemperature;
	year_TS mResidualCapacity;
	year_TS FreeHeatTemp_h;

	ASHP_HE_st mHeatPumpMaxAmbient;	// Max Heat & Elec for Ambient input - Struct: 2x TS
	ASHP_HE_st mHeatPumpMaxHotRoom;	// Max Heat & Elec for Hotroom input - Struct: 2x TS
};