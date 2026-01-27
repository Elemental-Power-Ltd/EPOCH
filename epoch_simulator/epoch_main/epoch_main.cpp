#include "epoch_main.hpp"
#include <iostream>
#include <spdlog/spdlog.h>

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

		simulate(fileConfig, config);
	}
	catch (const std::exception& e) {
		spdlog::error(e.what());
		return 1;
	}
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
