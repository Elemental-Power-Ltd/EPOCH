#include "Optimiser.hpp"

#include <mutex>
#include <filesystem>

#include <Eigen/Core>

#include "LeagueTable.hpp"
#include "TaskGenerator.hpp"
#include "../io/FileHandling.hpp"
#include "../Simulation/Simulate.hpp"


Optimiser::Optimiser(FileConfig fileConfig) :
	mFileConfig(fileConfig),
	mHistoricalData(readHistoricalData())
{

}

OutputValues Optimiser::runMainOptimisation(nlohmann::json inputJson)
{
	std::cout << "Starting Optimisation" << std::endl;
	return doOptimisation(inputJson);
}


OutputValues Optimiser::initialiseOptimisation(nlohmann::json inputJson) {

	std::cout << "Running initial optimisation" << std::endl;
	return doOptimisation(inputJson, true);
}

const HistoricalData Optimiser::readHistoricalData() {

	std::filesystem::path eloadFilepath = mFileConfig.getEloadFilepath();

	//read the electric load data
	std::vector<float> hotel_eload_data = readCSVColumn(eloadFilepath, 4); // read the column of the CSV data and store in vector data
	std::vector<float> ev_eload_data = readCSVColumn(eloadFilepath, 5); // read the column of the CSV data and store in vector data

	//read the heat load data
	std::filesystem::path hloadFilepath = mFileConfig.getHloadFilepath();
	std::vector<float> heatload_data = readCSVColumn(hloadFilepath, 4); // read the column of the CSV data and store in vector data

	//read the renewable generation data
	std::filesystem::path rgenFilepath = mFileConfig.getRgenFilepath();
	std::vector<float> RGen_data_1 = readCSVColumn(rgenFilepath, 4); // read the column of the CSV data and store in vector data
	std::vector<float> RGen_data_2 = readCSVColumn(rgenFilepath, 5);
	std::vector<float> RGen_data_3 = readCSVColumn(rgenFilepath, 6);
	std::vector<float> RGen_data_4 = readCSVColumn(rgenFilepath, 7);

	return {
	   toEigen(hotel_eload_data),
	   toEigen(ev_eload_data),
	   toEigen(heatload_data),
	   toEigen(RGen_data_1),
	   toEigen(RGen_data_2),
	   toEigen(RGen_data_3),
	   toEigen(RGen_data_4)
	};
}

Eigen::VectorXf Optimiser::toEigen(const std::vector<float>& vec)
{
	Eigen::VectorXf eig = Eigen::VectorXf(vec.size());

	for (int i = 0; i < vec.size(); i++) {
		eig[i] = vec[i];
	}

	return eig;
}

OutputValues Optimiser::RecallIndex(nlohmann::json inputJson, int recallindex) {

	OutputValues output{};

	if (!mTaskGenerator) {
		// Neither initOptimisation nor runMainOptimisation has been called previously
		// there are no tasks to recall
		throw std::exception();
	}

	Config config = mTaskGenerator->getTask(recallindex);

	output.Fixed_load1_scalar = config.getFixed_load1_scalar();
	output.Fixed_load2_scalar = config.getFixed_load2_scalar();
	output.Flex_load_max = config.getFlex_load_max();
	output.Mop_load_max = config.getMop_load_max();
	output.ScalarRG1 = config.getScalarRG1();
	output.ScalarRG2 = config.getScalarRG2();
	output.ScalarRG3 = config.getScalarRG3();
	output.ScalarRG4 = config.getScalarRG4();
	output.ScalarHL1 = config.getScalarHL1();
	output.ScalarHYield1 = config.getScalarHYield1();
	output.ScalarHYield2 = config.getScalarHYield2();
	output.ScalarHYield3 = config.getScalarHYield3();
	output.ScalarHYield4 = config.getScalarHYield4();
	output.GridImport = config.getGridImport();
	output.GridExport = config.getGridExport();
	output.Import_headroom = config.getImport_headroom();
	output.Export_headroom = config.getExport_headroom();
	output.ESS_charge_power = config.getESS_charge_power();
	output.ESS_discharge_power = config.getESS_discharge_power();
	output.ESS_capacity = config.getESS_capacity();
	output.ESS_RTE = config.getESS_RTE();
	output.ESS_aux_load = config.getESS_aux_load();
	output.ESS_start_SoC = config.getESS_start_SoC();
	output.ESS_charge_mode = config.getESS_charge_mode();
	output.ESS_discharge_mode = config.getESS_discharge_mode();
	output.import_kWh_price = config.getImport_kWh_price();
	output.export_kWh_price = config.getExport_kWh_price();

	return output;
}

