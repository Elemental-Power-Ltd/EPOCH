#include "Simulate_py.hpp"

#include "../io/FileHandling.hpp"

Simulator_py::Simulator_py():
	// Construct a default FileConfig to provide the paths for the CSVs
	mHistoricalData{ readHistoricalData(FileConfig{}) },
	mSimulator{}
{
}

SimulationResult Simulator_py::simulateScenario(const Config& config)
{
	return mSimulator.simulateScenario(mHistoricalData, config);
}
