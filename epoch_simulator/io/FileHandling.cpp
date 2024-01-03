#include "FileHandling.hpp"

#include <algorithm>
#include <fstream>
#include <iostream>
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
