#pragma once

#include <string>

#include <pybind11/pybind11.h>

#include "../epoch_lib/Definitions.hpp"

// define toString methods for the structs that we expose to Python
std::string resultToString(const SimulationResult& result);
std::string taskDataToString(const TaskData& taskData);
