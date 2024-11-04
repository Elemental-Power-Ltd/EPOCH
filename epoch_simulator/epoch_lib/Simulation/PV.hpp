#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskData.hpp"
#include "TempSum.hpp"
#include "../Definitions.hpp"

class BasicPV
{
public:
    BasicPV(const HistoricalData& historicalData, const TaskData& taskData) :
        // Initialise Persistent Values
        mTimesteps(taskData.calculate_timesteps()),	// Used in init & functions
        // FUTURE Set PVrect export limit (for clipping)
        // Initilaise data vectors with all values to zero
        mPVdcGen_e(Eigen::VectorXf::Zero(mTimesteps)),
        mPVacGen_e(Eigen::VectorXf::Zero(mTimesteps))
    {
        mPVdcGen_e = historicalData.RGen_data_1 * taskData.ScalarRG1
                  + historicalData.RGen_data_2 * taskData.ScalarRG2
                  + historicalData.RGen_data_3 * taskData.ScalarRG3
                  + historicalData.RGen_data_4 * taskData.ScalarRG4;
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
    const int mTimesteps;

    year_TS mPVdcGen_e;
    year_TS mPVacGen_e;
};