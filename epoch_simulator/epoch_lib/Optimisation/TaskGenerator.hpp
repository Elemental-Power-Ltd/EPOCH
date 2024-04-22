#pragma once

#include <mutex>
#include <vector>

#include <nlohmann/json.hpp>

#include "../Simulation/TaskData.hpp"


struct ParamRange {
	std::string name;
	float min, max, step;
};

struct ExpandedParamRange {
	std::string name;
	std::vector<float> values;
	uint64_t cumulativeProduct;
};

constexpr uint64_t MAX_SCENARIOS_FOR_INITIALISATION = 100;

class TaskGenerator {
public:
	TaskGenerator(const nlohmann::json& inputJson, bool initialisationOnly);

	uint64_t totalScenarios() const;
	bool nextTask(TaskData& taskData);
	TaskData getTask(uint64_t index) const;

private:
	std::vector<ParamRange> makeParamGrid(const nlohmann::json& inputJson);
	void validateParamRange(const ParamRange& paramRange);
	std::vector<float> makeRange(const ParamRange& paramRange);

	std::atomic<uint64_t> mScenarioCounter;
	uint64_t mTotalScenarios;
	uint64_t mScenarioLimit;
	std::vector<ParamRange> mParamGrid;
	std::vector<ExpandedParamRange> mExpandedParamGrid;
};
