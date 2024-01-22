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

private:
	int mCapacity;

	void considerMinimum(std::map<float, int>& subTable, float value, int paramIndex);
	void considerMaximum(std::map<float, int>& subTable, float value, int paramIndex);

	void considerMinimumUnderMutex(std::map<float, int>& subTable, float value, int paramIndex);
	void considerMaximumUnderMutex(std::map<float, int>& subTable, float value, int paramIndex);


	std::map<float, int> mCapex;
	std::map<float, int> mAnnualisedCost;
	std::map<float, int> mCostBalance;
	std::map<float, int> mPaybackHorizon;
	std::map<float, int> mCarbonBalance;

	std::mutex mMutex;
};