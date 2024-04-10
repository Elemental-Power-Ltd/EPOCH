#pragma once

#include "../epoch_lib/Simulation/Simulate.hpp"

// This class is a thin wrapper around the Simulator class
// to allow creation of a Simulator with less arguments

// In particular that creation of a Simulator_py should read the historical data
// So that this can be provided to the internal Simulator's simulateScenario function

class Simulator_py {
public:
	Simulator_py();

	SimulationResult simulateScenario(const Config& config);

private:
	Simulator mSimulator;
	HistoricalData mHistoricalData;
};


