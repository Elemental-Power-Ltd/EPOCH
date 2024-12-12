#pragma once

#include "Simulate.hpp"
#include "TaskData.hpp"
#include "../io/FileConfig.hpp"

// This class is a thin wrapper around the Simulator class
// it is responsible for parsing the site data 

class StandaloneSimualtor {
public:
	StandaloneSimualtor();

	SimulationResult simulateScenario(const TaskData& taskData, bool fullReporting = false);

private:
	FileConfig mFileConfig;
	HistoricalData mHistoricalData;
	Simulator mSimulator;
};