#include "TaskGenerator.hpp"

#include <algorithm>
#include <iostream>
#include <math.h>

#include <spdlog/spdlog.h>

TaskGenerator::TaskGenerator(const nlohmann::json& inputJson, bool initialisationOnly)
{
	mParamGrid = makeParamGrid(inputJson);

	uint64_t cumulativeProduct = 1;

	for (const auto& paramRange: mParamGrid) {

		std::vector<float> rangeValues = makeRange(paramRange);

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


uint64_t TaskGenerator::totalScenarios() const
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

Config TaskGenerator::getTask(uint64_t index) const {
	// the user facing index starts at 1
	// but the logic in here assumes a 0 index
	index -= 1;

	std::vector<std::pair<std::string, float>> paramSlice;

	for (const auto& paramRange: mExpandedParamGrid) {
		// Determine the index of this variable
		//	1. perform integer division by the cumulative product of previous parameter ranges
		//	   (this parameter should be fixed while we iterate through all permutations of those variables)
		//  2. take modulo of the size
		uint64_t i = (index / paramRange.cumulativeProduct) % paramRange.values.size();
		float value = paramRange.values[i];

		paramSlice.emplace_back(paramRange.name, paramRange.values[i]);
	}

	Config config;

	// Change the config parameters to the current set of values in the parameter grid
	for (size_t i = 0; i < paramSlice.size(); ++i) {
		if (config.param_map_float.find(paramSlice[i].first) != config.param_map_float.end()) {
			config.set_param_float(paramSlice[i].first, paramSlice[i].second);
		}
		else {
			config.set_param_int(paramSlice[i].first, paramSlice[i].second);
		}
	}

	// set the 1-based index
	config.paramIndex = index + 1;


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

				spdlog::debug("({},{}:{}:{})", item.key(), double(item.value()[0]), double(item.value()[1]), double(item.value()[2]));
			}
			else {
				// the item is a key-value pair
				paramGrid.push_back({ item.key(), item.value(), item.value(), 0.0 });
			}
		}
	}
	catch (const std::exception& e) {
		spdlog::warn("Error: {}", e.what());
		throw std::exception();
	}
	return paramGrid;
}

void TaskGenerator::validateParamRange(const ParamRange& paramRange)
{
	// note: no check is currently made that the steps fit evenly from min->max
	// This means that the last result could be greater than max

	if (paramRange.max < paramRange.min) {
		spdlog::warn("Maximum is less than manimum - for {}", paramRange.name);
		throw std::exception{};
	}

	if (paramRange.step == 0 && paramRange.min != paramRange.max) {
		spdlog::warn("Increment of 0 but minimum and maximum are not equal - for {}", paramRange.name);
		throw std::exception{};
	}

	if (paramRange.step < 0) {
		spdlog::warn("Cannot have a negative increment - for {}", paramRange.name);
		throw std::exception{};
	}
}

std::vector<float> TaskGenerator::makeRange(const ParamRange& paramRange)
{
	validateParamRange(paramRange);

	if (paramRange.min == paramRange.max) {
		return std::vector{ paramRange.min };
	}

	// in order to ensure we generate a range with the correct number of values
	// we create a vector of the correct size and then populate it with multiples of the step

	double num_values = (paramRange.max - paramRange.min) / paramRange.step;
	// Add 1 as the range includes both the min and the max
	num_values += 1;
	auto rangeValues = std::vector<float>(std::lround(num_values));

	for (size_t i = 0; i < rangeValues.size(); i++) {
		rangeValues[i] = paramRange.min + (i * paramRange.step);
	}

	return rangeValues;
}
