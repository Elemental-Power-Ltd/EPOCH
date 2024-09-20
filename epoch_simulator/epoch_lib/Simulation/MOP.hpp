#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskData.hpp"
#include "../Definitions.hpp"

class MOP
{
public:
	MOP(const TaskData& taskData) :
		mMOPmax_e(taskData.Mop_load_max * taskData.timestep_hours),
		// Initilaise results data vectors with all values to zero
		mMOP_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps()))
	{}

	void AllCalcs(TempSum_cl& TempSum) {
		// VECTOR OPERATIONS APPLY TO ALL TIMESTEPS
		// flip the Elec balance then clamp between 0 and MOPmax to capture surplus generation
		mMOP_e = -1.0f * TempSum.Elec_e;
		mMOP_e = mMOP_e.cwiseMax(0.0f).cwiseMin(mMOPmax_e);
		// Write the new electricity balance to TempSum: Load/Export is +ve & Gen/Import is -ve
		TempSum.Elec_e = TempSum.Elec_e + mMOP_e;
	}

	void Report(FullSimulationResult& Result) {
		//Result.MOP_load = mMOP_e;
	}

private:
	const float mMOPmax_e;
	year_TS mMOP_e;
};