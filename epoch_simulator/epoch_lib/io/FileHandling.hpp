#pragma once

#include "../Definitions.hpp"
#include "FileConfig.hpp"

#include <nlohmann/json.hpp>

#include <filesystem>
#include <string>
#include <vector>


std::vector<float> readCSVColumn(const std::filesystem::path& filename, int column, bool skipHeader);
std::vector<float> readCSVColumnAndSkipHeader(const std::filesystem::path& filename, int column);
std::vector<float> readCSVColumnWithoutSkip(const std::filesystem::path& filename, int column);
std::vector<std::vector<float>> readCSVAsTable(const std::filesystem::path& filename);
size_t countColumns(const std::filesystem::path& filename);
std::vector<year_TS> readImportTariffs(const std::filesystem::path& filename);

void writeResultsToCSV(std::filesystem::path filepath, const std::vector<ObjectiveResult>& results);
void appendResultToCSV(std::filesystem::path filepath, const ObjectiveResult& result);

void writeObjectiveResultHeader(std::ofstream& outFile);
void writeObjectiveResultRow(std::ofstream& outFile, const ObjectiveResult& result);

std::string valueOrEmpty(const year_TS& vec, Eigen::Index i);
void writeTimeSeriesToCSV(std::filesystem::path filepath, const ReportData& reportData);

nlohmann::json outputToJson(const OutputValues& data);
nlohmann::json convert_to_ranges(nlohmann::json& j);

void writeJsonToFile(const nlohmann::json& jsonObj, std::filesystem::path filepath);
nlohmann::json readJsonFromFile(std::filesystem::path filepath);

const HistoricalData readHistoricalData(const FileConfig& fileConfig);
Eigen::VectorXf toEigen(const std::vector<float>& vec);
Eigen::MatrixXf toEigen(const std::vector<std::vector<float>>& mat);
