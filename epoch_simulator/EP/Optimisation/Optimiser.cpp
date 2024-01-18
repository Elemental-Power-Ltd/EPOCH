#include "Optimiser.hpp"

#include <mutex>


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

CustomDataTable Optimiser::readInputData() {

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
	   {"hotel_eload_data", hotel_eload_data},
	   {"ev_eload_data", ev_eload_data},
	   {"heatload_data", heatload_data},
	   {"RGen_data_1", RGen_data_1 },
	   {"RGen_data_2", RGen_data_2},
	   {"RGen_data_3", RGen_data_3},
	   {"RGen_data_4", RGen_data_4}
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
	CustomDataTable inputData = readInputData();

	int numWorkers = determineWorkerCount();

	SafeQueue<std::vector<std::pair<std::string, float>>> taskQueue;
	SafeQueue<SimulationResult> resultsQueue;

	int numScenarios = generateTasks(paramGrid, taskQueue, initialisationOnly);
	std::cout << "Total number of scenarios is: " << numScenarios << std::endl;

	std::vector<std::thread> workers;
	std::atomic<bool> tasksCompleted(false);
	std::mutex scenario_call_mutex;
	int scenario_call = 1;

	for (int i = 0; i < (numWorkers - 1); ++i) { //keep one worker back for the main thread - need to do A/B test on whether this is performant
		workers.emplace_back([this, &taskQueue, &resultsQueue, &inputData, &tasksCompleted, &scenario_call, &scenario_call_mutex, i]() {
			std::vector<std::pair<std::string, float>> paramSlice;
			while (true) {
				if (taskQueue.pop(paramSlice)) {
					SimulationResult result = simulateScenarioAndSum(inputData, paramSlice);

					// add running statistics here 
					resultsQueue.push(result); // this pushes the result to the results queue. Need to only do this if it's a worthy result  
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
	SimulationResult result;
	std::vector<SimulationResult> allResults{};
	while (resultsQueue.pop(result)) {
		allResults.emplace_back(result);
	}

	findBestResults(allResults, output);

	// Commented out until the CustomDataTable types are reworked
	//std::filesystem::path outputFilepath = mFileConfig.getOutputCSVFilepath();
	//writeToCSV(outputFilepath, cumDataColumns);// comment out if you don't want a smaller CSV file of summed output that takes a few seconds to write

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


void Optimiser::appendSumToDataTable(CustomDataTable& outTable, CustomDataTable& singleTable) {
	for (auto& entry : singleTable) {
		// Find the matching key in outTable
		auto it = std::find_if(outTable.begin(), outTable.end(),
			[&entry](const std::pair<std::string, std::vector<float>>& outputPair) {
				return entry.first == outputPair.first;
			});

		// If the key is found, append the sum of the singleTable's vector to the matching outTable's vector
		if (it != outTable.end()) {
			float sum = std::accumulate(entry.second.begin(), entry.second.end(), 0.0f);
			it->second.push_back(sum);
		}
	}
}


std::pair<float, float> Optimiser::findMinValueandIndex(const CustomDataTable& dataColumns, const std::string& columnName) {
	const std::vector<float>* targetColumn = nullptr;
	const std::vector<float>* paramIndexColumn = nullptr;

	// Find the target column and paramIndex column
	for (const auto& column : dataColumns) {
		if (column.first == columnName) {
			targetColumn = &column.second;
		}
		if (column.first == "Parameter index") {
			paramIndexColumn = &column.second;
		}
	}

	if (!targetColumn || !paramIndexColumn) {
		throw std::runtime_error("Specified column or Parameter index column not found");
	}

	if (targetColumn->size() != paramIndexColumn->size()) {
		throw std::runtime_error("Inconsistent data size between columns");
	}

	float minValue = std::numeric_limits<float>::max();
	float correspondingParamIndex = -1;

	for (size_t i = 0; i < targetColumn->size(); ++i) {
		if ((*targetColumn)[i] < minValue) {
			minValue = (*targetColumn)[i];
			correspondingParamIndex = (*paramIndexColumn)[i];
		}
	}

	return { minValue, correspondingParamIndex };
}


std::pair<float, float> Optimiser::findMaxValueandIndex(const CustomDataTable& dataColumns, const std::string& columnName) {
	const std::vector<float>* targetColumn = nullptr;
	const std::vector<float>* paramIndexColumn = nullptr;

	// Find the target column and paramIndex column
	for (const auto& column : dataColumns) {
		if (column.first == columnName) {
			targetColumn = &column.second;
		}
		if (column.first == "Parameter index") {
			paramIndexColumn = &column.second;
		}
	}

	if (!targetColumn || !paramIndexColumn) {
		throw std::runtime_error("Specified column or Parameter index column not found");
	}

	if (targetColumn->size() != paramIndexColumn->size()) {
		throw std::runtime_error("Inconsistent data size between columns");
	}

	// Initialize with the lowest possible float value
	float maxValue = std::numeric_limits<float>::lowest();
	float correspondingParamIndex = -1;

	for (size_t i = 0; i < targetColumn->size(); ++i) {
		// Compare to find the maximum value
		if ((*targetColumn)[i] > maxValue) {
			maxValue = (*targetColumn)[i];
			correspondingParamIndex = (*paramIndexColumn)[i];
		}
	}

	return { maxValue, correspondingParamIndex };
}


std::tuple<float, float, float> Optimiser::getColumnStats(const std::vector<std::pair<std::string, std::vector<float>>>& CustomDataTable) {
	const std::string targetColumnName = "Calculative execution time (s)";

	// Find the target column
	auto it = std::find_if(CustomDataTable.begin(), CustomDataTable.end(),
		[&](const std::pair<std::string, std::vector<float>>& column) {
			return column.first == targetColumnName;
		});

	if (it == CustomDataTable.end()) {
		std::cerr << "Column not found!" << std::endl;
		return std::make_tuple(0.0f, 0.0f, 0.0f); // Return zeros if column not found
	}

	// Filter the non-zero values into a separate vector
	std::vector<float> nonZeroValues;
	std::copy_if(it->second.begin(), it->second.end(), std::back_inserter(nonZeroValues), [](float value) {
		return value != 0.0f;
		});

	// If there are no non-zero values, return zeros
	if (nonZeroValues.empty()) {
		return std::make_tuple(0.0f, 0.0f, 0.0f);
	}

	float maxVal = *std::max_element(nonZeroValues.begin(), nonZeroValues.end());
	float minVal = *std::min_element(nonZeroValues.begin(), nonZeroValues.end());
	float meanVal = std::accumulate(nonZeroValues.begin(), nonZeroValues.end(), 0.0f) / nonZeroValues.size();

	return std::make_tuple(maxVal, minVal, meanVal);
}

void Optimiser::appendDataColumns(std::vector<std::pair<std::string, std::vector<float>>>& cumDataColumns,
	const std::vector<std::pair<std::string, std::vector<float>>>& dataColumnsN) {
	for (const auto& dataColumnN : dataColumnsN) {
		// Try to find the column in cumdataColumns
		auto it = std::find_if(cumDataColumns.begin(), cumDataColumns.end(),
			[&dataColumnN](const std::pair<std::string, std::vector<float>>& cumColumn) {
				return cumColumn.first == dataColumnN.first;
			});

		if (it != cumDataColumns.end()) {
			// If column exists, append the data
			it->second.insert(it->second.end(), dataColumnN.second.begin(), dataColumnN.second.end());
		}
		else {
			// If column doesn't exist, add the new column and its data
			cumDataColumns.push_back(dataColumnN);
		}
	}
}


CustomDataTable Optimiser::SumDataTable(const CustomDataTable& dataTable) {
	CustomDataTable result;
	result.reserve(dataTable.size()); // Preallocate memory

	//std::cout << "Input DataTable Size: " << dataTable.size() << std::endl;

	for (const auto& item : dataTable) {
		//std::cout << "Processing: " << item.first << ", Vector Size: " << item.second.size() << std::endl;
		float sum = std::accumulate(item.second.begin(), item.second.end(), 0.0f);
		//std::cout << "Sum: " << sum << std::endl;
		result.emplace_back(item.first, std::vector<float>{sum});
	}

	return result;
}

void Optimiser::findBestResults(const std::vector<SimulationResult>& allResults, OutputValues& output) {

	// CAPEX
	auto it1 = std::min_element(allResults.begin(), allResults.end(),
		[](const SimulationResult& a, const SimulationResult& b) {
			return a.TS_project_CAPEX < b.TS_project_CAPEX;
		});
	output.CAPEX = it1->TS_project_CAPEX;
	output.CAPEX_index = it1->paramIndex;

	// Annualised cost
	auto it2 = std::min_element(allResults.begin(), allResults.end(),
		[](const SimulationResult& a, const SimulationResult& b) {
			return a.total_annualised_cost < b.total_annualised_cost;
		});
	output.annualised = it2->total_annualised_cost;
	output.annualised_index = it2->paramIndex;

	// Scenario Balance(£)
	auto it3 = std::max_element(allResults.begin(), allResults.end(),
		[](const SimulationResult& a, const SimulationResult& b) {
			return a.TS_scenario_cost_balance < b.TS_scenario_cost_balance;
		});
	output.scenario_cost_balance = it3->TS_scenario_cost_balance;
	output.scenario_cost_balance_index = it3->paramIndex;

	// Payback horizon (yrs)
	auto it4 = std::min_element(allResults.begin(), allResults.end(),
		[](const SimulationResult& a, const SimulationResult& b) {
			return a.TS_payback_horizon_years < b.TS_payback_horizon_years;
		});
	output.payback_horizon = it4->TS_payback_horizon_years;
	output.payback_horizon_index = it4->paramIndex;

	// Scenario Carbon Balance (kgC02e)
	auto it5 = std::max_element(allResults.begin(), allResults.end(),
		[](const SimulationResult& a, const SimulationResult& b) {
			return a.TS_scenario_carbon_balance < b.TS_scenario_carbon_balance;
		});
	output.scenario_carbon_balance = it5->TS_scenario_carbon_balance;
	output.scenario_carbon_balance_index = it5->paramIndex;
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
