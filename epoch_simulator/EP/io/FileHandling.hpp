#pragma once

#include "../dependencies/json.hpp"
#include "../Definitions.h"

#include <string>
#include <vector>


std::vector<float> readCSVColumn(const std::string& filename, int column);
bool isValidFloat(const std::string& str);
void writeToCSV(std::string absfilepath, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumns);
void appendCSV(std::string absfilepath, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumns);

nlohmann::json structToJson(const InputValues& data, const MemberMapping mappings[], size_t Size);
nlohmann::json structToJsonOut(const OutputValues& data, const OutMemberMapping mappings[], size_t Size);
nlohmann::json convert_to_ranges(nlohmann::json& j);

nlohmann::json handleJsonConversion(const InputValues& inputValues, const MemberMapping memberMappings[], size_t size);

void writeJsonToFile(const nlohmann::json& jsonObj, std::string filename);