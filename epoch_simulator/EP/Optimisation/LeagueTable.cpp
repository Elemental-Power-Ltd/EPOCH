#include "LeagueTable.h"

#include <set>

LeagueTable::LeagueTable(int capacity)
{
	mCapacity = capacity;
}

void LeagueTable::considerResult(const SimulationResult& r)
{
	// CAPEX
	considerMinimum(mCapex, r.project_CAPEX, r.paramIndex);

	// Annualised Cost
	considerMinimum(mAnnualisedCost, r.total_annualised_cost, r.paramIndex);

	// Cost Balance
	considerMaximum(mCostBalance, r.scenario_cost_balance, r.paramIndex);

	// Payback Horizon
	considerMinimum(mPaybackHorizon, r.payback_horizon_years, r.paramIndex);

	// Carbon Balance
	considerMaximum(mCarbonBalance, r.scenario_carbon_balance, r.paramIndex);
}

std::pair<int, float> LeagueTable::getBestCapex() const
{
	// first/smallest is best
	auto best = mCapex.begin();
	return std::pair<int, float>(best->second, best->first);
}

std::pair<int, float> LeagueTable::getBestAnnualisedCost() const
{
	// first/smallest is best
	auto best = mAnnualisedCost.begin();
	return std::pair<int, float>(best->second, best->first);
}

std::pair<int, float> LeagueTable::getBestCostBalance() const
{
	// last/largest is best
	auto best = mCostBalance.rbegin();
	return std::pair<int, float>(best->second, best->first);
}

std::pair<int, float> LeagueTable::getBestPaybackHorizon() const
{
	// first/smallest is best
	auto best = mPaybackHorizon.begin();
	return std::pair<int, float>(best->second, best->first);
}

std::pair<int, float> LeagueTable::getBestCarbonBalance() const
{
	// last/largest is best
	auto best = mCarbonBalance.rbegin();
	return std::pair<int, float>(best->second, best->first);
}

// return the parameter indices of the results held in the league table
// each paramIndex can then be used to reproduce the full result
std::vector<int> LeagueTable::toParamIndexList()
{
	// It is possible to have the same paramIndex in multiple of the subTables
	// For this reason, put the results into a set first to remove duplicates
	std::set<int> resultSet = {};

	for (const auto& res : mCapex) {
		resultSet.insert(res.second);
	}

	for (const auto& res : mAnnualisedCost) {
		resultSet.insert(res.second);
	}

	for (const auto& res : mCostBalance) {
		resultSet.insert(res.second);
	}

	for (const auto& res : mPaybackHorizon) {
		resultSet.insert(res.second);
	}

	for (const auto& res : mCarbonBalance) {
		resultSet.insert(res.second);
	}

	std::vector<int> results(resultSet.begin(), resultSet.end());

	return results;
}

// consider inserting a simulation result (identified by paramIndex and value)
// we are trying to minimise the value
void LeagueTable::considerMinimum(std::multimap<float, int>& subTable, float value, int paramIndex)
{
	if (subTable.size() < mCapacity) {
		// We are below the capacity of the league table
		// Insert the result
		considerMinimumUnderMutex(subTable, value, paramIndex);
		return;
	}

	// we are minimising so the worst result is the last/largest
	if (subTable.rbegin()->first > value) {
		// The worst result in the league table is worse than r
		considerMinimumUnderMutex(subTable, value, paramIndex);
	}
}

// consider inserting a simulation result (identified by paramIndex and value)
// we are trying to maximise the value
void LeagueTable::considerMaximum(std::multimap<float, int>& subTable, float value, int paramIndex)
{
	if (subTable.size() < mCapacity) {
		// We are below the capacity of the league table
		// Insert the result
		considerMaximumUnderMutex(subTable, value, paramIndex);
		return;
	}

	// we are maximising so the worst result is the first/smallest
	if (subTable.begin()->first < value) {
		// The worst result in the league table is worse than r
		considerMaximumUnderMutex(subTable, value, paramIndex);
	}
}

void LeagueTable::considerMinimumUnderMutex(std::multimap<float, int>& subTable, float value, int paramIndex)
{
	std::lock_guard<std::mutex> guard(mMutex);

	if (subTable.size() < mCapacity) {
		// We are below the capacity of the league table
		// Insert the result
		subTable.insert({ value, paramIndex });

		return;
	}

	// we are minimising so the worst result is the last/largest
	if (subTable.rbegin()->first > value) {
		// The worst result in the league table is worse than r
		// remove the worst result
		auto worst = subTable.end();
		worst--;
		subTable.erase(worst);

		// insert the new result from r
		subTable.insert({ value, paramIndex });
	}
}

void LeagueTable::considerMaximumUnderMutex(std::multimap<float, int>& subTable, float value, int paramIndex)
{
	std::lock_guard<std::mutex> guard(mMutex);

	if (subTable.size() < mCapacity) {
		// We are below the capacity of the league table
		// Insert the result
		subTable.insert({ value, paramIndex });
		return;
	}

	// we are maximising so the worst result is the first/smallest
	if (subTable.begin()->first < value) {
		// The worst result in the league table is worse than r
		// remove the worst result
		subTable.erase(subTable.begin());

		// insert the new result from r
		subTable.insert({ value, paramIndex });
	}
}
