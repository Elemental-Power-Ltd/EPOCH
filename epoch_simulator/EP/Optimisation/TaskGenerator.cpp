#include "TaskGenerator.hpp"

#include <algorithm>
#include <iostream>


TaskGenerator::TaskGenerator(const nlohmann::json& inputJson, bool initialisationOnly)
{
	mParamGrid = makeParamGrid(inputJson);

	long cumulativeProduct = 1;

	for (const auto& paramRange: mParamGrid) {

		// TODO - validation is important
		// esp that we don't have a negative step size or a flipped min/max

		std::vector<float> rangeValues;

		if (paramRange.min == paramRange.max) {
			rangeValues.emplace_back(paramRange.min);
		}
		else {
			float value = paramRange.min;
			while (value <= paramRange.max) {
				rangeValues.emplace_back(value);
				value += paramRange.step;
			};
		}

		mExpandedParamGrid.emplace_back(paramRange.name, rangeValues, cumulativeProduct);

		// multiply by the number of values in this parameter range ready for the next parameter
		cumulativeProduct *= rangeValues.size();
	}


	mTotalScenarios = cumulativeProduct;

	if (initialisationOnly) {
		mScenarioLimit = std::min(mTotalScenarios, MAX_SCENARIOS_FOR_INITIALISATION);
	}
	else {
		mScenarioLimit = mTotalScenarios;
	}

	mScenarioCounter = 1;

}


const int TaskGenerator::totalScenarios()
{
	return mTotalScenarios;
}

bool TaskGenerator::nextTask(Config& config)
{
	if (mScenarioCounter > mScenarioLimit) {
		return false;
	}

	// mScenarioCounter is atomic
	// Calling in this way should ensure that getTask is called incrementally with each index in the range
	config = getTask(mScenarioCounter++);
	return true;
}

Config TaskGenerator::getTask(int index)
{
	// the user facing index starts at 1
	// but the logic in here assumes a 0 index
	index -= 1;

	std::vector<std::pair<std::string, float>> paramSlice;

	for (const auto& paramRange: mExpandedParamGrid) {
		// Determine the index of this variable
		//	1. perform integer division by the cumulative product of previous parameter ranges
		//	   (this parameter should be fixed while we iterate through all permutations of those variables)
		//  2. take modulo of the size
		int i = (index / paramRange.cumulativeProduct) % paramRange.values.size();
		float value = paramRange.values[i];

		paramSlice.emplace_back(paramRange.name, paramRange.values[i]);
	}

	Config config;

	// Change the config parameters to the current set of values in the parameter grid
	for (size_t i = 0; i < paramSlice.size(); ++i) {
		if (config.param_map_float.find(paramSlice[i].first) != config.param_map_float.end()) {
			config.set_param_float(paramSlice[i].first, paramSlice[i].second);
			//			myConfig.print_param_float(paramSlice[i].first);
		}
		else {
			config.set_param_int(paramSlice[i].first, paramSlice[i].second);
			//			myConfig.print_param_int(paramSlice[i].first);
		}
	}

	// set the 1-based index
	config.setParamIndex(index + 1);


	return config;
}

std::vector<ParamRange> TaskGenerator::makeParamGrid(const nlohmann::json& inputJson)
{
	/*DEFINE PARAMETER GRID TO ITERATE THROUGH*/
	std::vector<ParamRange> paramGrid;

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
