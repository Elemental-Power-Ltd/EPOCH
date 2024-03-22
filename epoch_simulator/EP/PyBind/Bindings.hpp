#pragma once

#ifdef PYTHON_BINDINGS

#include <string>

#include <pybind11/pybind11.h>

#include "../Definitions.h"

// define toString methods for the structs that we expose to Python
std::string resultToString(const SimulationResult& result);
std::string configToString(const Config& config);


#endif 
