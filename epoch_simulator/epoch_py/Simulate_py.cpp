#include "Simulate_py.hpp"

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
		SimulationResult simResult = mSimulator.simulateScenario(mHistoricalData, taskData, SimulationType::FullReporting);

		// Temporary Feature:
		// When we call for fullReporting from Python, write the fullResult to a CSV
		auto fp = mFileConfig.getOutputDir() / "FullTimeSeries.csv";

		// note: deliberately not try-catching this
		// this will crash the program if it cannot write to file (ie the csv is open in Excel!)
		writeTimeSeriesToCSV(fp, *simResult.report_data);


		return simResult;
	} 

	return mSimulator.simulateScenario(mHistoricalData, taskData);
}
