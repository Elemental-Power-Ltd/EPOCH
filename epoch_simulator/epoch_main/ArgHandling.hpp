#pragma once

#include <argparse/argparse.hpp>
#include <spdlog/spdlog.h>

#include "../epoch_lib/Definitions.hpp"

enum class CommandlineMode {INTERACTIVE_CHOICE, OPTIMISATION, SIMULATION};

struct CommandlineArgs {
	std::string inputDir;
	std::string outputDir;
	CommandlineMode commandlineMode;
	bool verbose;
};


CommandlineArgs handleArgs(int argc, char* argv[]) {
	argparse::ArgumentParser argParser("Epoch", EPOCH_VERSION);

	// We support both Optimisation and Simulation
	// When neither is specified, the user will be presented with an interactive prompt to select an option
	auto& group = argParser.add_mutually_exclusive_group();

	group.add_argument("--optimise", "-opt")
		.flag()
		.help("Optimise over a search space");

	group.add_argument("--simulate", "-sim")
		.flag()
		.help("Simulate a single scenario with Epoch");


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
	if (argParser.get<bool>("--simulate")) {
		args.commandlineMode = CommandlineMode::SIMULATION;
	}
	else if (argParser.get<bool>("--optimise")) {
		args.commandlineMode = CommandlineMode::OPTIMISATION;
	}
	else {
		args.commandlineMode = CommandlineMode::INTERACTIVE_CHOICE;
	}

	args.inputDir = argParser.get<std::string>("--input");
	args.outputDir = argParser.get<std::string>("--output");
	args.verbose = argParser.get<bool>("--verbose");

	return args;
}