#include <gtest/gtest.h>

#include <filesystem>
#include <fstream>

#include "../epoch_lib/io/FileConfig.h"
#include "../epoch_lib/Optimisation/Optimiser.hpp"
#include "../epoch_lib/io/FileHandling.hpp"
#include "../epoch_lib/io/EpochConfig.hpp"

namespace fs = std::filesystem;

TEST(EpochTestCase, MatchesKnownOutput) {
	FileConfig fileConfig = FileConfig{
		"KnownInput", "OutputData", "Config",
		"CSVEload.csv", "CSVHload.csv", "CSVRGen.csv",
		"knownInput.json", "TestResults.csv", "TestOutputParameters.json", "TestOuputParametersFromInit.json"
	};

	ConfigHandler configHandler(fileConfig.getConfigDir());
	Optimiser opt = Optimiser(fileConfig, configHandler.getConfig());

	// Run the Optimiser on known input
	auto inputJson = readJsonFromFile(fileConfig.getInputJsonFilepath());
	OutputValues testOutput = opt.runMainOptimisation(inputJson);
	auto testJson = outputToJson(testOutput);
	writeJsonToFile(testJson, fileConfig.getOutputJsonFilepath());

	//// Load the known output
	fs::path knownOutputFile = fs::path{ "KnownOutput" } / fs::path{ "KnownOutput.json" };
	auto knownJson = readJsonFromFile(knownOutputFile);

	EXPECT_EQ(testJson["CAPEX"], knownJson["CAPEX"]);
	//EXPECT_EQ(testJson["CAPEX_index"], knownJson["CAPEX_index"]);

	EXPECT_EQ(testJson["annualised"], knownJson["annualised"]);
	//EXPECT_EQ(testJson["annualised_index"], knownJson["annualised_index"]);

	EXPECT_EQ(testJson["scenario_cost_balance"], knownJson["scenario_cost_balance"]);
	//EXPECT_EQ(testJson["scenario_cost_balance_index"], knownJson["scenario_cost_balance_index"]);

	EXPECT_EQ(testJson["payback_horizon"], knownJson["payback_horizon"]);
	//EXPECT_EQ(testJson["payback_horizon_index"], knownJson["payback_horizon_index"]);

	EXPECT_EQ(testJson["scenario_carbon_balance"], knownJson["scenario_carbon_balance"]);
	//EXPECT_EQ(testJson["scenario_carbon_balance_index"], knownJson["scenario_carbon_balance_index"]);

}