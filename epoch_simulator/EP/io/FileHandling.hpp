#pragma once

#include "../dependencies/json.hpp"
#include "../Definitions.h"

#include <string>
#include <vector>


std::vector<float> readCSVColumn(const std::string& filename, int column);
bool isValidFloat(const std::string& str);
void writeToCSV(std::string absfilepath, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumns);
void appendCSV(std::string absfilepath, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumns);

nlohmann::json inputToJson(const InputValues& data);
nlohmann::json outputToJson(const OutputValues& data);
nlohmann::json convert_to_ranges(nlohmann::json& j);

nlohmann::json handleJsonConversion(const InputValues& inputValues);

void writeJsonToFile(const nlohmann::json& jsonObj, std::string filename);

