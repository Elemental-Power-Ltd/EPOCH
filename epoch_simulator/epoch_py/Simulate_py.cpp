#include "Simulate_py.hpp"

#include <pybind11/pybind11.h>

#include "../epoch_lib/io/FileHandling.hpp"
#include "../epoch_lib/io/FileConfig.hpp"


Simulator_py::Simulator_py(const std::string& input_dir, const std::string& output_dir, const std::string& config_dir) :
	mFileConfig(input_dir, output_dir, config_dir),
	mHistoricalData{ readHistoricalData(mFileConfig)},
	mSimulator{}
{
}

SimulationResult Simulator_py::simulateScenario(const TaskData& taskData, bool fullReporting)
{
	// release the GIL for each call to simulateScenario
	pybind11::gil_scoped_release release;

	if (fullReporting) {
		FullSimulationResult fullSimulationResult = mSimulator.simulateScenarioFull(mHistoricalData, taskData, SimulationType::FullReporting);

		// Temporary Feature:
		// When we call for fullReporting from Python, write the fullResult to a CSV
		auto fp = mFileConfig.getOutputDir() / "FullTimeSeries.csv";

		// note: deliberately not try-catching this
		// this will crash the program if it cannot write to file (ie the csv is open in Excel!)
		writeTimeSeriesToCSV(fp, fullSimulationResult);


		SimulationResult simResult;

		simResult.runtime = fullSimulationResult.runtime;
		simResult.paramIndex = fullSimulationResult.paramIndex;
		simResult.total_annualised_cost = fullSimulationResult.total_annualised_cost;
		simResult.project_CAPEX = fullSimulationResult.project_CAPEX;
		simResult.scenario_cost_balance = fullSimulationResult.scenario_cost_balance;
		simResult.payback_horizon_years = fullSimulationResult.payback_horizon_years;
		simResult.scenario_carbon_balance = fullSimulationResult.scenario_carbon_balance;

		return simResult;
	} 

	return mSimulator.simulateScenario(mHistoricalData, taskData);
}
