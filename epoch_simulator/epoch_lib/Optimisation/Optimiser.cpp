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


OutputValues Optimiser::runOptimisation(nlohmann::json inputJson)
{
	spdlog::info("Starting Optimisation");
	auto clockStart = std::chrono::steady_clock::now();
	OutputValues output;
	resetTimeProfiler();

	mTaskGenerator = std::make_unique<TaskGenerator>(inputJson);

	int numWorkers = std::min(determineWorkerCount(), (int)inputJson["target_max_concurrency"]);

	LeagueTable leagueTable = LeagueTable(mConfig.optimiserConfig, mFileConfig);

	spdlog::info("Total number of scenarios is: {}", mTaskGenerator->totalScenarios());

	std::vector<std::thread> workers;

	for (int i = 0; i < numWorkers; ++i) {
		workers.emplace_back([this, &leagueTable]() {
			TaskWithIndex taskWithIndex{};

			Simulator sim{};

			while (mTaskGenerator->nextTask(taskWithIndex)) {
				SimulationResult result = sim.simulateScenario(mHistoricalData, taskWithIndex.task);
				leagueTable.considerResult(result, taskWithIndex);
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

	/* DUMMY OUTPUT -- NEEDS REPLACED WITH SENSIBLE OUTPUT */
	output.Fixed_load1_scalar = 1.0;
	output.Fixed_load2_scalar = 2.0;
	output.Flex_load_max = 3.0;
	output.Mop_load_max = 4.0;
	output.ScalarRG1 = 5.0;
	output.ScalarRG2 = 6.0;
	output.ScalarRG3 = 7.0;
	output.ScalarRG4 = 8.0;
	output.ScalarHYield = 9.0;
	output.s7_EV_CP_number = 26;
	output.f22_EV_CP_number = 27;
	output.r50_EV_CP_number = 28;
	output.u150_EV_CP_number = 29;
	output.EV_flex = 30.0;
	output.ScalarHL1 = 10.0;
	output.ASHP_HSource = 12;
	output.ASHP_RadTemp = 13.0;
	output.ASHP_HotTemp = 14.0;
	output.GridImport = 15.0;
	output.GridExport = 16.0;
	output.Import_headroom = 17.0;
	output.Export_headroom = 18.0;
	output.Min_power_factor = 19.0;
	output.ESS_charge_power = 20.0;
	output.ESS_discharge_power = 21.0;
	output.ESS_capacity = 22.0;
	output.ESS_start_SoC = 23.0;
	output.ESS_charge_mode = 24;
	output.ESS_discharge_mode = 25;
	output.DHW_cylinder_volume = 26;

	writeResultsToCSVs(leagueTable);

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

	TaskData taskData = mTaskGenerator->getTask(paramIndex);

	Simulator sim{};

	SimulationResult simResult = sim.simulateScenario(mHistoricalData, taskData, SimulationType::ResultOnly);

	return toObjectiveResult(simResult, taskData);
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

	// Scenario Balance(�)
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
