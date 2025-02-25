#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskComponents.hpp"
#include "TempSum.hpp"
#include "../Definitions.hpp"

class BasicPV
{
public:
    BasicPV(const SiteData& siteData, const Renewables& renewablesData) :
        mTimesteps(siteData.timesteps),
        // FUTURE Set PVrect export limit (for clipping)

        mPVdcGen_e(Eigen::VectorXf::Zero(mTimesteps)),
        mPVacGen_e(Eigen::VectorXf::Zero(mTimesteps))
    {
        // We should have already verified that solar_yields and yield_scalars are compatible
        assert(siteData.solar_yields.size() >= renewablesData.yield_scalars.size());

        for (size_t i = 0; i < renewablesData.yield_scalars.size(); i++) {
            mPVdcGen_e += siteData.solar_yields[i] * renewablesData.yield_scalars[i];
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