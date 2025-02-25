#pragma once

#include <filesystem>

#include <pybind11/pybind11.h>

#include "../epoch_lib/Simulation/Simulate.hpp"



// This class is a thin wrapper around the Simulator class
// to allow creation of a Simulator with less arguments

// In particular that creation of a Simulator_py should read the historical data
// So that this can be provided to the internal Simulator's simulateScenario function

class Simulator_py {
public:
	// We use static factory methods to instantiate the simulator
	// (It's otherwise hard to distinguish whether a string argument is a filepath or a json string)

	static Simulator_py from_file(const std::filesystem::path& path);
	static Simulator_py from_json(const std::string& json_str);

	/**
	* Check if a given TaskData would be valid to run a simulation with the loaded SiteData
	*/
	bool isValid(const TaskData& taskData);
	SimulationResult simulateScenario(const TaskData& taskData, bool fullReporting = false);
	CapexBreakdown calculateCapex(const TaskData& taskData);

private:
	explicit Simulator_py(SiteData&& siteData);

	Simulator mSimulator;
};


