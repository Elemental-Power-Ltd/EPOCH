#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskData.hpp"
#include "../Definitions.hpp"

class MOP_cl
{
public:
	MOP_cl(const TaskData& taskData) :
		MOPmax_e(taskData.Mop_load_max * taskData.timestep_hours),
		// Initilaise results data vectors with all values to zero
		MOP_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps()))
	{}

	void AllCalcs(TempSum_cl& TempSum) {
		// VECTOR OPERATIONS APPLY TO ALL TIMESTEPS
		// flip the Elec balance then clamp between 0 and MOPmax to capture surplus generation
		MOP_e = -1.0f * TempSum.Elec_e;
		MOP_e = MOP_e.cwiseMax(0.0f).cwiseMin(MOPmax_e);
		// Write the new electricity balance to TempSum: Load/Export is +ve & Gen/Import is -ve
		TempSum.Elec_e = TempSum.Elec_e + MOP_e;
	}

	void Report(FullSimulationResult& Result) {
		Result.MOP_load = MOP_e;
	}

private:
	const float MOPmax_e;
	year_TS MOP_e;
};