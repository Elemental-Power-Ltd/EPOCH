#pragma once

#include <iostream>
#include <limits>
#include <memory>
#include <thread>
#include <vector>

#include <nlohmann/json.hpp>

#include "../io/FileConfig.hpp"
#include "../io/EpochConfig.hpp"
#include "../Definitions.hpp"
#include "LeagueTable.hpp"
#include "TaskGenerator.hpp"


struct paramRange {
	std::string name;
	float min, max, step;
};

// A simple struct for tracking the min/max/mean time per scenario
struct TimeProfile {
	// minTime cannot default to 0
	float minTime = std::numeric_limits<float>::max();
	float maxTime;
	float totalTime;
	uint64_t count;
};

// Limit initialisation to running only the first 100 scenarios
const uint64_t INITIALISATION_MAX_SCENARIOS = 100;


class Optimiser {
public:
	Optimiser(FileConfig fileConfig, EpochConfig config);

	OutputValues runMainOptimisation(nlohmann::json inputJson);
	OutputValues initialiseOptimisation(nlohmann::json inputJson);
	OutputValues RecallIndex(nlohmann::json inputJson, uint64_t recallindex);

private:
	OutputValues doOptimisation(nlohmann::json inputJson, bool initialisationOnly=false);
	int determineWorkerCount();

	void findBestResults(const LeagueTable& leagueTable, OutputValues& output);
	void resetTimeProfiler();
	void addTimeToProfiler(float timeTaken);

	void writeResultsToCSVs(const LeagueTable& leagueTable);
	void reproduceAndWriteToCSV(ResultIndices resultIndices, std::string fileName) const;
	std::vector<ObjectiveResult> reproduceResults(const std::vector<uint64_t>& paramIndices) const;
	ObjectiveResult reproduceResult(uint64_t paramIndex) const;

	FileConfig mFileConfig;
	const EpochConfig mConfig;
	TimeProfile mTimeProfile;
	std::unique_ptr<TaskGenerator> mTaskGenerator;
	const HistoricalData mHistoricalData;
};

