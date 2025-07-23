#include "epoch_main.hpp"
#include <iostream>
#include <spdlog/spdlog.h>

#include "../epoch_lib/Optimisation/Optimiser.hpp"
#include "../epoch_lib/Simulation/Simulate.hpp"
#include "../epoch_lib/Simulation/TaskData.hpp"
#include "../epoch_lib/io/FileHandling.hpp"
#include "../epoch_lib/io/TaskDataJson.hpp"
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

	// TODO - wrangle with utf and locales to allow the pound sign
	spdlog::info("Scope 1 emissions: {} kgCO2e / year", result.scenario_carbon_balance_scope_1);
	spdlog::info("Scope 2 emissions: {} kgCO2e / year", result.scenario_carbon_balance_scope_2);
	spdlog::info("Capex: £{:.2f}", result.project_CAPEX);
	spdlog::info("Annualised Cost: £{:.2f} / year", result.total_annualised_cost);
	spdlog::info("Cost Balance: £{:.2f} / year", result.scenario_cost_balance);
	spdlog::info("Payback Horizon: {} years", result.payback_horizon_years);
	spdlog::info("NPV Balance: £{}", result.npv_balance);

	spdlog::info(
		"Energy totals (kWh):\n"
		" - Gas used = {}\n"
		" - Electricity imported = {}\n"
		" - Electricity generated = {}\n"
		" - Electricity exported = {}\n"
		" - Electrical shortfall = {}\n"
		" - Heat shortfall = {}\n"
		" - CH shortfall = {}\n"
		" - DHW shortfall = {}\n\n"
		"Financial totals (£):\n"
		" - Gas import cost = {}\n"
		" - Electricity import cost = {}\n"
		" - Electricity export gain = {}\n"
		" - Total Meter Cost = {}\n"
		" - Total Operating Cost = {}\n"
		" - Net Present Value = {}\n",
		result.metrics.total_gas_used,
		result.metrics.total_electricity_imported,
		result.metrics.total_electricity_generated,
		result.metrics.total_electricity_exported,
		result.metrics.total_electrical_shortfall,
		result.metrics.total_heat_shortfall,
		result.metrics.total_ch_shortfall,
		result.metrics.total_dhw_shortfall,
		result.metrics.total_gas_import_cost,
		result.metrics.total_electricity_import_cost,
		result.metrics.total_electricity_export_gain,
		result.metrics.total_meter_cost,
		result.metrics.total_operating_cost,
		result.metrics.total_net_present_value
	);



}