// Write the saved results from the league table to CSV files
// Currently we write one CSV per objective, each containing the N best entries followed by the single worst entry
void Optimiser::writeResultsToCSVs(const LeagueTable& leagueTable) {

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

	// write all of the (unique) results to a CSV
	std::vector<int> allResults = leagueTable.getAllResults();
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

std::vector<ObjectiveResult> Optimiser::reproduceResults(const std::vector<int>& paramIndices) const {
	std::vector<ObjectiveResult> results{};
	results.reserve(paramIndices.size());

	for (int paramIndex : paramIndices) {
		results.emplace_back(reproduceResult(paramIndex));
	}

	return results;
}

// Given a ParamIndex that was used to produce a certain result, reproduce it to obtain the full result
ObjectiveResult Optimiser::reproduceResult(int paramIndex) const {
	if (!mTaskGenerator) {
		throw std::exception();
	}

	Config config = mTaskGenerator->getTask(paramIndex);

	Simulator sim{};

	SimulationResult simResult = sim.simulateScenario(mHistoricalData, config, SimulationType::FullReporting);

	ObjectiveResult objectiveResult;

	objectiveResult.config = config;

	objectiveResult.project_CAPEX = simResult.project_CAPEX;
	objectiveResult.payback_horizon_years = simResult.payback_horizon_years;
	objectiveResult.total_annualised_cost = simResult.total_annualised_cost;
	objectiveResult.scenario_cost_balance = simResult.scenario_cost_balance;
	objectiveResult.scenario_carbon_balance = simResult.scenario_carbon_balance;

	return objectiveResult;
}

OutputValues Optimiser::doOptimisation(nlohmann::json inputJson, bool initialisationOnly)
{
	auto clockStart = std::chrono::steady_clock::now();
	OutputValues output;
	resetTimeProfiler();

	mTaskGenerator = std::make_unique<TaskGenerator>(inputJson, initialisationOnly);

	int numWorkers = std::min(determineWorkerCount(), (int)inputJson["target_max_concurrency"]);

	LeagueTable leagueTable = LeagueTable(CAPACITY_PER_LEAGUE_TABLE);

	std::cout << "Total number of scenarios is: " << mTaskGenerator->totalScenarios() << std::endl;

	std::vector<std::thread> workers;

	for (int i = 0; i < numWorkers; ++i) {
		workers.emplace_back([this, &leagueTable]() {

			Config config;
			Simulator sim{};

			while (mTaskGenerator->nextTask(config)) {
				SimulationResult result = sim.simulateScenario(mHistoricalData, config);
				leagueTable.considerResult(result);
				addTimeToProfiler(result.runtime);
			}
		});
	}

	for (auto& worker : workers) {
		if (worker.joinable()) {
			worker.join();
		}
	}

	std::cout << "tasksCompleted" << std::endl;
	std::cout << "workers joined" << std::endl;

	//// Retrieve and process results
	findBestResults(leagueTable, output);

	output.maxVal = mTimeProfile.maxTime;
	output.minVal = mTimeProfile.minTime;
	output.meanVal = mTimeProfile.totalTime / mTimeProfile.count;

	std::chrono::duration<double> elapsedTime = std::chrono::steady_clock::now() - clockStart;
	output.time_taken = static_cast<float>(elapsedTime.count());

	std::cout << "Max: " << output.maxVal << ", Min: " << output.minVal << ", Mean: " << output.meanVal << std::endl;
	std::cout << "Total Runtime: " << output.time_taken << "s" << std::endl;

	if (initialisationOnly) {
		// Compute the per-scenario estimates
		float float_numWorkers = float(numWorkers);

		int totalScenarios = mTaskGenerator->totalScenarios();

		output.num_scenarios = totalScenarios;
		output.est_seconds = (totalScenarios * output.meanVal) / (float_numWorkers - 1.0f);
		output.est_hours = (totalScenarios * output.meanVal) / (3600 * (float_numWorkers - 1.0f));

		std::cout << "Number of scenarios: " << output.num_scenarios << ", Hours: " << output.est_hours << ", Seconds: " << output.est_seconds << std::endl;
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
		std::cerr << "Unable to determine the number of logical cores." << std::endl;
		throw std::exception();
	}

	std::cout << "Number of logical cores found is " << numWorkers << std::endl;
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
