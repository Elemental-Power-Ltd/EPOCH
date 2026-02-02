#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>
#include <algorithm>

#include "SiteData.hpp"
#include "TaskComponents.hpp"
#include "../Definitions.hpp"
#include "ASHPLookup.hpp"
#include "TempSum.hpp"

// ASHPambient is only used within a AmbientHeatPumpController object
class AmbientHeatPump {

public:
	AmbientHeatPump(const SiteData& siteData, const HeatPumpData& hp, bool suppliesDHW) :
		// Initialise results data vectors with all values to zero
		mDHWload_e(Eigen::VectorXf::Zero(siteData.timesteps)),	// ASHP electrical load
		mDHWout_h(Eigen::VectorXf::Zero(siteData.timesteps)),	// ASHP heat output
		mCHload_e(Eigen::VectorXf::Zero(siteData.timesteps)),	// ASHP electrical load
		mCHout_h(Eigen::VectorXf::Zero(siteData.timesteps)),		// ASHP heat output
		mFreeHeat_h(Eigen::VectorXf::Zero(siteData.timesteps)),	// ASHP heat from ambient
		// Initialise Persistent Values
		DHW_OUT_TEMP(60),	// FUTURE: removed when taskData.ASHP_DHWtemp available
		mASHPperfDHW(siteData, hp, FIXED_SEND_TEMP_VAL),	// lookup object for DHW performance
		mASHPperfCH(siteData, hp, FIXED_SEND_TEMP_VAL),	// lookup object for CH performance
		mTimesteps(siteData.timesteps),
		mHeatpumpSuppliesDHW(suppliesDHW),
		mHeatpumpSuppliesCentralHeating(true),		// FUTURE: read value from (new) taskData value or use ASHP_RadTemp not zero
		mHeatPumpMax_h(0),
		mHeatPumpMax_e(0),
		mMaxElec_e(0.0f),
		mAmbientTemperature(siteData.air_temperature)	// Ambient Temperature
	{
		mResidualCapacity = Eigen::VectorXf::Constant(siteData.timesteps, 1.0f);// Remaining heatpump capacity
	}

	void AllCalcs(TempSum& tempSum) {
		// Applies fixed precedence: hot water is served before central heating

		for (size_t t = 0; t < mTimesteps; t++) {

			if (mHeatpumpSuppliesDHW) {
				// Lookup performances for DHW (hot water) output temperature
				HeatpumpValues ambientDHW = mASHPperfDHW.Lookup(mAmbientTemperature[t]);

				// Adjust output and load to meet heating demand
				if (ambientDHW.Heat_h <= 0) {	// If no HeatPump capacity, set values to zero
					mDHWout_h[t] = 0;
					mDHWload_e[t] = 0;
					mResidualCapacity[t] = 0;
				}
				else if (tempSum.DHW_load_h[t] <= ambientDHW.Heat_h) {	// Adjust values to load
					mDHWout_h[t] = tempSum.DHW_load_h[t];
					mDHWload_e[t] = ambientDHW.Load_e * mDHWout_h[t] / ambientDHW.Heat_h;
					mResidualCapacity[t] = 1 - mDHWout_h[t] / ambientDHW.Heat_h;
				}
				else {	// ASHP cannot meet heating target, so will do maximum capacity
					mDHWout_h[t] = ambientDHW.Heat_h;
					mDHWload_e[t] = ambientDHW.Load_e;
					mResidualCapacity[t] = 0;
				}
			}
			mFreeHeat_h[t] = mDHWout_h[t] - mDHWload_e[t];	// How much heat from ambient

			if (mHeatpumpSuppliesCentralHeating) {
				// Lookup performances for CH (central heating) output temperature
				HeatpumpValues ambientCH = mASHPperfCH.Lookup(mAmbientTemperature[t]);

				mHeatPumpMax_h = ambientCH.Heat_h * mResidualCapacity[t];
				mHeatPumpMax_e = ambientCH.Load_e * mResidualCapacity[t];
				
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
			}
			mFreeHeat_h[t] = mFreeHeat_h[t] + mCHout_h[t] - mCHload_e[t];
		}
		tempSum.Elec_e = tempSum.Elec_e + mDHWload_e + mCHload_e;
		tempSum.DHW_load_h = tempSum.DHW_load_h - mDHWout_h;
		tempSum.Heat_h = tempSum.Heat_h - mCHout_h;
	}

