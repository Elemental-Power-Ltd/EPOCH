#include "Optimiser.hpp"

#include <mutex>

#include "LeagueTable.hpp"
#include "../io/FileHandling.hpp"
#include "../Simulation/Simulate.hpp"


Optimiser::Optimiser(FileConfig fileConfig)
{
	mFileConfig = fileConfig;
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

HistoricalData Optimiser::readHistoricalData() {

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
	   hotel_eload_data,
	   ev_eload_data,
	   heatload_data,
	   RGen_data_1,
	   RGen_data_2,
	   RGen_data_3,
	   RGen_data_4
	};
}

std::vector<paramRange> Optimiser::makeParamGrid(const nlohmann::json& inputJson)
{
	/*DEFINE PARAMETER GRID TO ITERATE THROUGH*/
	std::vector<paramRange> paramGrid;

	// input argument should be a JSON object containing a dictionary of key-tuple pairs
	// each key should be the name of a parameter to be iterated over; the tuple should provide the range and step size of the iterator
	try {
		// Loop through all key-value/key-tuple pairs
		for (const auto& item : inputJson.items()) {
			if (item.value().is_array()) {
				// the item is a key-tuple pair
				paramGrid.push_back({ item.key(), item.value()[0], item.value()[1], item.value()[2] });
				std::cout << "(" << item.key() << "," << item.value()[0] << ":" << item.value()[1] << ":" << item.value()[2] << ")" << std::endl;
			}
			else {
				// the item is a key-value pair
				paramGrid.push_back({ item.key(), item.value(), item.value(), 0.0 });
			}
		}
	}
	catch (const std::exception& e) {
		std::cerr << "Error: " << e.what() << std::endl;
		throw std::exception();
	}
	return paramGrid;
}


OutputValues Optimiser::RecallIndex(nlohmann::json inputJson, int recallindex) {

	OutputValues output;

	output.maxVal = 0;

	std::vector<paramRange> paramGrid;

	try {
		// Loop through all key-value/key-tuple pairs
		for (const auto& item : inputJson.items()) {
			if (item.value().is_array()) {
				// the item is a key-tuple pair
				paramGrid.push_back({ item.key(), item.value()[0], item.value()[1], item.value()[2] });
				std::cout << "(" << item.key() << "," << item.value()[0] << ":" << item.value()[1] << ":" << item.value()[2] << ")" << std::endl;
			}
			else {
				// the item is a key-value pair
				paramGrid.push_back({ item.key(), item.value(), item.value(), 0.0 });
			}
		}
	}
	catch (const std::exception& e) {
		std::cerr << "Error: " << e.what() << std::endl;
		return output;
	}

	if (paramGrid.empty()) return output;

	//auto paramSlice = ParamRecall(paramGrid, recallindex);

	auto paramSlice = TaskRecall(paramGrid, recallindex);

	for (const auto& p : paramSlice) {
		std::cout << p.first << ": " << p.second << std::endl;
	}

	std::string target = "Fixed_load1_scalar"; // Replace with the string you're looking for
	float value = 0.0f;
	bool found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.Fixed_load1_scalar = value;
	}

	target = "Fixed_load2_scalar"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.Fixed_load2_scalar = value;
	}
	target = "Flex_load_max"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.Flex_load_max = value;
	}
	target = "Mop_load_max"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.Mop_load_max = value;
	}
	target = "ScalarRG1"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarRG1 = value;
	}
	target = "ScalarRG2"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarRG2 = value;
	}

	target = "ScalarRG3"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarRG3 = value;
	}
	target = "ScalarRG4"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarRG4 = value;
	}

	target = "ScalarHL1"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarHL1 = value;
	}
	target = "ScalarHYield1"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarHYield1 = value;
	}
	target = "ScalarHYield2"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarHYield2 = value;
	}
	target = "ScalarHYield3"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarHYield3 = value;
	}
	target = "ScalarHYield4"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ScalarHYield4 = value;
	}
	target = "GridImport"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.GridImport = value;
	}
	target = "GridExport"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.GridExport = value;
	}
	target = "Import_headroom"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.Import_headroom = value;
	}
	target = "Export_headroom"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.Export_headroom = value;
	}
	target = "ESS_charge_power"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_charge_power = value;
	}
	target = "ESS_discharge_power"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_discharge_power = value;
	}
	target = "ESS_capacity"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_capacity = value;
	}

	target = "ESS_RTE"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_RTE = value;
	}

	target = "ESS_aux_load"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_aux_load = value;
	}
	target = "ESS_start_SoC"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_start_SoC = value;
	}
	target = "ESS_charge_mode"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_charge_mode = value;
	}

	target = "ESS_discharge_mode"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.ESS_discharge_mode = value;
	}

	target = "import_kWh_price"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.import_kWh_price = value;
	}

	target = "export_kWh_price"; // Replace with the string you're looking for
	value = 0.0f;
	found = false;
	for (const auto& element : paramSlice) {
		if (element.first == target) {
			value = element.second;
			found = true;
			break; // Stop the loop once you've found the element
		}
	}
	if (found) {
		output.export_kWh_price = value;
	}


	return output;
}


