#pragma once

#include <iostream>
#include <limits>
#include <thread>
#include <vector>

#include "../dependencies/json.hpp"
#include "../io/FileConfig.h"
#include "Threadsafe.h"
#include "../Definitions.h"


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
	HistoricalData readHistoricalData();
	std::vector<paramRange> makeParamGrid(const nlohmann::json& inputJson);
	int generateTasks(const std::vector<paramRange>& paramGrid, SafeQueue<std::vector<std::pair<std::string, float>>>& taskQueue, bool initialisationOnly);
	OutputValues doOptimisation(nlohmann::json inputJson, bool initialisationOnly=false);
	int determineWorkerCount();

	void findBestResults(const std::vector<SimulationResult>& allResults, OutputValues& output);
	void resetTimeProfiler();
	void addTimeToProfiler(float timeTaken);

	std::vector<std::pair<std::string, float>> TaskRecall(const std::vector<paramRange>& paramGrid, int index);

	FileConfig mFileConfig;
	TimeProfile mTimeProfile;
};

