#include "Optimiser.hpp"

#include <mutex>
#include <filesystem>

#include <Eigen/Core>
#include <spdlog/spdlog.h>

#include "LeagueTable.hpp"
#include "TaskGenerator.hpp"
#include "../io/FileHandling.hpp"
#include "../Simulation/Simulate.hpp"


Optimiser::Optimiser(FileConfig fileConfig, EpochConfig config) :
	mFileConfig(fileConfig),
	mConfig(config),
	mHistoricalData(readHistoricalData(mFileConfig))
{
}

OutputValues Optimiser::runMainOptimisation(nlohmann::json inputJson)
{
	spdlog::info("Starting Optimisation");
	return doOptimisation(inputJson);
}


OutputValues Optimiser::initialiseOptimisation(nlohmann::json inputJson) {

	spdlog::info("Running initial optimisation");
	return doOptimisation(inputJson, true);
}

OutputValues Optimiser::RecallIndex(nlohmann::json inputJson, uint64_t recallindex) {

	OutputValues output{};

	if (!mTaskGenerator) {
		// Neither initOptimisation nor runMainOptimisation has been called previously
		// there are no tasks to recall
		throw std::exception();
	}

	if (recallindex < 1 || recallindex > mTaskGenerator->totalScenarios()) {
		// check that the paramIndex is within bounds
		throw std::exception();
	}

	Config config = mTaskGenerator->getTask(recallindex);

	output.Fixed_load1_scalar = config.Fixed_load1_scalar;
	output.Fixed_load2_scalar = config.Fixed_load2_scalar;
	output.Flex_load_max = config.Flex_load_max;
	output.Mop_load_max = config.Mop_load_max;
	output.ScalarRG1 = config.ScalarRG1;
	output.ScalarRG2 = config.ScalarRG2;
	output.ScalarRG3 = config.ScalarRG3;
	output.ScalarRG4 = config.ScalarRG4;
	output.ScalarHL1 = config.ScalarHL1;
	output.ScalarHYield1 = config.ScalarHYield1;
	output.ScalarHYield2 = config.ScalarHYield2;
	output.ScalarHYield3 = config.ScalarHYield3;
	output.ScalarHYield4 = config.ScalarHYield4;
	output.GridImport = config.GridImport;
	output.GridExport = config.GridExport;
	output.Import_headroom = config.Import_headroom;
	output.Export_headroom = config.Export_headroom;
	output.ESS_charge_power = config.ESS_charge_power;
	output.ESS_discharge_power = config.ESS_discharge_power;
	output.ESS_capacity = config.ESS_capacity;
	output.ESS_RTE = config.ESS_RTE;
	output.ESS_aux_load = config.ESS_aux_load;
	output.ESS_start_SoC = config.ESS_start_SoC;
	output.ESS_charge_mode = config.ESS_charge_mode;
	output.ESS_discharge_mode = config.ESS_discharge_mode;
	output.import_kWh_price = config.Import_kWh_price;
	output.export_kWh_price = config.Export_kWh_price;

	return output;
}

// Write the saved results from the league table to CSV files
// Currently we write one CSV per objective, each containing the N best entries followed by the single worst entry
void Optimiser::writeResultsToCSVs(const LeagueTable& leagueTable) {

	spdlog::info("Writing results to CSVs");

	auto capexIndices = leagueTable.getResultsForObjective(Objective::CAPEX);
	reproduceAndWriteToCSV(capexIndices, "CAPEX.csv");

	auto annualisedCostIndices = leagueTable.getResultsForObjective(Objective::AnnualisedCost);
	reproduceAndWriteToCSV(annualisedCostIndices, "AnnualisedCost.csv");

	auto paybackHorizonIndices = leagueTable.getResultsForObjective(Objective::PaybackHorizon);
	reproduceAndWriteToCSV(paybackHorizonIndices, "PaybackHorizon.csv");

	auto costBalanceIndices = leagueTable.getResultsForObjective(Objective::CostBalance);
	reproduceAndWriteToCSV(costBalanceIndices, "CostBalance.csv");

	auto carbonBalanceIndices = leagueTable.getResultsForObjective(Objective::CarbonBalance);
	reproduceAndWriteToCSV(carbonBalanceIndices, "CarbonBalance.csv");

	// write all the results to a single summary CSV
	std::vector<uint64_t> allResults = leagueTable.getAllResults();
	std::vector<ObjectiveResult> fullResults = reproduceResults(allResults);
	writeResultsToCSV(mFileConfig.getOutputCSVFilepath(), fullResults);

}

