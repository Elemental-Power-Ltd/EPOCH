#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "SiteData.hpp"


class TempSum
{
public:
	TempSum(const SiteData& siteData) :
		// Initilaise temporary vectors with all values to zero
		Elec_e(Eigen::VectorXf::Zero(siteData.timesteps)),	// Electricity energy balance
		Heat_h(Eigen::VectorXf::Zero(siteData.timesteps)), // Building heat energy balance
		DHW_load_h(Eigen::VectorXf::Zero(siteData.timesteps)),   // Hot water energy balance
		Pool_h(Eigen::VectorXf::Zero(siteData.timesteps)),   // Pool energy balance
		Waste_h(Eigen::VectorXf::Zero(siteData.timesteps))   // Waste heat
	{}
	// Public data, can be overwritten
	year_TS Elec_e;
	year_TS Heat_h;
	// The water demand load for DHW
	year_TS DHW_load_h;
	year_TS Pool_h;
	year_TS Waste_h;

	// Report the energy balances before we run the balancing loop
	// this allows us to see the state before components like batteries have been run
	void ReportBeforeBalancingLoop(ReportData& reportData) const {
		reportData._TempSum_elec_e = Elec_e;
		reportData._TempSum_heat_h = Heat_h;
		reportData._TempSum_DHW_load_h = DHW_load_h;
	};

	void Report(ReportData& reportData) const {
		//Grid import breach (capacity shortfall): clamp Elec balance above zero
		reportData.Actual_import_shortfall = Elec_e.cwiseMax(0.0f);
		// Grid export breach (not curtailed): flip Elec and then clamp above zero
		reportData.Actual_curtailed_export = -1.0f * Elec_e;
		reportData.Actual_curtailed_export = reportData.Actual_curtailed_export.cwiseMax(0.0f);
		// Any remaining heat load = a heat shortfall
		reportData.Heat_shortfall = Heat_h + DHW_load_h + Pool_h;
		reportData.DHW_Shortfall = DHW_load_h;
		reportData.CH_shortfall = Heat_h;
		// Any surplus heat generated is wasted (conservation of energy checksum)
		reportData.Heat_surplus = Waste_h;
	}
};