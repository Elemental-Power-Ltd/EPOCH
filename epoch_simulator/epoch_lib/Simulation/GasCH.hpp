#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskData.hpp"
#include "../Definitions.hpp"

class GasCombustionHeater
{
public:
	GasCombustionHeater(const TaskData& taskData) :
		mTimesteps(taskData.calculate_timesteps()),	// Used in init & functions
		// FUTURE: Add GasCH power limit in task data
			// GasCHmax_e(taskData.GasCH_heatpwr * taskData.timestep_hours),
		// Initilaise results data vector with all values to zero
		mGasCH_e(Eigen::VectorXf::Zero(mTimesteps))
	{}

	void AllCalcs(TempSum& tempSum) {
		// VECTOR OPERATIONS APPLY TO ALL TIMESTEPS
		// Clamp between 0 and GasCHmax to capture addressable heat load
			//mGasCH_e = tempSum.Heat_e.cwiseMax(0.0f).cwiseMin(GasCHmax_e);
		
		// Assume infinite GasCH power provides all remaining heat load and Heat_h not -ve
		mGasCH_e = tempSum.Heat_h;
		tempSum.Heat_h(Eigen::VectorXf::Zero(mTimesteps));

		//FUTURE: Enable GasCH to heat DHW (and poss pool)
		//mGasCH_e = mGasCH_e + tempSum.DHW_load_h;
		//tempSum.DHW_load_h(Eigen::VectorXf::Zero(mTimesteps);
		//mGasCH_e = mGasCH_e + tempSum.Pool_h;
		//tempSum.Pool_h(Eigen::VectorXf::Zero(mTimesteps);
	}

	void Report(FullSimulationResult& Result) {
		Result.GasCH_load = mGasCH_e;
	}

private:
	const int mTimesteps;
	// const float GasCHmax_e;
	year_TS mGasCH_e;
};