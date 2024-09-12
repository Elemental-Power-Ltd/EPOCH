#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskData.hpp"
#include "../Definitions.hpp"

class GasCH_cl
{
public:
	GasCH_cl(const TaskData& taskData) :
		TScount(taskData.calculate_timesteps()),	// Used in init & functions
		// FUTURE: Add GasCH power limit in task data
			// GasCHmax_e(taskData.GasCH_heatpwr * taskData.timestep_hours),
		// Initilaise results data vector with all values to zero
		GasCH_e(Eigen::VectorXf::Zero(TScount))
	{}

	void AllCalcs(TempSum_cl& TempSum) {
		// VECTOR OPERATIONS APPLY TO ALL TIMESTEPS
		// Clamp between 0 and GasCHmax to capture addressable heat load
			//GasCH_e = TempSum.Heat_e.cwiseMax(0.0f).cwiseMin(GasCHmax_e);
		
		// Assume infinite GasCH power provides all remaining heat load and Heat_h not -ve
		GasCH_e = TempSum.Heat_h;
		TempSum.Heat_h(Eigen::VectorXf::Zero(TScount));

		//FUTURE: Enable GasCH to heat DHW (and poss pool)
		//GasCH_e = GasCH_e + TempSum.DHW_h;
		//TempSum.DHW_h(Eigen::VectorXf::Zero(TScount);
		//GasCH_e = GasCH_e + TempSum.Pool_h;
		//TempSum.Pool_h(Eigen::VectorXf::Zero(TScount);
	}

	void Report(FullSimulationResult& Result) {
		Result.GasCH_load = GasCH_e;
	}

private:
	const int TScount;
	// const float GasCHmax_e;
	year_TS GasCH_e;
};