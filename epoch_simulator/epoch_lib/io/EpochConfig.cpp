#include "EpochConfig.hpp"
#include "FileHandling.hpp"
#include "TaskConfigJson.hpp"

ConfigHandler::ConfigHandler(std::filesystem::path configPath)
	: mConfigPath(configPath),
	mConfig(parseConfig())
{
}

EpochConfig ConfigHandler::getConfig() const {
	return mConfig;
}


EpochConfig ConfigHandler::parseConfig()
{
	// Load the config from json
	nlohmann::json jsonConfig = readJsonFromFile(mConfigPath);


	EpochConfig epochConfig{};

	epochConfig.taskConfig = jsonConfig["simulator"].get<TaskConfig>();

	return epochConfig;
}
