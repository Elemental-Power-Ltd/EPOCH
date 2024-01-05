#pragma once

#define NOMINMAX  // necessary before including windows.h

#include "EP_FE_full.h"

#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <fstream>
#include <functional>
#include <future>
#include <iostream> 
#include <limits>
#include <map>
#include <mutex>
#include <numeric>
#include <optional>
#include <queue>
#include <regex>
#include <sstream>
#include <string>
#include <thread>
#include <utility>
#include <vector>
#include <xmmintrin.h> 
#include <windows.h>

#include "GUI/gui.hpp"

#include "EP/dependencies/json.hpp"
#include "EP/io/FileHandling.hpp"
#include "EP/Optimisation/Optimiser.hpp"


void workerFunction(SafeQueue<std::map<std::string, float>>& taskQueue) {
	std::map<std::string, float> task;
	while (taskQueue.pop(task)) {
		// Process the task (param_slice)
		// ...

		// Check if there are more tasks to process
		if (taskQueue.empty()) {
			break;
		}
	}
}

float findMinValue(const CustomDataTable& dataColumns, const std::string& columnName) {
	const std::vector<float>* targetColumn = nullptr;
	const std::vector<float>* paramIndexColumn = nullptr;

	// Find the target column and paramIndex column
	for (const auto& column : dataColumns) {
		if (column.first == columnName) {
			targetColumn = &column.second;
		}
		if (column.first == "Parameter index") {
			paramIndexColumn = &column.second;
		}
	}

	if (!targetColumn || !paramIndexColumn) {
		throw std::runtime_error("Specified column or Parameter index column not found");
	}

	if (targetColumn->size() != paramIndexColumn->size()) {
		throw std::runtime_error("Inconsistent data size between columns");
	}

	float minValue = std::numeric_limits<float>::max();
	float correspondingParamIndex = -1;

	for (size_t i = 0; i < targetColumn->size(); ++i) {
		if ((*targetColumn)[i] < minValue) {
			minValue = (*targetColumn)[i];
			correspondingParamIndex = (*paramIndexColumn)[i];
		}
	}

	return minValue;
}

float findMaxValue (const CustomDataTable& dataColumns, const std::string& columnName) {
	const std::vector<float>* targetColumn = nullptr;
	const std::vector<float>* paramIndexColumn = nullptr;

	// Find the target column and paramIndex column
	for (const auto& column : dataColumns) {
		if (column.first == columnName) {
			targetColumn = &column.second;
		}
		if (column.first == "Parameter index") {
			paramIndexColumn = &column.second;
		}
	}

	if (!targetColumn || !paramIndexColumn) {
		throw std::runtime_error("Specified column or Parameter index column not found");
	}

	if (targetColumn->size() != paramIndexColumn->size()) {
		throw std::runtime_error("Inconsistent data size between columns");
	}

	// Initialize with the lowest possible float value
	float maxValue = std::numeric_limits<float>::lowest();
	float correspondingParamIndex = -1;

	for (size_t i = 0; i < targetColumn->size(); ++i) {
		// Compare to find the maximum value
		if ((*targetColumn)[i] > maxValue) {
			maxValue = (*targetColumn)[i];
			correspondingParamIndex = (*paramIndexColumn)[i];
		}
	}

	return maxValue;
}


std::vector<std::pair<std::string, float>> ParamRecall(const std::vector<paramRange>& paramGrid, int index) { // now depreciated 11_12_2023
	std::vector<std::pair<std::string, float>> paramSlice;

	for (const auto& range : paramGrid) {
		int numValues = static_cast<int>((range.max - range.min) / range.step) + 1;
		int valueIndex = (index % numValues);
		float value = range.min + valueIndex * range.step;

		paramSlice.emplace_back(range.name, value);

		index /= numValues;
	}

	return paramSlice;
}

float computeMin(SafeQueue<CustomDataTable>& queue, const std::string& columnName) {
	float minValue = std::numeric_limits<float>::max();
	CustomDataTable dataTable;

	while (!queue.empty()) {
		if (queue.try_pop(dataTable)) {
			for (const auto& pair : dataTable) {
				if (pair.first == columnName) {
					for (float value : pair.second) {
						minValue = std::min(minValue, value);
					}
				}
			}
		}
		std::this_thread::sleep_for(std::chrono::seconds(1));
	}

	// Process the min and max values as needed
	return minValue;
}


float computeMax(SafeQueue<CustomDataTable>& queue, const std::string& columnName) {
	float maxValue = std::numeric_limits<float>::lowest();
	CustomDataTable dataTable;

	while (!queue.empty()) {
		if (queue.try_pop(dataTable)) {
			for (const auto& pair : dataTable) {
				if (pair.first == columnName) {
					for (float value : pair.second) {
						maxValue = std::max(maxValue, value);
					}
				}
			}
		}
		std::this_thread::sleep_for(std::chrono::seconds(1));// Optionally, add a small sleep here to reduce CPU usage
	}

	// Process the min and max values as needed
	return maxValue;
}


int APIENTRY wWinMain(_In_ HINSTANCE hInstance,
	_In_opt_ HINSTANCE hPrevInstance,
	_In_ LPWSTR    lpCmdLine,
	_In_ int       nCmdShow)
{
	UNREFERENCED_PARAMETER(hPrevInstance);
	UNREFERENCED_PARAMETER(lpCmdLine);

	// TODO: Place code here.


	// Initialize global strings
	LoadStringW(hInstance, IDS_APP_TITLE, szTitle, MAX_LOADSTRING);
	LoadStringW(hInstance, IDC_EPFEFULL, szWindowClass, MAX_LOADSTRING);
	MyRegisterClass(hInstance);

	// Perform application initialization:
	if (!InitInstance(hInstance, nCmdShow))
	{
		return FALSE;
	}

	HACCEL hAccelTable = LoadAccelerators(hInstance, MAKEINTRESOURCE(IDC_EPFEFULL));

	MSG msg;

	// Main message loop:
	while (GetMessage(&msg, nullptr, 0, 0))
	{
		if (!TranslateAccelerator(msg.hwnd, hAccelTable, &msg))
		{
			TranslateMessage(&msg);
			DispatchMessage(&msg);
		}
	}

	return (int)msg.wParam;
}