std::vector<std::pair<std::string, float>> Optimiser::TaskRecall(const std::vector<paramRange>& paramGrid, int index)

{
	// CAUTION THIS SHOULD ONLY BE CALLED IN THE CONTEXT OF "RECALL" AS THE taskQueue is already written in the main optimisation using the generateTask function

	SafeQueue<std::vector<std::pair<std::string, float>>> taskQueue;

	std::vector<std::pair<std::string, float>> paramSlice;

	/* Use an iterative approach as follows */
	size_t numParameters = paramGrid.size();
	if (numParameters == 0) return paramSlice;

	// Vectors to keep track of the current indices and values for each parameter
	std::vector<size_t> indices(numParameters, 0);
	std::vector<float> current_values(numParameters, 0);

	// Initialize current values to the min values
	for (size_t i = 0; i < numParameters; ++i) {
		current_values[i] = paramGrid[i].min;
	}

	bool finished = false;

	int j = 0;

	while (!finished) {
		j++; // this set j = 1 to align with paramslice number

		// Create a new task with the current combination of parameters
		std::vector<std::pair<std::string, float>> currentTask;
		for (size_t i = 0; i < numParameters; ++i) {
			currentTask.emplace_back(paramGrid[i].name, current_values[i]);
		}

		// Add task index to currentTask, to keep track of ordering through parallelisation
		currentTask.emplace_back("Parameter index", j);

		// Push the new task onto the task queue
		taskQueue.push(currentTask);

		if (j == index)
		{
			paramSlice = currentTask;
			finished = true;
			return paramSlice;

		}
		// Move to the next combination
		for (size_t i = 0; i < numParameters; ++i) {
			// If step is 0, default it to cover the entire range as one step
			float step = paramGrid[i].step != 0 ? paramGrid[i].step : (paramGrid[i].max - paramGrid[i].min);
			// Guard against non-positive step sizes
			if (step <= 0) {
				step = 1;
			}

			current_values[i] += step;

			if (current_values[i] > paramGrid[i].max) {
				if (i == numParameters - 1) {
					finished = true;
					break;
				}
				else {
					current_values[i] = paramGrid[i].min;  // Reset this parameter and carry '1' to the next
					// No need to break, continue to update the next parameter
				}
			}
			else {
				break; // Found the next combination, break out of the loop
			}
		}
	}
	return paramSlice;
}

std::vector<SimulationResult> Optimiser::reproduceResults(const std::vector<int>& paramIndices)
{
	std::vector<SimulationResult> results{};
	results.reserve(paramIndices.size());

	for (int paramIndex : paramIndices) {
		results.emplace_back(reproduceResult(paramIndex));
	}

	return results;
}

// Given a ParamIndex that was used to produce a certain result
// Reproduce the full SimulationResult that it would produce
SimulationResult Optimiser::reproduceResult(int paramIndex)
{
	SimulationResult r{};

	// TODO - this method doesn't currently do anything
	// we need to rework the ParamGrid generation first
	r.paramIndex = paramIndex;

	return r;
}


