#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>
#include <algorithm>

#include "TaskData.hpp"
#include "../Definitions.hpp"
#include "ASHPperf.hpp"
#include "TempSum.hpp"

// ASHPambient is only used within a HeatPcontrol object
class AmbientHeatPump {

public:
	AmbientHeatPump(const HistoricalData& historicalData, const TaskData& taskData) :
		// Initialise Persistent Values
		DHW_OUT_TEMP(60),	// FUTURE: removed when taskData.ASHP_DHWtemp available
		mASHPperfDHW(taskData, DHW_OUT_TEMP),	// lookup object for DHW performance
		mASHPperfCH(taskData, taskData.ASHP_RadTemp),	// lookup object for CH performance
		mTimesteps(taskData.calculate_timesteps()),
		mDHWflag(1),	// FUTURE: read value from (new) taskData value or use ASHP_DHWtemp not zero
		mCHflag(1),		// FUTURE: read value from (new) taskData value or use ASHP_RadTemp not zero
		mAmbientTemperature(historicalData.airtemp_data),	// Ambient Temperature
		mHeatPumpMax_h(0),
		mHeatPumpMax_e(0),
		mMaxElec_e(0.0f),

		// Initilaise results data vectors with all values to zero
		DHWload_e(Eigen::VectorXf::Zero(mTimesteps)),	// ASHP electrical load
		DHWout_h(Eigen::VectorXf::Zero(mTimesteps)),	// ASHP heat output
		CHload_e(Eigen::VectorXf::Zero(mTimesteps)),	// ASHP electrical load
		CHout_h(Eigen::VectorXf::Zero(mTimesteps)),		// ASHP heat output
		FreeHeat_h(Eigen::VectorXf::Zero(mTimesteps))	// ASHP heat from ambient
	{
		mResidualCapacity = Eigen::VectorXf::Constant(mTimesteps, 1.0f);// Remaining heatpump capacity
		mHeatPumpMaxAmbient.Heat_h = 0;	// For mASHPperf->Lookup results
		mHeatPumpMaxAmbient.Load_e = 0;
	}

