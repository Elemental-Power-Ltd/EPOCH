#include <gtest/gtest.h>

#include <filesystem>
#include <fstream>

#include "../epoch_lib/io/FileConfig.hpp"
#include "../epoch_lib/Optimisation/Optimiser.hpp"
#include "../epoch_lib/io/FileHandling.hpp"
#include "../epoch_lib/io/EpochConfig.hpp"

namespace fs = std::filesystem;

TEST(EpochFullRun, MatchesKnownOutput) {
	FileConfig fileConfig = FileConfig{
		"KnownInput", "OutputData", "Config"
	};

	ConfigHandler configHandler(fileConfig.getConfigDir());
	Optimiser opt = Optimiser(fileConfig, configHandler.getConfig());

	// Run the Optimiser on known input
	auto inputJson = readJsonFromFile(fileConfig.getInputJsonFilepath());
	OutputValues testOutput = opt.runOptimisation(inputJson);
	auto testJson = outputToJson(testOutput);

	//// Load the known output
	fs::path knownOutputFile = fs::path{ "KnownOutput" } / fs::path{ "knownOutput.json" };
	auto knownJson = readJsonFromFile(knownOutputFile);

	EXPECT_EQ(testJson["CAPEX"], knownJson["CAPEX"]);

	EXPECT_EQ(testJson["annualised"], knownJson["annualised"]);

	EXPECT_EQ(testJson["scenario_cost_balance"], knownJson["scenario_cost_balance"]);

	EXPECT_EQ(testJson["payback_horizon"], knownJson["payback_horizon"]);

	// This is the scope 1 emissions
	EXPECT_EQ(testJson["scenario_carbon_balance"], knownJson["scenario_carbon_balance"]);
}