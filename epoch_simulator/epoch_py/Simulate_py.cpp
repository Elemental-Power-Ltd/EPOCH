#include "Simulate_py.hpp"

#include <pybind11/pybind11.h>

#include "../epoch_lib/io/FileHandling.hpp"
#include "../epoch_lib/io/FileConfig.hpp"


Simulator_py::Simulator_py(const std::string& input_dir, const std::string& output_dir, const std::string& config_dir) :
	// Construct a default FileConfig to provide the paths for the CSVs
	mHistoricalData{ readHistoricalData(FileConfig(input_dir, output_dir, config_dir))},
	mSimulator{}
{
}

SimulationResult Simulator_py::simulateScenario(const TaskData& taskData)
{
	// release the GIL for each call to simulateScenario
	pybind11::gil_scoped_release release;
	return mSimulator.simulateScenario(mHistoricalData, taskData);
}