int Optimiser::generateTasks(const std::vector<paramRange>& paramGrid, SafeQueue<std::vector<std::pair<std::string, float>>>& taskQueue, bool initialisationOnly)
{
	int j = 0;
	/* Use an iterative approach as follows */
	size_t numParameters = paramGrid.size();
	if (numParameters == 0) return j;

	// Vectors to keep track of the current indices and values for each parameter
	std::vector<size_t> indices(numParameters, 0);
	std::vector<float> current_values(numParameters, 0);

	// Initialize current values to the min values
	for (size_t i = 0; i < numParameters; ++i) {
		current_values[i] = paramGrid[i].min;
	}

	bool finished = false;

	while (!finished) {

		if (initialisationOnly && j > INITIALISATION_MAX_SCENARIOS) {
			break;
		}

		j++;

		// Create a new task with the current combination of parameters
		std::vector<std::pair<std::string, float>> currentTask;
		for (size_t i = 0; i < numParameters; ++i) {
			currentTask.emplace_back(paramGrid[i].name, current_values[i]);
		}
		// Add task index to currentTask, to keep track of ordering through parallelisation
		currentTask.emplace_back("Parameter index", j);
		// Push the new task onto the task queue
		taskQueue.push(currentTask);

		// Move to the next combination
		for (size_t i = 0; i < numParameters; ++i) {
			// If step is 0, default it to cover the entire range as one step
			float step = paramGrid[i].step != 0 ? paramGrid[i].step : (paramGrid[i].max - paramGrid[i].min);
			// Guard against non-positive step sizes
			if (step <= 0) {
				step = 1;
			}

			current_values[i] += step;

			if (current_values[i] > paramGrid[i].max) {
				if (i == numParameters - 1) {
					finished = true;
					break;
				}
				else {
					current_values[i] = paramGrid[i].min;  // Reset this parameter and carry '1' to the next
					// No need to break, continue to update the next parameter
				}
			}
			else {
				break; // Found the next combination, break out of the loop
			}
		}
	}
	return j;
}

OutputValues Optimiser::doOptimisation(nlohmann::json inputJson, bool initialisationOnly)
{
	OutputValues output;
	resetTimeProfiler();

	auto paramGrid = makeParamGrid(inputJson);
	HistoricalData inputData = readHistoricalData();

	int numWorkers = determineWorkerCount();

	SafeQueue<std::vector<std::pair<std::string, float>>> taskQueue;
	LeagueTable leagueTable = LeagueTable(CAPACITY_PER_LEAGUE_TABLE);

	int numScenarios = generateTasks(paramGrid, taskQueue, initialisationOnly);
	std::cout << "Total number of scenarios is: " << numScenarios << std::endl;

	std::vector<std::thread> workers;
	std::atomic<bool> tasksCompleted(false);
	std::mutex scenario_call_mutex;
	int scenario_call = 1;

	for (int i = 0; i < (numWorkers - 1); ++i) { //keep one worker back for the main thread - need to do A/B test on whether this is performant
		workers.emplace_back([this, &taskQueue, &leagueTable, &inputData, &tasksCompleted, &scenario_call, &scenario_call_mutex, i]() {
			std::vector<std::pair<std::string, float>> paramSlice;
			while (true) {
				if (taskQueue.pop(paramSlice)) {
					SimulationResult result = simulateScenarioAndSum(inputData, paramSlice);

					// add running statistics here 
					leagueTable.considerResult(result);

					addTimeToProfiler(result.runtime);
					{
						std::lock_guard<std::mutex> lock(scenario_call_mutex);
						std::cout << "scenario called " << scenario_call << " times" << std::endl;
						scenario_call++;
					}

				}
				else {
					std::cout << "sleeping for 10 ms" << std::endl;
					std::this_thread::sleep_for(std::chrono::milliseconds(10)); // Short sleep
					if (tasksCompleted.load()) {
						std::cout << "Worker " << i << ": no more tasks, exiting." << std::endl;
						break;
					}
				}
			}
			});
	}

	// After all tasks are generated
	tasksCompleted.store(true);
	std::cout << "tasksCompleted" << std::endl;

	for (auto& worker : workers) {
		if (worker.joinable()) {
			worker.join();
		}
	}
	std::cout << "workers joined" << std::endl;

	//// Retrieve and process results
	findBestResults(leagueTable, output);

	// write the results to a CSV file
	std::filesystem::path outputFilepath = mFileConfig.getOutputCSVFilepath();
	std::vector<SimulationResult> results = reproduceResults(leagueTable.toParamIndexList());
	writeResultsToCSV(outputFilepath, results);

	output.maxVal = mTimeProfile.maxTime;
	output.minVal = mTimeProfile.minTime;
	output.meanVal = mTimeProfile.totalTime / mTimeProfile.count;

	std::cout << "Max: " << output.maxVal << ", Min: " << output.minVal << ", Mean: " << output.meanVal << std::endl;

	if (initialisationOnly) {
		// Compute the per-scenario estimates
		float float_numWorkers = float(numWorkers);

		// FIXME: Enormously inefficient temporary approach to count the number of tasks for a full run-through
		int totalScenarios = generateTasks(paramGrid, taskQueue, false);

		output.num_scenarios = totalScenarios;
		output.est_seconds = (totalScenarios * output.meanVal) / (float_numWorkers - 1.0);
		output.est_hours = (totalScenarios * output.meanVal) / (3600 * (float_numWorkers - 1.0));

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
	output.ESS_charge_mode = 24.0;
	output.ESS_discharge_mode = 25.0;

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
