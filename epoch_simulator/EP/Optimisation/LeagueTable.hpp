#pragma once



#include <map>
#include <mutex>

#include "../Definitions.h"


class LeagueTable {
public:
	LeagueTable(int capacity);

	void considerResult(const SimulationResult& r);

	std::pair<int, float> getBestCapex() const;
	std::pair<int, float> getBestAnnualisedCost() const;
	std::pair<int, float> getBestPaybackHorizon() const;
	std::pair<int, float> getBestCostBalance() const;
	std::pair<int, float> getBestCarbonBalance() const;

	std::vector<int> toParamIndexList(bool includeWorst=true);

private:
	int mCapacity;

	void considerMinimum(std::multimap<float, int>& subTable, float value, int paramIndex);
	void considerMaximum(std::multimap<float, int>& subTable, float value, int paramIndex);

	void considerMinimumUnderMutex(std::multimap<float, int>& subTable, float value, int paramIndex);
	void considerMaximumUnderMutex(std::multimap<float, int>& subTable, float value, int paramIndex);

	void considerAsWorst(const SimulationResult& r);
	void considerAsWorstUnderMutex(const SimulationResult& r);


	std::multimap<float, int> mCapex;
	std::multimap<float, int> mAnnualisedCost;
	std::multimap<float, int> mPaybackHorizon;
	std::multimap<float, int> mCostBalance;
	std::multimap<float, int> mCarbonBalance;

	// While it might otherwise make more sense for these to be <int, float>  (ie index, value)
	// we keep these in the same order as the multimaps above for internal consistency within the class
	std::pair<float, int> mWorstCapex;
	std::pair<float, int> mWorstAnnualisedCost;
	std::pair<float, int> mWorstPaybackHorizon;
	std::pair<float, int> mWorstCostBalance;
	std::pair<float, int> mWorstCarbonBalance;


	std::mutex mMutex;
};