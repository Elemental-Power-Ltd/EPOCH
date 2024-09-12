#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskData.hpp"

class TempSum_cl
{
public:
	TempSum_cl(const TaskData& taskData) :
		// Initilaise temporary vectors with all values to zero
		TScount(taskData.calculate_timesteps()),
		Elec_e(Eigen::VectorXf::Zero(TScount)),	// Electricity energy balance
		Heat_h(Eigen::VectorXf::Zero(TScount)), // Building heat energy balance
		DHW_h(Eigen::VectorXf::Zero(TScount)),   // Hot water energy balance
		Pool_h(Eigen::VectorXf::Zero(TScount)),   // Pool energy balance
		Waste_h(Eigen::VectorXf::Zero(TScount))   // Waste heat
	{}
	// Public data, can be overwritten
	year_TS Elec_e;
	year_TS Heat_h;
	year_TS DHW_h;
	year_TS Pool_h;
	year_TS Waste_h;

	void Report(FullSimulationResult& Result) const {
		//Grid import breach (capacity shortfall): clamp Elec balance above zero
		Result.Actual_import_shortfall = Elec_e.cwiseMax(0.0f);
		// Grid export breach (not curtailed): flip Elec and then clamp above zero
		Result.Actual_curtailed_export = -1.0f * Elec_e;
		Result.Actual_curtailed_export = Result.Actual_curtailed_export.cwiseMax(0.0f);
		// Any remaining heat load = a heat shortfall
		Result.Heat_shortfall = Heat_h + DHW_h + Pool_h;
		// Any surplus heat generated is wasted (conservation of energy checksum)
		Result.Heat_surplus = Waste_h;
	}

private:
	int TScount;
};