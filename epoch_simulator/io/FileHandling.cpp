#include "FileHandling.hpp"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <regex>
#include <string>
#include <sstream>
#include <vector>

#include "../Definitions.h"



std::vector<float> readCSVColumn(const std::string& filename, int column) {
	std::ifstream file(filename);
	std::vector<float> columnValues;
	std::string line;
	bool columnHasValues = false;

	if (!file.is_open()) {
		std::cerr << "Could not open the file!" << std::endl;
		return columnValues; // Return empty vector
	}

	// Skip the header row
	std::getline(file, line);

	while (std::getline(file, line)) {

		// Check if the line contains only commas (and possibly whitespaces), which indicates the end of the file
		if (std::all_of(line.begin(), line.end(), [](char c) { return c == ',' || std::isspace(c); })) {
			break;
		}

		std::stringstream ss(line);
		std::string cell;
		std::vector<std::string> row;

		// Parse each cell in the row
		while (std::getline(ss, cell, ',')) {
			row.push_back(cell);
		}

		// If the row ends with a comma, add an empty string to the row (signifying an empty column)
		if (line.back() == ',') {
			row.push_back("");
		}

		// Convert the value from the specified column to float and store it in the vector
		int column_1 = column - 1;
		if (row.size() > column_1) {
			if (!row[column_1].empty()) {
				columnHasValues = true;
			}

			if (isValidFloat(row[column_1])) {
				try {
					columnValues.push_back(std::stof(row[column_1]));
				}
				catch (...) {
					std::cerr << "Unknown exception at line: " << line << '\n';
					columnValues.push_back(std::nanf(""));
				}
			}
			else {
				//std::cerr << "Warning: invalid data at line: " << line << '\n';
				columnValues.push_back(std::nanf(""));
			}
		}
		else {
			std::cerr << "Warning: insufficient columns at line: " << line << '\n';
			columnValues.push_back(std::nanf(""));
		}
	}

	if (!columnHasValues) {
		std::fill(columnValues.begin(), columnValues.end(), 0.0f);
	}

	return columnValues;
}

bool isValidFloat(const std::string& str) {
	std::stringstream sstr(str);
	float f;
	return !(sstr >> f).fail() && (sstr >> std::ws).eof();
}


void writeToCSV(std::string absfilepath, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumns) {
	if (dataColumns.empty()) {
		std::cerr << "Data columns are empty!" << std::endl;
		return;
	}

	std::size_t numColumns = dataColumns.size();
	std::size_t numRows = dataColumns[0].second.size();

	// Check if all vectors are of the same length
	for (const auto& dataColumn : dataColumns) {
		if (dataColumn.second.size() != numRows) {
			std::cerr << "Data columns are not of the same length!" << std::endl;
			std::cerr << "Number of rows is:" << dataColumns[0].second.size() << std::endl;
			std::cerr << "Data column is:" << dataColumn.second.size() << std::endl;
			return;
		}
	}

	std::ofstream outFile(absfilepath);

	if (!outFile.is_open()) {
		std::cerr << "Failed to open the output file!" << std::endl;
		return;
	}

	// Write column names as the first row
	for (std::size_t i = 0; i < numColumns; ++i) {
		outFile << dataColumns[i].first;
		if (i < numColumns - 1) {
			outFile << ",";
		}
	}
	outFile << std::endl;

	// Write data rows
	for (std::size_t i = 0; i < numRows; ++i) {
		for (std::size_t j = 0; j < numColumns; ++j) {
			outFile << dataColumns[j].second[i];
			if (j < numColumns - 1) {
				outFile << ",";
			}
		}
		outFile << std::endl;
	}

	outFile.close();
}



void appendCSV(std::string absfilepath, const std::vector<std::pair<std::string, std::vector<float>>>& dataColumns) {
	if (dataColumns.empty()) {
		std::cerr << "Data columns are empty!" << std::endl;
		return;
	}

	std::size_t numColumns = dataColumns.size();
	std::size_t numRows = dataColumns[0].second.size();

	// Check if all vectors are of the same length
	for (const auto& dataColumn : dataColumns) {
		if (dataColumn.second.size() != numRows) {
			std::cerr << "Data columns are not of the same length!" << std::endl;
			std::cerr << "Number of rows is:" << dataColumns[0].second.size() << std::endl;
			std::cerr << "Data column is:" << dataColumn.second.size() << std::endl;
			return;
		}
	}

	// Open file in append mode
	std::ofstream outFile(absfilepath, std::ios::app);

	if (!outFile.is_open()) {
		std::cerr << "Failed to open the output file!" << std::endl;
		return;
	}

	// Check if the file is empty; if it is, write the headers
	outFile.seekp(0, std::ios::end);
	bool isEmpty = !outFile.tellp();
	if (isEmpty) {
		// Write column names as the first row
		for (std::size_t i = 0; i < numColumns; ++i) {
			outFile << dataColumns[i].first;
			if (i < numColumns - 1) {
				outFile << ",";
			}
		}
		outFile << std::endl;
	}

	// Write data rows
	for (std::size_t i = 0; i < numRows; ++i) {
		for (std::size_t j = 0; j < numColumns; ++j) {
			outFile << dataColumns[j].second[i];
			if (j < numColumns - 1) {
				outFile << ",";
			}
		}
		outFile << std::endl;
	}

	outFile.close();
}

