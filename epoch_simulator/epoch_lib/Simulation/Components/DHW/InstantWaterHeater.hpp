#pragma once

#include <Eigen/Core>

#include "../../SiteData.hpp"
#include "../../TempSum.hpp"
#include "../../../Definitions.hpp"


class InstantWaterHeater
{
public: 
	InstantWaterHeater(const SiteData& siteData) :
		mDHW_resistive(Eigen::VectorXf::Zero(siteData.timesteps))
	{}

	void AllCalcs(TempSum& tempSum) {
		mDHW_resistive = tempSum.DHW_load_h;
		tempSum.DHW_load_h.setZero();

		tempSum.Elec_e += mDHW_resistive;
	}

	void Report(ReportData& reportData) {
		reportData.DHW_resistive_load = mDHW_resistive;
	}
private:
	year_TS mDHW_resistive;
};