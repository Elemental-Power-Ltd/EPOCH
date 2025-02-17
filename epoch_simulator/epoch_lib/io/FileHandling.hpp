#pragma once

#include "../Definitions.hpp"
#include "FileConfig.hpp"
#include "../Simulation/SiteData.hpp"

#include <nlohmann/json.hpp>

#include <filesystem>
#include <string>
#include <vector>

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

const SiteData readSiteData(const FileConfig& fileConfig);
const SiteData readSiteData(const std::filesystem::path& siteDataPath);

Eigen::VectorXf toEigen(const std::vector<float>& vec);
Eigen::MatrixXf toEigen(const std::vector<std::vector<float>>& mat);

std::vector<float> toStdVec(const Eigen::VectorXf& vec);
std::vector<std::vector<float>> toStdVecOfVec(const Eigen::MatrixXf& mat);

std::string toIso8601(const std::chrono::system_clock::time_point& tp);
std::chrono::system_clock::time_point fromIso8601(const std::string& isoStr);

