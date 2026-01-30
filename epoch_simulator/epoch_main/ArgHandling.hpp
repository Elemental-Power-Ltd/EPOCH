#pragma once

#include <argparse/argparse.hpp>
#include <spdlog/spdlog.h>

#include "../epoch_lib/Definitions.hpp"


enum class OutputFormat { Human, Json };

struct CommandlineArgs {
	std::string inputDir;
	std::string outputDir;
	bool verbose = false;

	OutputFormat format = OutputFormat::Human;
};


CommandlineArgs handleArgs(int argc, char* argv[]) {
	argparse::ArgumentParser argParser("Epoch", EPOCH_VERSION);

	// Determine the directories to read from & write to
	argParser.add_argument("--input", "-i")
		.help("The directory containing all input files")
		.default_value(std::string("./InputData"));

	argParser.add_argument("--output", "-o")
		.help("The directory to write all output files to")
		.default_value(std::string("./OutputData"));

	// Enable verbose logging
	argParser.add_argument("--verbose")
		.help("Set logging to verbose")
		.flag();

	auto& mode = argParser.add_mutually_exclusive_group(false);
	mode.add_argument("--json", "-J")
		.help("Output JSON to sdout. Automatically quiets all logs")
		.flag();

	mode.add_argument("--human", "-H")
		.help("Output a human readable summary")
		.flag();

	argParser.parse_args(argc, argv);

	CommandlineArgs args;
	args.inputDir = argParser.get<std::string>("--input");
	args.outputDir = argParser.get<std::string>("--output");
	args.verbose = argParser.get<bool>("--verbose");

	const bool jsonFlag = argParser.get<bool>("--json");

	if (jsonFlag) {
		args.format = OutputFormat::Json;
	}
	else {
		args.format = OutputFormat::Human;

	}

	return args;
}