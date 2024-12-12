#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskComponents.hpp"
#include "../Definitions.hpp"

class Grid
{
public:
	Grid(const HistoricalData& historicalData, const GridData& gridData, const Building& building) :
		// Initilaise results data vectors with all values to zero
		Imp_e(Eigen::VectorXf::Zero(historicalData.timesteps)),
		Exp_e(Eigen::VectorXf::Zero(historicalData.timesteps)),
		ImpHeadroom_e(gridData.import_headroom * building.scalar_electrical_load * historicalData.hotel_eload_data.maxCoeff()),
		// Following are Import and Export Max kWh per timestep (adjusted for Power Factor & Headroom)
		ImpMax_e((gridData.grid_import * gridData.min_power_factor - ImpHeadroom_e) * historicalData.timestep_hours),
		ExpMax_e(gridData.grid_export * historicalData.timestep_hours)
	{}

	float AvailImport() const {
		return ImpMax_e;
	}

	float AvailExport() const {
		return ExpMax_e;
	}

	void AllCalcs(TempSum& tempSum) {
		// VECTOR OPERATIONS APPLY TO ALL TIMESTEPS
		// clamp the grid import between 0 and Import Max at each timestep
		Imp_e = tempSum.Elec_e.cwiseMax(0.0f).cwiseMin(ImpMax_e);
		// flip the ESUM then clamp between 0 and Export Max at each timestep
		Exp_e = -1.0f * tempSum.Elec_e;
		Exp_e = Exp_e.cwiseMax(0.0f).cwiseMin(ExpMax_e);
		// Write the new electricity balance to tempSum: Load/Export is +ve & Gen/Import is -ve
		tempSum.Elec_e = tempSum.Elec_e + Exp_e - Imp_e;
	}

	void Report(ReportData& reportData) {
		reportData.Grid_Import = Imp_e;
		reportData.Grid_Export = Exp_e;
	}

	// Can't go direct to Acc values for 'SimulationResult' as Import & Export vectors required for Supplier ToU costs

private:
	const float ImpHeadroom_e;
	const float ImpMax_e;
	const float ExpMax_e;

	year_TS Imp_e;
	year_TS Exp_e;
};