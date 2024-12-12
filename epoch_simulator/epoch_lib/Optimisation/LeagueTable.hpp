#pragma once

#include <map>
#include <mutex>

#include "../Definitions.hpp"
#include "../io/EpochConfig.hpp"
#include "../io/FileConfig.hpp"
#include "../io/BufferedCSVWriter.hpp"
#include "../Simulation/TaskData.hpp"
#include "TaskGenerator.hpp"

struct ResultIndices {
	std::vector<uint64_t> bestIndices;
	uint64_t worstIndex;
};


class LeagueTable {
public:
	LeagueTable(const OptimiserConfig& optimiserConfig, const FileConfig& fileConfig);

	void considerResult(const SimulationResult& r, const TaskWithIndex& taskWithIndex);

	std::pair<uint64_t, float> getBestCapex() const;
	std::pair<uint64_t, float> getBestAnnualisedCost() const;
	std::pair<uint64_t, float> getBestPaybackHorizon() const;
	std::pair<uint64_t, float> getBestCostBalance() const;
	std::pair<uint64_t, float> getBestCarbonBalance() const;

	std::vector<uint64_t> getAllResults(bool includeWorst=true) const;
	ResultIndices getResultsForObjective(Objective objective) const;


private:
	size_t mCapacity;
	OptimiserConfig mConfig;

	void considerMinimum(std::multimap<float, uint64_t>& subTable, float value, uint64_t paramIndex);
	void considerMaximum(std::multimap<float, uint64_t>& subTable, float value, uint64_t paramIndex);

	void considerMinimumUnderMutex(std::multimap<float, uint64_t>& subTable, float value, uint64_t paramIndex);
	void considerMaximumUnderMutex(std::multimap<float, uint64_t>& subTable, float value, uint64_t paramIndex);

	void considerAsWorst(const SimulationResult& r, uint64_t paramIndex);
	void considerAsWorstUnderMutex(const SimulationResult& r, uint64_t paramIndex);

	enum class TableOrder { ASCENDING, DESCENDING };
	std::vector<uint64_t> mapToParamIndices(const std::multimap<float, uint64_t>& subTable, TableOrder order=TableOrder::ASCENDING) const;


	std::multimap<float, uint64_t> mCapex;
	std::multimap<float, uint64_t> mAnnualisedCost;
	std::multimap<float, uint64_t> mPaybackHorizon;
	std::multimap<float, uint64_t> mCostBalance;
	std::multimap<float, uint64_t> mCarbonBalance;

	// While it might otherwise make more sense for these to be <int, float>  (ie index, value)
	// we keep these in the same order as the multimaps above for internal consistency within the class
	std::pair<float, uint64_t> mWorstCapex;
	std::pair<float, uint64_t> mWorstAnnualisedCost;
	std::pair<float, uint64_t> mWorstPaybackHorizon;
	std::pair<float, uint64_t> mWorstCostBalance;
	std::pair<float, uint64_t> mWorstCarbonBalance;

	std::mutex mMutex;
	std::unique_ptr<BufferedCSVWriter> mBufferedCSVWriter;
};