#pragma once

#include <mutex>
#include <vector>

#include "../dependencies/json.hpp"
#include "../Simulation/Config.h"


struct ParamRange {
	std::string name;
	float min, max, step;
};

struct ExpandedParamRange {
	std::string name;
	std::vector<float> values;
	int cumulativeProduct;
};

constexpr int MAX_SCENARIOS_FOR_INITIALISATION = 100;

class TaskGenerator {
public:
	TaskGenerator(const nlohmann::json& inputJson, bool initialisationOnly);

	const int totalScenarios();
	bool nextTask(Config& config);
	Config getTask(int index);

private:
	std::vector<ParamRange> makeParamGrid(const nlohmann::json& inputJson);
	void validateParamRange(const ParamRange& paramRange);
	std::vector<float> makeRange(const ParamRange& paramRange);

	std::atomic<int> mScenarioCounter;
	int mTotalScenarios;
	int mScenarioLimit;
	std::vector<ParamRange> mParamGrid;
	std::vector<ExpandedParamRange> mExpandedParamGrid;
};
