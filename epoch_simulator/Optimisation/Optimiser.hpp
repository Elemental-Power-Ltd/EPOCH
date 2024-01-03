#pragma once

#include <iostream>
#include <thread>
#include <vector>

#include "../json.hpp"
#include "../FileIO.h"
#include "../Threadsafe.h"
#include "../Definitions.h"


struct paramRange {
	std::string name;
	float min, max, step;
};

class Optimiser {
public:
	Optimiser();

	OutputValues runMainOptimisation(nlohmann::json inputJson);
	OutputValues initialiseOptimisation(nlohmann::json inputJson);
	OutputValues RecallIndex(nlohmann::json inputJson, int recallindex);


private:
	int generateTasks(const std::vector<paramRange>& paramGrid, SafeQueue<std::vector<std::pair<std::string, float>>>& taskQueue);
	void appendSumToDataTable(CustomDataTable& outTable, CustomDataTable& singleTable);
	std::pair<float, float> findMinValueandIndex(const CustomDataTable& dataColumns, const std::string& columnName);
	std::pair<float, float> findMaxValueandIndex(const CustomDataTable& dataColumns, const std::string& columnName);
	std::tuple<float, float, float> getColumnStats(const std::vector<std::pair<std::string, std::vector<float>>>& CustomDataTable);
	void appendDataColumns(std::vector<std::pair<std::string, std::vector<float>>>& cumDataColumns, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumnsN);
	CustomDataTable SumDataTable(const CustomDataTable& dataTable);


	std::vector<std::pair<std::string, float>> TaskRecall(const std::vector<paramRange>& paramGrid, int index);

};

