#include "Simulate_py.hpp"

#include <pybind11/pybind11.h>

#include "../epoch_lib/io/FileHandling.hpp"

Simulator_py::Simulator_py() :
	// Construct a default FileConfig to provide the paths for the CSVs
	mHistoricalData{ readHistoricalData(FileConfig{}) },
	mSimulator{}
{
}

SimulationResult Simulator_py::simulateScenario(const Config& config)
{
	// release the GIL for each call to simulateScenario
	pybind11::gil_scoped_release release;
	return mSimulator.simulateScenario(mHistoricalData, config);
}
