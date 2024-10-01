#pragma once

#include <pybind11/pybind11.h>


#include "../epoch_lib/Simulation/Simulate.hpp"
#include "../epoch_lib/io/FileHandling.hpp"
#include "../epoch_lib/io/FileConfig.hpp"



// This class is a thin wrapper around the Simulator class
// to allow creation of a Simulator with less arguments

// In particular that creation of a Simulator_py should read the historical data
// So that this can be provided to the internal Simulator's simulateScenario function

class Simulator_py {
public:
	Simulator_py(const std::string& input_dir, const std::string& output_dir, const std::string& config_dir);

	SimulationResult simulateScenario(const TaskData& taskData, bool fullReporting = false);

private:
	FileConfig mFileConfig;
	HistoricalData mHistoricalData;
	Simulator mSimulator;
};


