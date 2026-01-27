#pragma once

#include <argparse/argparse.hpp>
#include <spdlog/spdlog.h>

#include "../epoch_lib/Definitions.hpp"


struct CommandlineArgs {
	std::string inputDir;
	std::string outputDir;
	bool verbose;
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

	argParser.parse_args(argc, argv);

	CommandlineArgs args;
	args.inputDir = argParser.get<std::string>("--input");
	args.outputDir = argParser.get<std::string>("--output");
	args.verbose = argParser.get<bool>("--verbose");

	return args;
}