#include "Simulate_py.hpp"

#include <pybind11/pybind11.h>

#include "../epoch_lib/io/FileHandling.hpp"
#include "../epoch_lib/io/FileConfig.h"


Simulator_py::Simulator_py() :
	// Construct a default FileConfig to provide the paths for the CSVs
	mHistoricalData{ readHistoricalData(FileConfig("./InputData", "./OutputData", "./ConfigData"))},
	mSimulator{}
{
}

SimulationResult Simulator_py::simulateScenario(const TaskData& taskData)
{
	// release the GIL for each call to simulateScenario
	pybind11::gil_scoped_release release;
	return mSimulator.simulateScenario(mHistoricalData, taskData);
}
