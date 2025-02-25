#include "Simulate_py.hpp"
#include "../epoch_lib/io/FileHandling.hpp"
#include "../epoch_lib/io/SiteDataJson.hpp"


/**
* Factory method for a Simulator that accepts a filepath to a SiteData.json file
*/
Simulator_py Simulator_py::from_file(const std::filesystem::path& siteDataPath)
{
	SiteData sd = readSiteData(siteDataPath);
	return Simulator_py(std::move(sd));
}

/**
* Factory method for a Simulator that accepts the site data as a json string
*/
Simulator_py Simulator_py::from_json(const std::string& json_str)
{
	SiteData sd = nlohmann::json::parse(json_str).get<SiteData>();
	return Simulator_py(std::move(sd));
}


Simulator_py::Simulator_py(SiteData&& siteData) :
	mSimulator{ std::move(siteData) }
{
}

bool Simulator_py::isValid(const TaskData& taskData)
{
	try {
		mSimulator.validateScenario(taskData);
	}
	catch (const std::runtime_error&) {
		return false;
	}
	return true;
}

SimulationResult Simulator_py::simulateScenario(const TaskData& taskData, bool fullReporting)
{
	// release the GIL for each call to simulateScenario
	pybind11::gil_scoped_release release;

	SimulationType reportingType = fullReporting ? SimulationType::FullReporting : SimulationType::ResultOnly;

	return mSimulator.simulateScenario(taskData, reportingType);
}

CapexBreakdown Simulator_py::calculateCapex(const TaskData& taskData) {
	return mSimulator.calculateCapex(taskData);
}