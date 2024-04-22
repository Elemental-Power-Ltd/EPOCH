#include <argparse/argparse.hpp>
#include <spdlog/spdlog.h>

struct CommandlineArgs {
	std::string inputDir;
	std::string outputDir;
	std::string configDir;
	bool verbose;
};


CommandlineArgs handleArgs(int argc, char* argv[]) {
	argparse::ArgumentParser argParser("Epoch");

	argParser.add_argument("--input", "-i")
		.help("The directory containing all input files")
		.default_value(std::string("./InputData"));

	argParser.add_argument("--output", "-o")
		.help("The directory to write all output files to")
		.default_value(std::string("./OutputData"));

	argParser.add_argument("--config", "-c")
		.help("The directory containing the config files")
		.default_value(std::string("./Config"));

	argParser.add_argument("--verbose")
		.help("Set logging to verbose")
		.flag();

	argParser.parse_args(argc, argv);

	CommandlineArgs args;
	args.inputDir = argParser.get<std::string>("--input");
	args.outputDir = argParser.get<std::string>("--output");
	args.configDir = argParser.get<std::string>("--config");
	args.verbose = argParser.get<bool>("--verbose");

	return args;
}