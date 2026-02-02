#include "epoch_main.hpp"
#include <iostream>
#include <spdlog/spdlog.h>

#include "../epoch_lib/Simulation/Simulate.hpp"
#include "../epoch_lib/Simulation/TaskData.hpp"
#include "../epoch_lib/io/FileHandling.hpp"
#include "../epoch_lib/io/TaskDataJson.hpp"
#include "../epoch_lib/io/ToString.hpp"
#include "../epoch_lib/io/SiteDataJson.hpp"
#include "../epoch_lib/io/ResultJson.hpp"


static void configureLogging(const CommandlineArgs& args) {
	if (args.format == OutputFormat::Json) {
		// JSON sets quiet mode for piping
		spdlog::set_level(spdlog::level::off);
		return;
	}

	if (args.verbose) {
		spdlog::set_level(spdlog::level::debug);
	}
	else {
		spdlog::set_level(spdlog::level::info);
	}
}

int main(int argc, char* argv[]) {

	try {
		CommandlineArgs args = handleArgs(argc, argv);
		configureLogging(args);

		spdlog::info("Running Epoch version {}", EPOCH_VERSION);

		FileConfig fileConfig{ args.inputDir, args.outputDir };
		ConfigHandler configHandler(fileConfig.getConfigFilepath());
		const EpochConfig config = configHandler.getConfig();

		simulate(fileConfig, config, args);
	}
	catch (const std::exception& e) {
		spdlog::error(e.what());
		return 1;
	}
}


void simulate(const FileConfig& fileConfig, const EpochConfig& config, const CommandlineArgs& args) {
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

	if (args.format == OutputFormat::Json) {
		nlohmann::json j = result;
		std::cout << j.dump(2) << '\n';
	}
	else {
		spdlog::info(resultToString(result));
	}
}