	void AllCalcs(TempSum& tempSum) {
		// Applies fixed precedence: hot water is served before central heating
		if (mDHWflag == 1) {
			for (int t = 1; t <= mTimesteps; t++) {
				// Lookup performances for DHW (hot water) output temperature
				mASHPperfDHW.Lookup(mAmbientTemperature[t], mHeatPumpMaxAmbient);	// 2nd Arg is return values struct

				// Adjust output and load to meet heating demand
				if (mHeatPumpMaxAmbient.Heat_h <= 0) {	// If no HeatPump capacity, set values to zero
					DHWout_h[t] = 0;
					DHWload_e[t] = 0;
					mResidualCapacity[t] = 0;
				}
				else if (tempSum.DHW_load_h[t] <= mHeatPumpMaxAmbient.Heat_h) {	// Adjust values to load
					DHWout_h[t] = tempSum.DHW_load_h[t];
					DHWload_e[t] = mHeatPumpMaxAmbient.Load_e * DHWout_h[t] / mHeatPumpMaxAmbient.Heat_h;
					mResidualCapacity[t] = 1 - DHWout_h[t] / mHeatPumpMaxAmbient.Heat_h;
				}
				else {	// ASHP cannot meet heating target, so will do maximum capacity
					DHWout_h[t] = mHeatPumpMaxAmbient.Heat_h;
					DHWload_e[t] = mHeatPumpMaxAmbient.Load_e;
					mResidualCapacity[t] = 0;
				}
			}
			FreeHeat_h = DHWout_h - DHWload_e;	// How much heat from ambient
		}
		if (mCHflag == 1) {
			for (int t = 1; t <= mTimesteps; t++) {
				// Lookup performances for CH (central heating) output temperature
				mASHPperfCH.Lookup(mAmbientTemperature[t], mHeatPumpMaxAmbient);// 2nd Arg is return values struct

					mHeatPumpMax_h = mHeatPumpMaxAmbient.Heat_h * mResidualCapacity[t];
					mHeatPumpMax_e = mHeatPumpMaxAmbient.Load_e * mResidualCapacity[t];
				}
				// Adjust output and load to meet heating demand
				if (mHeatPumpMax_h <= 0) {	// If no HeatPump capacity, set values to zero
					CHout_h[t] = 0;
					CHload_e[t] = 0;
					mResidualCapacity[t] = 0;
				}
				else if (tempSum.Heat_h[t] <= mHeatPumpMax_h) {	// Adjust values to load
					CHout_h[t] = tempSum.Heat_h[t];
					CHload_e[t] = mHeatPumpMax_e * CHout_h[t] / mHeatPumpMax_h;
					mResidualCapacity[t] = mResidualCapacity[t] * (1 - CHout_h[t] / mHeatPumpMax_h);
				}
				else {	// ASHP cannot meet heating target, so will do maximum capacity
					CHout_h[t] = mHeatPumpMax_h;
					CHload_e[t] = mHeatPumpMax_e;
					mResidualCapacity[t] = 0;
				}
			}
			FreeHeat_h = FreeHeat_h + CHout_h - CHload_e;
		}
		tempSum.Elec_e = tempSum.Elec_e + DHWload_e + CHload_e;
		tempSum.DHW_load_h = tempSum.DHW_load_h - DHWout_h;
		tempSum.Heat_h = tempSum.Heat_h - CHout_h;
	}

	void StepCalc(TempSum& tempSum, const float ElecBudget_e, int t) {
		if (ElecBudget_e <= 0) {
			// No electricty available for the ASHP (balancing object)
			DHWout_h[t] = 0;
			DHWload_e[t] = 0;
			CHout_h[t] = 0;
			CHload_e[t] = 0;
			mResidualCapacity[t] = 0;
			mElecResidual_e = 0;
		}
		else {
			if (mDHWflag == 1) {
				// Lookup performances for DHW (hot water) output temperature
				mASHPperfDHW.Lookup(mAmbientTemperature[t], mHeatPumpMaxAmbient);	// 2nd Arg is return values struct

				// Adjust output and load to meet heating demand
				if (mHeatPumpMaxAmbient.Heat_h <= 0) {	// If no HeatPump capacity, set values to zero
					DHWout_h[t] = 0;
					DHWload_e[t] = 0;
					mResidualCapacity[t] = 0;
				}
				else if (tempSum.DHW_load_h[t] <= mHeatPumpMaxAmbient.Heat_h) {	// Adjust values to load
					DHWout_h[t] = tempSum.DHW_load_h[t];
					DHWload_e[t] = mHeatPumpMaxAmbient.Load_e * DHWout_h[t] / mHeatPumpMaxAmbient.Heat_h;
					mResidualCapacity[t] = 1 - DHWout_h[t] / mHeatPumpMaxAmbient.Heat_h;
				}
				else {	// ASHP cannot meet heating target, so will do maximum capacity
					DHWout_h[t] = mHeatPumpMaxAmbient.Heat_h;
					DHWload_e[t] = mHeatPumpMaxAmbient.Load_e;
					mResidualCapacity[t] = 0;
				}
				// Adjust output and load to meet available electricity
				if (DHWload_e[t] > ElecBudget_e) {
					// Check whether the ASHP load exceeds the electricity budget, if so, reduce proportionally
					DHWout_h[t] = DHWout_h[t] * ElecBudget_e / DHWload_e[t];
					DHWload_e[t] = ElecBudget_e;
					mResidualCapacity[t] = (1 - DHWout_h[t] / mHeatPumpMaxAmbient.Heat_h) * ElecBudget_e / DHWload_e[t];
				}
				FreeHeat_h[t] = DHWout_h[t] - DHWload_e[t];	// How much heat from ambient
				mElecResidual_e = ElecBudget_e - DHWload_e[t];
			}
		}
		if (mElecResidual_e <= 0) {
			// No electricty remains for the ASHP CH
			CHout_h[t] = 0;
			CHload_e[t] = 0;
			mResidualCapacity[t] = 0;
		}
		else {
			if (mCHflag == 1) {
				// Lookup performances for CH (central heating) output temperature
				mASHPperfCH.Lookup(mAmbientTemperature[t], mHeatPumpMaxAmbient);	// 2nd Arg is return values struct
				
				mHeatPumpMax_h = mHeatPumpMaxAmbient.Heat_h * mResidualCapacity[t];
				mHeatPumpMax_e = mHeatPumpMaxAmbient.Load_e * mResidualCapacity[t];
				// Adjust output and load to meet heating demand
				if (mHeatPumpMax_h <= 0) {	// If no HeatPump capacity, set values to zero
					CHout_h[t] = 0;
					CHload_e[t] = 0;
					mResidualCapacity[t] = 0;
				}
				else if (tempSum.Heat_h[t] <= mHeatPumpMax_h) {	// Adjust values to load
					CHout_h[t] = tempSum.Heat_h[t];
					CHload_e[t] = mHeatPumpMax_e * CHout_h[t] / mHeatPumpMax_h;
					mResidualCapacity[t] = mResidualCapacity[t] * (1 - CHout_h[t] / mHeatPumpMax_h);
				}
				else {	// ASHP cannot meet heating target, so do maximum capacity
					CHout_h[t] = mHeatPumpMax_h;
					CHload_e[t] = mHeatPumpMax_e;
					mResidualCapacity[t] = 0;
				}
				// Adjust output and load to meet available electricity
				if (CHload_e[t] > mElecResidual_e) {
					// Check whether the ASHP load exceeds the electricity budget, if so, reduce proportionally
					CHout_h[t] = CHout_h[t] * ElecBudget_e / CHload_e[t];
					CHload_e[t] = ElecBudget_e;
					mResidualCapacity[t] = (1 - CHout_h[t] / mHeatPumpMax_h) * ElecBudget_e / CHload_e[t];
				}
				FreeHeat_h[t] = CHout_h[t] - CHload_e[t];	// How much heat from ambient
				mElecResidual_e = mElecResidual_e - CHload_e[t];
			}
		}
		tempSum.Elec_e[t] = tempSum.Elec_e[t] + DHWload_e[t] + CHload_e[t];
		tempSum.DHW_load_h[t] = tempSum.DHW_load_h[t] - DHWout_h[t];
		tempSum.Heat_h[t] = tempSum.Heat_h[t] - CHout_h[t];
	}

	// Public output data, create private ASHP object in parent
	year_TS DHWload_e;
	year_TS DHWout_h;
	year_TS CHload_e;
	year_TS CHout_h;
	year_TS FreeHeat_h;

private:
	const int DHW_OUT_TEMP;

	ASHPperf_cl mASHPperfDHW;
	ASHPperf_cl mASHPperfCH;

	const int mTimesteps;
	const int mHotTemp;
	const int mDHWflag;
	const int mCHflag;
	float mHeatPumpMax_h;
	float mHeatPumpMax_e;
	float mElecResidual_e;
	float mMaxElec_e;

	const year_TS mAmbientTemperature;
	year_TS mResidualCapacity;

	ASHP_HE_st mHeatPumpMaxAmbient;	// Max Heat & Elec for Ambient input - Struct: 2x TS
};