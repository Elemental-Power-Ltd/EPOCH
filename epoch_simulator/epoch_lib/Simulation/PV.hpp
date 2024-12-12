#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskComponents.hpp"
#include "TempSum.hpp"
#include "../Definitions.hpp"

class BasicPV
{
public:
    BasicPV(const HistoricalData& historicalData, const Renewables& renewablesData) :
        mTimesteps(historicalData.timesteps),
        // FUTURE Set PVrect export limit (for clipping)

        mPVdcGen_e(Eigen::VectorXf::Zero(mTimesteps)),
        mPVacGen_e(Eigen::VectorXf::Zero(mTimesteps))
    {
        // FIXME JW - this currently relies on there being exactly 4 entries
        //  rework once historicalData is dynamic

        // use a vector that is exactly four long to prevent IOOB errors
        std::vector<float> exactlyFourScalars(4, 0.0f);
        for (size_t i = 0; i < 4 && i < renewablesData.yield_scalars.size(); i++) {
            exactlyFourScalars[i] = renewablesData.yield_scalars[i];
        }

        mPVdcGen_e = historicalData.RGen_data_1 * exactlyFourScalars[0]
                  + historicalData.RGen_data_2 * exactlyFourScalars[1]
                  + historicalData.RGen_data_3 * exactlyFourScalars[2]
                  + historicalData.RGen_data_4 * exactlyFourScalars[3];
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