void Optimiser::reproduceAndWriteToCSV(ResultIndices resultIndices, std::string fileName) const {

	std::vector<ObjectiveResult> results = reproduceResults(resultIndices.bestIndices);
	ObjectiveResult worst = reproduceResult(resultIndices.worstIndex);
	results.emplace_back(worst);

	auto fullPath = mFileConfig.getOutputDir() / fileName;
	writeResultsToCSV(fullPath, results);
}

std::vector<ObjectiveResult> Optimiser::reproduceResults(const std::vector<uint64_t>& paramIndices) const {
	std::vector<ObjectiveResult> results{};
	results.reserve(paramIndices.size());

	for (uint64_t paramIndex : paramIndices) {
		results.emplace_back(reproduceResult(paramIndex));
	}

	return results;
}

// Given a ParamIndex that was used to produce a certain result, reproduce it to obtain the full result
ObjectiveResult Optimiser::reproduceResult(uint64_t paramIndex) const {
	if (!mTaskGenerator) {
		throw std::exception();
	}

	Config config = mTaskGenerator->getTask(paramIndex);

	Simulator sim{};

	SimulationResult simResult = sim.simulateScenario(mHistoricalData, config, SimulationType::FullReporting);

	return toObjectiveResult(simResult, config);
}

OutputValues Optimiser::doOptimisation(nlohmann::json inputJson, bool initialisationOnly)
{
	auto clockStart = std::chrono::steady_clock::now();
	OutputValues output;
	resetTimeProfiler();

	mTaskGenerator = std::make_unique<TaskGenerator>(inputJson, initialisationOnly);

	int numWorkers = std::min(determineWorkerCount(), (int)inputJson["target_max_concurrency"]);

	LeagueTable leagueTable = LeagueTable(mConfig.optimiserConfig, mFileConfig);

	spdlog::info("Total number of scenarios is: {}", mTaskGenerator->totalScenarios());

	std::vector<std::thread> workers;

	for (int i = 0; i < numWorkers; ++i) {
		workers.emplace_back([this, &leagueTable]() {

			Config config;
			Simulator sim{};

			while (mTaskGenerator->nextTask(config)) {
				SimulationResult result = sim.simulateScenario(mHistoricalData, config);
				leagueTable.considerResult(result, config);
				addTimeToProfiler(result.runtime);
			}
		});
	}

	for (auto& worker : workers) {
		if (worker.joinable()) {
			worker.join();
		}
	}

	spdlog::info("Optimisation completed, processing results...");

	//// Retrieve and process results
	findBestResults(leagueTable, output);

	output.maxVal = mTimeProfile.maxTime;
	output.minVal = mTimeProfile.minTime;
	output.meanVal = mTimeProfile.totalTime / mTimeProfile.count;

	std::chrono::duration<double> elapsedTime = std::chrono::steady_clock::now() - clockStart;
	output.time_taken = static_cast<float>(elapsedTime.count());

	spdlog::info("Max: {}s, Min: {}s, Mean: {}s", output.maxVal, output.minVal, output.meanVal);
	spdlog::info("Total Runtime: {}s", output.time_taken);

	if (initialisationOnly) {
		// Compute the per-scenario estimates
		float float_numWorkers = float(numWorkers);

		uint64_t totalScenarios = mTaskGenerator->totalScenarios();

		output.num_scenarios = totalScenarios;
		output.est_seconds = (totalScenarios * output.meanVal) / (float_numWorkers - 1.0f);
		output.est_hours = (totalScenarios * output.meanVal) / (3600 * (float_numWorkers - 1.0f));

		spdlog::info("Number of scenarios: {} Estimated time: {} hours ({} seconds)", output.num_scenarios, output.est_hours, output.est_seconds);
	}

	/* DUMMY OUTPUT -- NEEDS REPLACED WITH SENSIBLE OUTPUT */
	output.Fixed_load1_scalar = 1.0;
	output.Fixed_load2_scalar = 2.0;
	output.Flex_load_max = 3.0;
	output.Mop_load_max = 4.0;
	output.ScalarRG1 = 5.0;
	output.ScalarRG2 = 6.0;
	output.ScalarRG3 = 7.0;
	output.ScalarRG4 = 8.0;
	output.ScalarHL1 = 9.0;
	output.ScalarHYield1 = 10.0;
	output.ScalarHYield2 = 11.0;
	output.ScalarHYield3 = 12.0;
	output.ScalarHYield4 = 13.0;
	output.GridImport = 14.0;
	output.GridExport = 15.0;
	output.Import_headroom = 16.0;
	output.Export_headroom = 17.0;
	output.ESS_charge_power = 18.0;
	output.ESS_discharge_power = 19.0;
	output.ESS_capacity = 20.0;
	output.ESS_RTE = 21.0;
	output.ESS_aux_load = 22.0;
	output.ESS_start_SoC = 23.0;
	output.ESS_charge_mode = 24;
	output.ESS_discharge_mode = 25;

	writeResultsToCSVs(leagueTable);

	return output;
}

