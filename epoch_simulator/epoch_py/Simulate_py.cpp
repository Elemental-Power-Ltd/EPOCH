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
		return mSimulator.simulateScenario(mHistoricalData, taskData, SimulationType::FullReporting);
	} 

	return mSimulator.simulateScenario(mHistoricalData, taskData, SimulationType::ResultOnly);
}
