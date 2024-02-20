#include "LeagueTable.hpp"

#include <set>

LeagueTable::LeagueTable(int capacity):
	mCapacity(capacity),
	mWorstCapex{ -FLT_MAX, 0},
	mWorstAnnualisedCost{ -FLT_MAX, 0 },
	mWorstCostBalance{ FLT_MAX, 0 },
	mWorstPaybackHorizon{ -FLT_MAX ,0},
	mWorstCarbonBalance{ FLT_MAX, 0 }
{}

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

	considerAsWorst(r);
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
std::vector<int> LeagueTable::toParamIndexList(bool includeWorst)
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

	if (includeWorst) {
		resultSet.insert(mWorstCapex.second);
		resultSet.insert(mWorstAnnualisedCost.second);
		resultSet.insert(mWorstCostBalance.second);
		resultSet.insert(mWorstPaybackHorizon.second);
		resultSet.insert(mWorstCarbonBalance.second);
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

void LeagueTable::considerAsWorst(const SimulationResult& r)
{
	// if any of the objectives are the worst seen so far, acquire the mutex and check again
	if (r.project_CAPEX > mWorstCapex.first ||
		r.total_annualised_cost > mWorstAnnualisedCost.first ||
		r.payback_horizon_years > mWorstPaybackHorizon.first ||
		r.scenario_cost_balance < mWorstCostBalance.first ||
		r.scenario_carbon_balance < mWorstCarbonBalance.first
		) {
		considerAsWorstUnderMutex(r);
	}
}

void LeagueTable::considerAsWorstUnderMutex(const SimulationResult& r)
{
	std::lock_guard<std::mutex> guard(mMutex);

	//////// Minimising objectives ////////
	// CAPEX
	if (r.project_CAPEX > mWorstCapex.first) {
		mWorstCapex = { r.project_CAPEX, r.paramIndex };
	}

	// Annualised Cost
	if (r.total_annualised_cost > mWorstAnnualisedCost.first) {
		mWorstAnnualisedCost = { r.total_annualised_cost, r.paramIndex };
	}

	// Payback Horizon
	if (r.payback_horizon_years > mWorstPaybackHorizon.first) {
		mWorstPaybackHorizon = { r.payback_horizon_years, r.paramIndex };
	}


	//////// Maximising objectives ////////
	// Cost Balance
	if (r.scenario_cost_balance < mWorstCostBalance.first) {
		mWorstCostBalance = { r.scenario_cost_balance, r.paramIndex };
	}

	// Carbon Balance
	if (r.scenario_carbon_balance < mWorstCarbonBalance.first) {
		mWorstCarbonBalance = { r.scenario_carbon_balance, r.paramIndex };
	}
}