int Optimiser::determineWorkerCount()
{
	// interrogate the hardware to find number of logical cores, base concurrency loop on that
	int numWorkers = std::thread::hardware_concurrency();

	if (numWorkers == 0) {
		spdlog::warn("Unable to determine the number of logical cores. defaulting to 16");
		return 16;
	}

	spdlog::debug("Number of logical cores found is {}", numWorkers);
	return numWorkers;
}

void Optimiser::findBestResults(const LeagueTable& leagueTable, OutputValues& output) {

	// CAPEX
	auto bestCapex = leagueTable.getBestCapex();
	output.CAPEX = bestCapex.second;
	output.CAPEX_index = bestCapex.first;

	// Annualised cost
	auto bestAnnualisedCost = leagueTable.getBestAnnualisedCost();
	output.annualised = bestAnnualisedCost.second;
	output.annualised_index = bestAnnualisedCost.first;

	// Scenario Balance(£)
	auto bestCostBalance = leagueTable.getBestCostBalance();
	output.scenario_cost_balance = bestCostBalance.second;
	output.scenario_cost_balance_index = bestCostBalance.first;

	// Payback horizon (yrs)
	auto bestPaybackHorizon = leagueTable.getBestPaybackHorizon();
	output.payback_horizon = bestPaybackHorizon.second;
	output.payback_horizon_index = bestPaybackHorizon.first;

	// Scenario Carbon Balance (kgC02e)
	auto bestCarbonBalance = leagueTable.getBestCarbonBalance();
	output.scenario_carbon_balance = bestCarbonBalance.second;
	output.scenario_carbon_balance_index = bestCarbonBalance.first;
}

void Optimiser::resetTimeProfiler()
{
	mTimeProfile = TimeProfile{};
}


void Optimiser::addTimeToProfiler(float timeTaken)
{
	// For truly correct behaviour, a synchronization mechanism is needed
	// but we don't actually care if this is 100% accurate
	mTimeProfile.totalTime += timeTaken;
	if (timeTaken < mTimeProfile.minTime) {
		mTimeProfile.minTime = timeTaken;
	}
	if (timeTaken > mTimeProfile.maxTime) {
		mTimeProfile.maxTime = timeTaken;
	}
	mTimeProfile.count++;
}
