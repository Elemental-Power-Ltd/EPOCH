#include "epoch_main.hpp"
#include <iostream>
#include <spdlog/spdlog.h>

#include "../epoch_lib/Optimisation/Optimiser.hpp"
#include "../epoch_lib/Simulation/Simulate.hpp"
#include "../epoch_lib/Simulation/TaskData.hpp"
#include "../epoch_lib/io/FileHandling.hpp"
#include "../epoch_lib/io/TaskDataJson.hpp"
#include "../epoch_lib/io/ToString.hpp"
#include "../epoch_lib/io/SiteDataJson.hpp"

int main(int argc, char* argv[]) {
	spdlog::info("Running Epoch version {}", EPOCH_VERSION);

	try {
		CommandlineArgs args = handleArgs(argc, argv);

		if (args.verbose) {
			spdlog::set_level(spdlog::level::debug);
			spdlog::debug("Verbose logging enabled");
		}

		FileConfig fileConfig{ args.inputDir, args.outputDir };
		ConfigHandler configHandler(fileConfig.getConfigFilepath());
		const EpochConfig config = configHandler.getConfig();

		if (args.commandlineMode == CommandlineMode::INTERACTIVE_CHOICE) {
			spdlog::info("No mode specified, selecting interactively");
			args.commandlineMode = getInteractiveChoice();
		}

		switch (args.commandlineMode) {
		case CommandlineMode::OPTIMISATION:
			optimise(fileConfig, config);
			break;
		case CommandlineMode::SIMULATION:
			simulate(fileConfig, config);
			break;
		default:
			// (this should be unreachable)
			spdlog::error("Invalid mode specified");
			return 1;
		}
	}
	catch (const std::exception& e) {
		spdlog::error(e.what());
		return 1;
	}
}

CommandlineMode getInteractiveChoice() {
	while (true) {
		// Use std::cout instead of spdlog for this as we don't want to pollute any logs
		std::cout << " ############ EPOCH ############" << std::endl;
		std::cout << " ## Select a mode to proceed: ##" << std::endl;
		std::cout << " ## [1] Optimisation          ##" << std::endl;
		std::cout << " ## [2] Simulation            ##" << std::endl;
		std::cout << " ###############################" << std::endl;
		std::cout << " Mode: ";

		std::string input;
		std::getline(std::cin, input);

		if (input == "1") {
			return CommandlineMode::OPTIMISATION;
		}
		else if (input == "2") {
			return CommandlineMode::SIMULATION;
		}
		else {
			spdlog::warn("Unrecognised input. Please enter 1 or 2");
		}
	}
}

void optimise(const FileConfig& fileConfig, const EpochConfig& config) {
	spdlog::info("Loading Optimiser");
	auto converted_json = readJsonFromFile(fileConfig.getInputJsonFilepath());

	auto optimiser = Optimiser(fileConfig, config);
	OutputValues output = optimiser.runOptimisation(converted_json);

	nlohmann::json jsonObj = outputToJson(output);
	writeJsonToFile(jsonObj, fileConfig.getOutputJsonFilepath());
}

void simulate(const FileConfig& fileConfig, const EpochConfig& config) {
	spdlog::info("Loading Simulator");

	SiteData siteData = readSiteData(fileConfig.getSiteDataFilepath());
	TaskData taskData = readTaskData(fileConfig.getTaskDataFilepath());

	Simulator simulator{ siteData, config.taskConfig };

	auto result = simulator.simulateScenario(taskData, SimulationType::FullReporting);

	// an invalid result will have no report data
	if (result.report_data) {
		auto fp = fileConfig.getOutputDir() / "FullTimeSeries.csv";
		writeTimeSeriesToCSV(fp, *result.report_data);
	}

	spdlog::info(resultToString(result));

}
