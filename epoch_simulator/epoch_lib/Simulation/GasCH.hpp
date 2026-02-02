#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "../Definitions.hpp"
#include "SiteData.hpp"

class GasCombustionHeater
{
public:
	GasCombustionHeater(const SiteData& siteData, GasCHData gasData) :
		mTimesteps(siteData.timesteps),
		mMaxOutput(gasData.maximum_output * siteData.timestep_hours),
		mEfficiency(gasData.boiler_efficiency),
		mGasCH_h(Eigen::VectorXf::Zero(mTimesteps))
	{}

	void AllCalcs(TempSum& tempSum) {

		year_TS heaterCapacity = Eigen::VectorXf::Constant(mTimesteps, mMaxOutput);

		// First try to meet the remaining DHW heating demand
		year_TS gasForDHW_h = tempSum.DHW_load_h.cwiseMax(0.0f).cwiseMin(heaterCapacity);
		heaterCapacity -= gasForDHW_h;
		tempSum.DHW_load_h -= gasForDHW_h;
		mGasCH_h = gasForDHW_h;

		// Then try to meet the remaining building heating demand
		year_TS gasForBuilding_h = tempSum.Heat_h.cwiseMax(0.0f).cwiseMin(heaterCapacity);
		heaterCapacity -= gasForBuilding_h;
		tempSum.Heat_h -= gasForBuilding_h;
		mGasCH_h += gasForBuilding_h;

		// Finally try to meet the remaing pool heat
		year_TS gasForPool_h = tempSum.Pool_h.cwiseMax(0.0f).cwiseMin(heaterCapacity);
		heaterCapacity -= gasForPool_h;
		tempSum.Pool_h -= gasForPool_h;
		mGasCH_h += gasForPool_h;

		// finally, divide by the efficiency to calculate the input energy needed
		mGasCH_h /= mEfficiency;
	}

	void Report(ReportData& reportData) {
		reportData.GasCH_load = mGasCH_h;
	}

private:
	const size_t mTimesteps;
	float mMaxOutput;
	float mEfficiency;
	year_TS mGasCH_h;
};