// Custom function to convert a struct to a JSON object
nlohmann::json structToJson(const InputValues& data, const MemberMapping mappings[], size_t Size) {
	nlohmann::json jsonObj;
	for (size_t i = 0; i < Size; ++i) {
		const auto& mapping = mappings[i];
		if (mapping.getFloat) {
			jsonObj[mapping.name] = mapping.getFloat(data);
		}
		else if (mapping.getInt) {
			jsonObj[mapping.name] = mapping.getInt(data);
		}
	}
	return jsonObj;
}


// Custom function to convert a struct to a JSON object
nlohmann::json structToJsonOut(const OutputValues& data, const OutMemberMapping mappings[], size_t Size) {
	nlohmann::json jsonObj;
	for (size_t i = 0; i < Size; ++i) {
		const auto& mapping = mappings[i];
		if (mapping.getFloat) {
			jsonObj[mapping.name] = mapping.getFloat(data);
		}
		else if (mapping.getInt) {
			jsonObj[mapping.name] = mapping.getInt(data);
		}
	}
	return jsonObj;
}

// function to group the keys in a JSON, such that we have a key-tuple JSON describing parameter ranges
nlohmann::json convert_to_ranges(nlohmann::json& j) {
	// This regex matches strings ending with "_lower", "_upper", or "_step"
	std::regex param_regex("(.+)(_lower|_upper|_step)$");
	std::smatch match;

	nlohmann::json new_json;
	for (auto& el : j.items()) {
		std::string key = el.key();
		if (std::regex_match(key, match, param_regex)) {
			// Extract the base parameter name and the suffix
			std::string param_base = match[1].str();
			std::string suffix = match[2].str();

			// Initialize the tuple if it doesn't exist
			if (!new_json.contains(param_base)) {
				//				new_json[param_base] = nlohmann::json::array({ nullptr, nullptr, nullptr });
				new_json[param_base] = nlohmann::json::array({ 0.0, 0.0, 0.0 });
			}

			// Assign the value to the correct position in the tuple
//			if (suffix == "_lower") new_json[param_base][0] = el.value();
//			else if (suffix == "_upper") new_json[param_base][1] = el.value();
//			else if (suffix == "_step") new_json[param_base][2] = el.value();
			if (suffix == "_lower") new_json[param_base][0] = el.value().is_null() ? nlohmann::json(0.0) : el.value();
			else if (suffix == "_upper") new_json[param_base][1] = el.value().is_null() ? nlohmann::json(0.0) : el.value();
			else if (suffix == "_step") new_json[param_base][2] = el.value().is_null() ? nlohmann::json(0.0) : el.value();
		}
		else {
			// Copy over any keys that don't match the pattern
			new_json[key] = el.value();
		}
	}

	return new_json;
}

nlohmann::json handleJsonConversion(const InputValues& inputValues, const MemberMapping memberMappings[], size_t size) {
	// Aim: to export 'inputvalues' to a json file that can be read e.g. as a Python dict, s.t. other EPL software can use this as an input

	nlohmann::json jsonObj = structToJson(inputValues, memberMappings, size);
	writeJsonToFile(jsonObj, "parameters.json");

	nlohmann::json converted_json = convert_to_ranges(jsonObj);
	writeJsonToFile(converted_json, "parameters_grouped.json");

	std::cout << "JSON file written successfully!" << std::endl;

	return converted_json;

}

void writeJsonToFile(const nlohmann::json& jsonObj, std::string filename) {
	try {
		std::ofstream file(filename);
		file << jsonObj.dump(4);  // The "4" argument adds pretty-printing with indentation
		file.close();
	}
	catch (const std::exception e) {
		std::cerr << "Error: " << e.what() << std::endl;
	}
}
	
