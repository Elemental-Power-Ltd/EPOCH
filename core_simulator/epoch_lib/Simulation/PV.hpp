#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskComponents.hpp"
#include "TempSum.hpp"
#include "../Definitions.hpp"

class BasicPV
{
public:
    BasicPV(const SiteData& siteData, const std::vector<SolarData>& solar_panels) :
        mTimesteps(siteData.timesteps),
        // FUTURE Set PVrect export limit (for clipping)

        mPVdcGen_e(Eigen::VectorXf::Zero(mTimesteps)),
        mPVacGen_e(Eigen::VectorXf::Zero(mTimesteps))
    {
        for (const SolarData& solar : solar_panels) {
            mPVdcGen_e += siteData.solar_yields[solar.yield_index] * solar.yield_scalar;
        }
    }

    void AllCalcs(TempSum& tempSum) {
        // FUTURE: Apply oversizing
        mPVacGen_e = mPVdcGen_e;

        // Subtract PV generation from the electrical demand
        tempSum.Elec_e -= mPVacGen_e;
    }

    year_TS get_PV_AC_out() const {
        return mPVacGen_e;
    }

    void Report(ReportData& reportData) {
        // report target load to allow calculation of revenue missed
        reportData.PVdcGen = mPVdcGen_e;
        reportData.PVacGen = mPVacGen_e;
    }

private:
    const size_t mTimesteps;

    year_TS mPVdcGen_e;
    year_TS mPVacGen_e;
};