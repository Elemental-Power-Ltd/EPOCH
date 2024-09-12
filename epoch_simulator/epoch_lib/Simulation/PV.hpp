#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "TaskData.hpp"
#include "../Definitions.hpp"

class PVbasic_cl
{
public:
    PVbasic_cl(const HistoricalData& historicalData, const TaskData& taskData) :
        // Initialise Persistent Values
        TScount(taskData.calculate_timesteps()),	// Used in init & functions
        // FUTURE Set PVrect export limit (for clipping)
        // Initilaise data vectors with all values to zero
        PVdcGen_e(Eigen::VectorXf::Zero(TScount)),
        PVacGen_e(Eigen::VectorXf::Zero(TScount))
    {
        PVdcGen_e = historicalData.RGen_data_1 * taskData.ScalarRG1
                  + historicalData.RGen_data_2 * taskData.ScalarRG2
                  + historicalData.RGen_data_3 * taskData.ScalarRG3
                  + historicalData.RGen_data_4 * taskData.ScalarRG4;
    }

    void AllCalcs() {
        // FUTURE: Apply oversizing
        PVdcGen_e = PVacGen_e;
    }

    void Report(FullSimulationResult &Result) {
        // report target load to allow calculation of revenue missed
        //Result.PVdcGen = PVdcGen_e;
        //Result.PVacGen = PVacGen_e;
    }

private:
    const int TScount;

    year_TS PVdcGen_e;
    year_TS PVacGen_e;
};