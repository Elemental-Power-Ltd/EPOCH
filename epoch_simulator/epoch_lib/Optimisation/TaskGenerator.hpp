#pragma once

#include <atomic>
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

struct TaskWithIndex {
	TaskData task;
	uint64_t index;
};

class TaskGenerator {
public:
	TaskGenerator(const nlohmann::json& inputJson);

	uint64_t totalScenarios() const;
	bool nextTask(TaskWithIndex& taskWithIndex);
	TaskData getTask(uint64_t index) const;

private:
	std::vector<ParamRange> makeParamGrid(const nlohmann::json& inputJson);
	void validateParamRange(const ParamRange& paramRange);
	std::vector<float> makeRange(const ParamRange& paramRange);

	std::atomic<uint64_t> mScenarioCounter;
	uint64_t mTotalScenarios;
	std::vector<ParamRange> mParamGrid;
	std::vector<ExpandedParamRange> mExpandedParamGrid;
};
