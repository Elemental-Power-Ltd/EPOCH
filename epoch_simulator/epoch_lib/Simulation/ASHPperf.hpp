#pragma once

#include "TaskData.hpp"

// TODO
// guess at what this struct needs to contain
struct ASHP_HE_st {
	float Heat_h;
	float Load_e;
};

class ASHPperf_cl
{
public:
	ASHPperf_cl(const TaskData& taskData, const int& outputMode) :

		// TODO
		// outputMode is the taskData.ASHP_RadTemp (or new .ASHP_DHWtemp)
		// FUDGED WITH FIXED VALUES
		// UNFUDGE: Initilaise lookup tables using historicalData.ASHPinputtable .ASHPoutputtable
		mMaxLoad_e(taskData.timestep_hours * 0.5f * taskData.ASHP_HPower),
		mMaxHeat_h(taskData.timestep_hours * 2.0f * taskData.ASHP_HPower)
	{}

	float MaxElecLoad() const {
		// We always return the maximum theoretical load from the heatpump
		// This avoids throttling calculations when there is adequate power
		return mMaxLoad_e;
	}

	void Lookup(const float TargetHeat_h, ASHP_HE_st& ASHPoutputs) {
		// FUDGE: Needs to convert TargetHeat_h to int and lookup in perf tables
		ASHPoutputs.Heat_h = mMaxHeat_h;
		ASHPoutputs.Load_e = mMaxLoad_e;
	}


private:
	// Lookup arrays: Index Input temp, output max Heat & max electricity
	const float mMaxLoad_e;
	const float mMaxHeat_h;
};