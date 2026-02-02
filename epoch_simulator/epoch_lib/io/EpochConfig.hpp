#pragma once

#include <filesystem>
#include <nlohmann/json.hpp>
#include <spdlog/spdlog.h>

#include "../Exceptions.hpp"
#include "../Simulation/TaskConfig.hpp"


struct EpochConfig {
	TaskConfig taskConfig;
};

class ConfigHandler {
public:
	ConfigHandler(std::filesystem::path configPath);
	EpochConfig getConfig() const;

private:
	EpochConfig parseConfig();

	std::filesystem::path mConfigPath;
	EpochConfig mConfig;
};

// Templated function to read nlohmann json fields and throw a useful exception message if they are not present or the wrong type
template <typename T>
T getField(const nlohmann::json& json, const std::string & fieldName) {
	try {
		if (!json.contains(fieldName)) {
			throw ConfigException(fieldName + " is not present in the config file. Expected a value of type " + typeid(T).name());
		}

		T field = json[fieldName];
		return field;
	}
	catch (const std::exception& e) {
		spdlog::error("Failed to read " + fieldName + " from the config");
		throw ConfigException(e.what());
	}
}