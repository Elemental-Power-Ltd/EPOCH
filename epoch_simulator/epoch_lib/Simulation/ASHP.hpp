#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>
#include <algorithm>

#include "TaskData.hpp"
#include "../Definitions.hpp"
#include "ASHPperf.hpp"

// ASHPhot is only used within a DataCentre or alternative heat waste object
class HotRoomHeatPump {

public:
	HotRoomHeatPump(const HistoricalData& historicalData, const TaskData& taskData) :
		// Initialise Persistent Values
		mASHPperf(taskData),
		mTimesteps(taskData.calculate_timesteps()),
		mPowerScalar(taskData.timestep_hours),
		mHotTemp(taskData.ASHP_HotTemp),
		mAmbientTemperature(historicalData.airtemp_data),	// Ambient Temperature

		// Initilaise results data vectors with all values to zero
		Load_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),	// ASHP electrical load
		Heat_h(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),	// ASHP heat output
		FreeHeat_h(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),	// ASHP heat from ambient
		UsedHotHeat_h(Eigen::VectorXf::Zero(taskData.calculate_timesteps()))	// ASHP heat from Hotroom
	{		
		mHeatPumpMaxAmbient.Heat_h = 0;	// For mASHPperf->Lookup results
		mHeatPumpMaxAmbient.Load_e = 0;
		mHeatPumpMaxHotRoom.Heat_h = 0;
		mHeatPumpMaxHotRoom.Load_e = 0;
	}

	const float MaxElec() {
		// Peak kWh per timestep of ASHP
		return mASHPperf.MaxElecLoad();
	}

	void AllCalcs(const year_TS& TargetHeat_h, const year_TS& AvailHotHeat_h) {
		for(int t = 1; t <= mTimesteps; t++) {
			mASHPperf.Lookup(mAmbientTemperature[t], mHeatPumpMaxAmbient);	// 2nd Arg is return values struct
			mASHPperf.Lookup(mHotTemp, mHeatPumpMaxHotRoom);		// 2nd Arg is return values struct
			
			// If TargetHeat < ASHPmax = lower of Hotroom & Ambient+CoE (Conservation of Energy value)
			mHeatPumpMax_h = std::min((mHeatPumpMaxAmbient.Heat_h + AvailHotHeat_h[t]), mHeatPumpMaxHotRoom.Heat_h);
			if(TargetHeat_h[t] <= mHeatPumpMax_h) {
				Heat_h[t] = TargetHeat_h[t];
				Load_e[t] = mHeatPumpMaxHotRoom.Load_e * TargetHeat_h[t] / mHeatPumpMaxHotRoom.Heat_h;
			}
			else {	// ASHP cannot meet TargetHeat, so use values from lower of Hotroom & Amb+CoE
				if(mHeatPumpMaxAmbient.Heat_h <= mHeatPumpMaxHotRoom.Heat_h) {
					Heat_h[t] = mHeatPumpMaxAmbient.Heat_h;
					Load_e[t] = mHeatPumpMaxAmbient.Load_e;
				}
				else {
					Heat_h[t] = mHeatPumpMaxHotRoom.Heat_h;
					Load_e[t] = mHeatPumpMaxHotRoom.Load_e;
				}
			}
		}
		FreeHeat_h = Heat_h - Load_e - AvailHotHeat_h;	// How much heat from ambient
		FreeHeat_h.cwiseMax(0.0f);	// Prevent -ve values where not all AvailHotHeat_h was required
		UsedHotHeat_h = Heat_h - Load_e - FreeHeat_h;
	}

	void StepCalc(const float TargetHeat_h, const float AvailHotHeat_h, const float ElecBudget_e, int t) {
		if(ElecBudget_e <= 0) {
			// No electricty available for the ASHP
			Heat_h[t] = 0;
			Load_e[t] = 0;
		}
		else {
			// Calculate the best the ASHP can do to meet target heat
			mASHPperf.Lookup(mAmbientTemperature[t], mHeatPumpMaxAmbient);	// 2nd Arg is return values struct
			mASHPperf.Lookup(mHotTemp, mHeatPumpMaxHotRoom);		// 2nd Arg is return values struct
			// if TargetHeat < ASHPmax = lower of Hotroom & Ambient+CoE (Conservation of Energy value)
			mHeatPumpMax_h = std::min((mHeatPumpMaxAmbient.Heat_h + AvailHotHeat_h), mHeatPumpMaxHotRoom.Heat_h);
			if(TargetHeat_h <= mHeatPumpMax_h) {
				Heat_h[t] = TargetHeat_h;
				Load_e[t] = mHeatPumpMaxHotRoom.Load_e * TargetHeat_h / mHeatPumpMaxHotRoom.Heat_h;
			}
			else {	// ASHP cannot meet TargetHeat, so use values from lower of Hotroom & Amb+CoE
				if(mHeatPumpMaxAmbient.Heat_h <= mHeatPumpMaxHotRoom.Heat_h) {
					Heat_h[t] = mHeatPumpMaxAmbient.Heat_h;
					Load_e[t] = mHeatPumpMaxAmbient.Load_e;
				}
				else {
					Heat_h[t] = mHeatPumpMaxHotRoom.Heat_h;
					Load_e[t] = mHeatPumpMaxHotRoom.Load_e;
				}
			}
			if(Load_e[t] > ElecBudget_e) {
				// Check whether the ASHP load exceeds the electricity budget, if so, reduce proportionally
				Heat_h[t] = Heat_h[t] * ElecBudget_e / Load_e[t];
				Load_e[t] = ElecBudget_e;
			}
		}
	}

	// Public output data, create private ASHP object in parent
	year_TS Load_e;
	year_TS Heat_h;
	year_TS FreeHeat_h;
	year_TS UsedHotHeat_h;

private:
	ASHPperf_cl mASHPperf;
	
	const int mTimesteps;
	const float mPowerScalar;
	const int mHotTemp;
	float mHeatPumpMax_h;

	const year_TS mAmbientTemperature;

	ASHP_HE_st mHeatPumpMaxAmbient;	// Max Heat & Elec for Ambient input - Struct: 2x TS
	ASHP_HE_st mHeatPumpMaxHotRoom;	// Max Heat & Elec for Hotroom input - Struct: 2x TS
};