#include "LeagueTable.hpp"
#include <cfloat>

LeagueTable::LeagueTable(const OptimiserConfig& optimiserConfig, const FileConfig& fileConfig) :
	mCapacity(optimiserConfig.leagueTableCapacity),
	mConfig(optimiserConfig),
	mWorstCapex{ -FLT_MAX, 0},
	mWorstAnnualisedCost{ -FLT_MAX, 0 },
	mWorstPaybackHorizon{ -FLT_MAX ,0},
	mWorstCostBalance{ FLT_MAX, 0 },
	mWorstCarbonBalance{ FLT_MAX, 0 }
{
	if (mConfig.produceExhaustiveOutput) {
		mBufferedCSVWriter = std::make_unique<BufferedCSVWriter>(fileConfig.getOutputDir() / "ExhaustiveResults.csv");

		spdlog::warn("Writing exhaustive output to CSV. Performance will be reduced");

	}
}

void LeagueTable::considerResult(const SimulationResult& r, const TaskWithIndex& taskWithIndex)
{
	// CAPEX
	considerMinimum(mCapex, r.metrics.total_capex, taskWithIndex.index);

	// Annualised Cost
	considerMinimum(mAnnualisedCost, r.metrics.total_annualised_cost, taskWithIndex.index);

	// Payback Horizon
	// FIXME - payback horizon can now be negative, if we restore grid search this will need changing
	considerMinimum(mPaybackHorizon, r.comparison.payback_horizon_years, taskWithIndex.index);

	// Cost Balance
	considerMaximum(mCostBalance, r.comparison.cost_balance, taskWithIndex.index);

	// Carbon Balance
	considerMaximum(mCarbonBalance, r.comparison.carbon_balance_scope_1, taskWithIndex.index);

	considerAsWorst(r, taskWithIndex.index);

	if (mConfig.produceExhaustiveOutput) {
		mBufferedCSVWriter->writeResult(toObjectiveResult(r, taskWithIndex.task));
	}
}

std::pair<uint64_t, float> LeagueTable::getBestCapex() const
{
	// first/smallest is best
	auto best = mCapex.begin();
	return std::pair<uint64_t, float>(best->second, best->first);
}

std::pair<uint64_t, float> LeagueTable::getBestAnnualisedCost() const
{
	// first/smallest is best
	auto best = mAnnualisedCost.begin();
	return std::pair<uint64_t, float>(best->second, best->first);
}

std::pair<uint64_t, float> LeagueTable::getBestPaybackHorizon() const
{
	// first/smallest is best
	auto best = mPaybackHorizon.begin();
	return std::pair<uint64_t, float>(best->second, best->first);
}

std::pair<uint64_t, float> LeagueTable::getBestCostBalance() const
{
	// last/largest is best
	auto best = mCostBalance.rbegin();
	return std::pair<uint64_t, float>(best->second, best->first);
}

std::pair<uint64_t, float> LeagueTable::getBestCarbonBalance() const
{
	// last/largest is best
	auto best = mCarbonBalance.rbegin();
	return std::pair<uint64_t, float>(best->second, best->first);
}

// return the parameter indices of the results held in the league table
// each paramIndex can then be used to reproduce the full result
std::vector<uint64_t> LeagueTable::getAllResults(bool includeWorst) const {
	std::vector<uint64_t> allResults{};

	auto capexResults = getResultsForObjective(Objective::CAPEX);
	allResults.insert(allResults.end(), capexResults.bestIndices.begin(), capexResults.bestIndices.end());

	auto annualisedCostResults = getResultsForObjective(Objective::AnnualisedCost);
	allResults.insert(allResults.end(), annualisedCostResults.bestIndices.begin(), annualisedCostResults.bestIndices.end());

	auto paybackHorizonResults = getResultsForObjective(Objective::PaybackHorizon);
	allResults.insert(allResults.end(), paybackHorizonResults.bestIndices.begin(), paybackHorizonResults.bestIndices.end());

	auto costBalanceResults = getResultsForObjective(Objective::CostBalance);
	allResults.insert(allResults.end(), costBalanceResults.bestIndices.begin(), costBalanceResults.bestIndices.end());

	auto carbonBalanceResults = getResultsForObjective(Objective::CarbonBalance);
	allResults.insert(allResults.end(), carbonBalanceResults.bestIndices.begin(), carbonBalanceResults.bestIndices.end());

	if (includeWorst) {
		allResults.emplace_back(mWorstCapex.second);
		allResults.emplace_back(mWorstAnnualisedCost.second);
		allResults.emplace_back(mWorstPaybackHorizon.second);
		allResults.emplace_back(mWorstCostBalance.second);
		allResults.emplace_back(mWorstCarbonBalance.second);
	}

	return allResults;
}

