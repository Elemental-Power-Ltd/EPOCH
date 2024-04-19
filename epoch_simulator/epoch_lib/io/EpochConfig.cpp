#include "EpochConfig.hpp"
#include "FileHandling.hpp"

ConfigHandler::ConfigHandler(std::filesystem::path configDir)
	: mConfigDir(configDir),
	mConfig(parseConfig())
{
}

EpochConfig ConfigHandler::getConfig() const {
	return mConfig;
}


EpochConfig ConfigHandler::parseConfig()
{
	// Load the config from json
	nlohmann::json jsonConfig = readJsonFromFile(mConfigDir / "EpochConfig.json");


	EpochConfig epochConfig{};
	epochConfig.optimiserConfig = parseOptimiserSection(jsonConfig["optimiser"]);

	return epochConfig;
}

OptimiserConfig ConfigHandler::parseOptimiserSection(nlohmann::json optimiserJson)
{
	OptimiserConfig optConfig{};

	optConfig.leagueTableCapacity = getField<int>(optimiserJson, "leagueTableCapacity");
	optConfig.produceExhaustiveOutput = getField<bool>(optimiserJson, "produceExhaustiveOutput");


	return optConfig;
}
