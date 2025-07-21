#include "Simulate_py.hpp"

#include "../epoch_lib/io/EpochConfig.hpp"
#include "../epoch_lib/io/FileHandling.hpp"
#include "../epoch_lib/io/SiteDataJson.hpp"
#include "../epoch_lib/io/TaskConfigJson.hpp"

/**
* Factory method for a Simulator that accepts filepaths to a SiteData.json and epochConfig.json
*/
Simulator_py Simulator_py::from_file(const std::filesystem::path& siteDataPath, const std::filesystem::path& configPath)
{
	SiteData sd = readSiteData(siteDataPath);

	ConfigHandler configHandler(configPath);
	
	return Simulator_py(std::move(sd), configHandler.getConfig().taskConfig);
}

/**
* Factory method for a Simulator that accepts the site data as a json string
*/
Simulator_py Simulator_py::from_json(const std::string& site_data_json_str, const std::string& config_json_str)
{
	SiteData sd = nlohmann::json::parse(site_data_json_str).get<SiteData>();
	TaskConfig config = nlohmann::json::parse(config_json_str).get<TaskConfig>();
	return Simulator_py(std::move(sd), config);
}


Simulator_py::Simulator_py(SiteData&& siteData, TaskConfig taskConfig) :
	config(taskConfig),
	mSimulator{ std::move(siteData), config }
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

CapexBreakdown Simulator_py::calculateCapexWithDiscounts(const TaskData& taskData) {
	return mSimulator.calculateCapexWithDiscounts(taskData);
}