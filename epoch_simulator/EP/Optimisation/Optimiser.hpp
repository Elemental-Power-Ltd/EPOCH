#pragma once

#include <iostream>
#include <limits>
#include <memory>
#include <thread>
#include <vector>

#include "../dependencies/json.hpp"
#include "../io/FileConfig.h"
#include "Threadsafe.h"
#include "../Definitions.h"
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
	int count;
};

// Limit initialisation to running only the first 100 scenarios
const int INITIALISATION_MAX_SCENARIOS = 100;


class Optimiser {
public:
	Optimiser(FileConfig fileConfig);

	OutputValues runMainOptimisation(nlohmann::json inputJson);
	OutputValues initialiseOptimisation(nlohmann::json inputJson);
	OutputValues RecallIndex(nlohmann::json inputJson, int recallindex);


private:
	const HistoricalData readHistoricalData();
	OutputValues doOptimisation(nlohmann::json inputJson, bool initialisationOnly=false);
	int determineWorkerCount();

	void findBestResults(const LeagueTable& leagueTable, OutputValues& output);
	void resetTimeProfiler();
	void addTimeToProfiler(float timeTaken);

	std::vector<SimulationResult> reproduceResults(const std::vector<int>& paramIndices);
	SimulationResult reproduceResult(int paramIndex);

	FileConfig mFileConfig;
	TimeProfile mTimeProfile;
	std::unique_ptr<TaskGenerator> mTaskGenerator;
	const HistoricalData mHistoricalData;
};