	void StepCalc(TempSum& tempSum, const float ElecBudget_e, int t) {
		if (ElecBudget_e <= 0) {
			// No electricty available for the ASHP (balancing object)
			mDHWout_h[t] = 0;
			mDHWload_e[t] = 0;
			mCHout_h[t] = 0;
			mCHload_e[t] = 0;
			mResidualCapacity[t] = 0;
			mElecResidual_e = 0;
		}
		else {
			if (mHeatpumpSuppliesDHW) {
				// Lookup performances for DHW (hot water) output temperature
				HeatpumpValues ambientDHW = mASHPperfDHW.Lookup(mAmbientTemperature[t]);

				// Adjust output and load to meet heating demand
				if (ambientDHW.Heat_h <= 0) {	// If no HeatPump capacity, set values to zero
					mDHWout_h[t] = 0;
					mDHWload_e[t] = 0;
					mResidualCapacity[t] = 0;
				}
				else if (tempSum.DHW_load_h[t] <= ambientDHW.Heat_h) {	// Adjust values to load
					mDHWout_h[t] = tempSum.DHW_load_h[t];
					mDHWload_e[t] = ambientDHW.Load_e * mDHWout_h[t] / ambientDHW.Heat_h;
					mResidualCapacity[t] = 1 - mDHWout_h[t] / ambientDHW.Heat_h;
				}
				else {	// ASHP cannot meet heating target, so will do maximum capacity
					mDHWout_h[t] = ambientDHW.Heat_h;
					mDHWload_e[t] = ambientDHW.Load_e;
					mResidualCapacity[t] = 0;
				}
				// Adjust output and load to meet available electricity
				if (mDHWload_e[t] > ElecBudget_e) {
					// Check whether the ASHP load exceeds the electricity budget, if so, reduce proportionally
					mDHWout_h[t] = mDHWout_h[t] * ElecBudget_e / mDHWload_e[t];
					mDHWload_e[t] = ElecBudget_e;
					mResidualCapacity[t] = (1 - mDHWout_h[t] / ambientDHW.Heat_h) * ElecBudget_e / mDHWload_e[t];
				}
				mFreeHeat_h[t] = mDHWout_h[t] - mDHWload_e[t];	// How much heat from ambient
				mElecResidual_e = ElecBudget_e - mDHWload_e[t];
			}
		}
		if (mElecResidual_e <= 0) {
			// No electricty remains for the ASHP CH
			mCHout_h[t] = 0;
			mCHload_e[t] = 0;
			mResidualCapacity[t] = 0;
		}
		else {
			if (mHeatpumpSuppliesCentralHeating) {
				// Lookup performances for CH (central heating) output temperature
				HeatpumpValues ambientCH = mASHPperfCH.Lookup(mAmbientTemperature[t]);
				
				mHeatPumpMax_h = ambientCH.Heat_h * mResidualCapacity[t];
				mHeatPumpMax_e = ambientCH.Load_e * mResidualCapacity[t];
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
				mFreeHeat_h[t] = mCHout_h[t] - mCHload_e[t];	// How much heat from ambient
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

private:
	const int DHW_OUT_TEMP;

	ASHPLookup mASHPperfDHW;
	ASHPLookup mASHPperfCH;

	const size_t mTimesteps;
	bool mHeatpumpSuppliesDHW;
	bool mHeatpumpSuppliesCentralHeating;
	float mHeatPumpMax_h;
	float mHeatPumpMax_e;
	float mElecResidual_e;
	float mMaxElec_e;

	const year_TS mAmbientTemperature;
	year_TS mResidualCapacity;
};