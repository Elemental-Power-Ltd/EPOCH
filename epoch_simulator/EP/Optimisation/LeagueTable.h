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
	std::pair<int, float> getBestCostBalance() const;
	std::pair<int, float> getBestPaybackHorizon() const;
	std::pair<int, float> getBestCarbonBalance() const;

	std::vector<int> toParamIndexList();

private:
	int mCapacity;

	void considerMinimum(std::multimap<float, int>& subTable, float value, int paramIndex);
	void considerMaximum(std::multimap<float, int>& subTable, float value, int paramIndex);

	void considerMinimumUnderMutex(std::multimap<float, int>& subTable, float value, int paramIndex);
	void considerMaximumUnderMutex(std::multimap<float, int>& subTable, float value, int paramIndex);


	std::multimap<float, int> mCapex;
	std::multimap<float, int> mAnnualisedCost;
	std::multimap<float, int> mCostBalance;
	std::multimap<float, int> mPaybackHorizon;
	std::multimap<float, int> mCarbonBalance;

	std::mutex mMutex;
};