ResultIndices LeagueTable::getResultsForObjective(Objective objective) const {

	ResultIndices result;

	switch (objective) {
	case Objective::CAPEX:
		result.bestIndices = mapToParamIndices(mCapex);
		result.worstIndex = mWorstCapex.second;
		return result;
	case Objective::AnnualisedCost:
		result.bestIndices = mapToParamIndices(mAnnualisedCost);
		result.worstIndex = mWorstAnnualisedCost.second;
		return result;
	case Objective::PaybackHorizon:
		result.bestIndices = mapToParamIndices(mPaybackHorizon);
		result.worstIndex = mWorstPaybackHorizon.second;
		return result;
	case Objective::CarbonBalance:
		result.bestIndices = mapToParamIndices(mCarbonBalance, TableOrder::DESCENDING);
		result.worstIndex = mWorstCarbonBalance.second;
		return result;
	case Objective::CostBalance:
		result.bestIndices = mapToParamIndices(mCostBalance, TableOrder::DESCENDING);
		result.worstIndex = mWorstCostBalance.second;
		return result;
	default:
		return result;
	}
}

// consider inserting a simulation result (identified by paramIndex and value)
// we are trying to minimise the value
void LeagueTable::considerMinimum(std::multimap<float, uint64_t>& subTable, float value, uint64_t paramIndex)
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
void LeagueTable::considerMaximum(std::multimap<float, uint64_t>& subTable, float value, uint64_t paramIndex)
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

void LeagueTable::considerMinimumUnderMutex(std::multimap<float, uint64_t>& subTable, float value, uint64_t paramIndex)
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

void LeagueTable::considerMaximumUnderMutex(std::multimap<float, uint64_t>& subTable, float value, uint64_t paramIndex)
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

void LeagueTable::considerAsWorst(const SimulationResult& r, uint64_t paramIndex) {
	// if any of the objectives are the worst seen so far, acquire the mutex and check again
	if (r.metrics.total_capex > mWorstCapex.first ||
		r.metrics.total_annualised_cost > mWorstAnnualisedCost.first ||
		r.comparison.payback_horizon_years > mWorstPaybackHorizon.first ||
		r.comparison.cost_balance < mWorstCostBalance.first ||
		r.comparison.carbon_balance_scope_1 < mWorstCarbonBalance.first
		) {
		considerAsWorstUnderMutex(r, paramIndex);
	}
}

void LeagueTable::considerAsWorstUnderMutex(const SimulationResult& r, uint64_t paramIndex) {
	std::lock_guard<std::mutex> guard(mMutex);

	//////// Minimising objectives ////////
	// CAPEX
	if (r.metrics.total_capex > mWorstCapex.first) {
		mWorstCapex = { r.metrics.total_capex, paramIndex };
	}

	// Annualised Cost
	if (r.metrics.total_annualised_cost > mWorstAnnualisedCost.first) {
		mWorstAnnualisedCost = { r.metrics.total_annualised_cost, paramIndex };
	}

	// Payback Horizon
	if (r.comparison.payback_horizon_years > mWorstPaybackHorizon.first) {
		mWorstPaybackHorizon = { r.comparison.payback_horizon_years, paramIndex };
	}


	//////// Maximising objectives ////////
	// Cost Balance
	if (r.comparison.cost_balance < mWorstCostBalance.first) {
		mWorstCostBalance = { r.comparison.cost_balance, paramIndex };
	}

	// Carbon Balance
	if (r.comparison.carbon_balance_scope_1 < mWorstCarbonBalance.first) {
		mWorstCarbonBalance = { r.comparison.carbon_balance_scope_1, paramIndex };
	}
}

std::vector<uint64_t> LeagueTable::mapToParamIndices(const std::multimap<float, uint64_t>& subTable, TableOrder order) const {

	std::vector<uint64_t> indices{};
	indices.reserve(subTable.size());

	if (order == TableOrder::ASCENDING) {
		for (const auto& [_, paramIndex] : subTable) {
			indices.emplace_back(paramIndex);
		}
	} else {  //TableOrder::DESCENDING
		// This objective is a maximising objective, use a reverse iterator to return the largest result first
		for (auto it = subTable.rbegin(); it != subTable.rend(); ++it) {
			indices.emplace_back(it->second);
		}
	}

	return indices;
}
