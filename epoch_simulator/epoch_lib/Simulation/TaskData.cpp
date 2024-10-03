#include "Simulate.hpp"  // Include the full header file here
#include "TaskData.hpp"            // Include the current class header

void TaskData::TempSum_cl::Report(FullSimulationResult & Result) const {
    // Implementation that uses FullSimulationResult
    Result.Actual_import_shortfall = Elec_e.cwiseMax(0.0f);
    Result.Actual_curtailed_export = -1.0f * Elec_e;
    Result.Actual_curtailed_export = Result.Actual_curtailed_export.cwiseMax(0.0f);
    Result.Heat_shortfall = Heat_h + DHW_h + Pool_h;
    Result.Heat_surplus = Waste_h;
}