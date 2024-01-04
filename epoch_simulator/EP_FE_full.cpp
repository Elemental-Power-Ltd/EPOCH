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

#include "EP/dependencies/json.hpp"
#include "EP/io/FileHandling.hpp"
#include "EP/Optimisation/Optimiser.hpp"


#define MAX_LOADSTRING 100
#define ID_BUTTON0 0
#define ID_BUTTON1 1 
#define ID_BUTTON2 200

#define ID_TEXTBOX2 2
#define ID_TEXTBOX3 3
#define ID_TEXTBOX4 4
#define ID_TEXTBOX5 5
#define ID_TEXTBOX6 6
#define ID_TEXTBOX7 7
#define ID_TEXTBOX8 8
#define ID_TEXTBOX9 9
#define ID_TEXTBOX10 10
#define ID_TEXTBOX11 11 
#define ID_TEXTBOX12 12
#define ID_TEXTBOX13 13
#define ID_TEXTBOX14 14
#define ID_TEXTBOX15 15
#define ID_TEXTBOX16 16
#define ID_TEXTBOX17 17
#define ID_TEXTBOX18 18
#define ID_TEXTBOX19 19
#define ID_TEXTBOX20 20
#define ID_TEXTBOX21 21 
#define ID_TEXTBOX22 22
#define ID_TEXTBOX23 23
#define ID_TEXTBOX24 24
#define ID_TEXTBOX25 25
#define ID_TEXTBOX26 26
#define ID_TEXTBOX27 27
#define ID_TEXTBOX28 28
#define ID_TEXTBOX29 29
#define ID_TEXTBOX30 30
#define ID_TEXTBOX31 31 
#define ID_TEXTBOX32 32
#define ID_TEXTBOX33 33
#define ID_TEXTBOX34 34
#define ID_TEXTBOX35 35
#define ID_TEXTBOX36 36
#define ID_TEXTBOX37 37
#define ID_TEXTBOX38 38
#define ID_TEXTBOX39 39
#define ID_TEXTBOX40 40
#define ID_TEXTBOX41 41 
#define ID_TEXTBOX42 42
#define ID_TEXTBOX43 43
#define ID_TEXTBOX44 44
#define ID_TEXTBOX45 45
#define ID_TEXTBOX46 46
#define ID_TEXTBOX47 47
#define ID_TEXTBOX48 48
#define ID_TEXTBOX49 49
#define ID_TEXTBOX50 50
#define ID_TEXTBOX51 51 
#define ID_TEXTBOX52 52
#define ID_TEXTBOX53 53
#define ID_TEXTBOX54 54
#define ID_TEXTBOX55 55
#define ID_TEXTBOX56 56
#define ID_TEXTBOX57 57
#define ID_TEXTBOX58 58
#define ID_TEXTBOX59 59
#define ID_TEXTBOX60 60
#define ID_TEXTBOX61 61 
#define ID_TEXTBOX62 62
#define ID_TEXTBOX63 63
#define ID_TEXTBOX64 64
#define ID_TEXTBOX65 65
#define ID_TEXTBOX66 66
#define ID_TEXTBOX67 67
#define ID_TEXTBOX68 68
#define ID_TEXTBOX69 69
#define ID_TEXTBOX70 70
#define ID_TEXTBOX71 71
#define ID_TEXTBOX72 72
#define ID_TEXTBOX73 73
#define ID_TEXTBOX74 74
#define ID_TEXTBOX75 75
#define ID_TEXTBOX76 76
#define ID_TEXTBOX77 77
#define ID_TEXTBOX78 78
#define ID_TEXTBOX79 79
#define ID_TEXTBOX71 80
#define ID_TEXTBOX72 81
#define ID_TEXTBOX73 82
#define ID_TEXTBOX74 83
#define ID_TEXTBOX75 84
#define ID_TEXTBOX76 85
#define ID_TEXTBOX77 86
#define ID_TEXTBOX78 87
#define ID_TEXTBOX79 88
#define ID_TEXTBOX80 89
#define ID_TEXTBOX81 90
#define ID_TEXTBOX82 92
#define ID_TEXTBOX83 93
#define ID_TEXTBOX84 94
#define ID_TEXTBOX85 95
#define ID_TEXTBOX86 96
#define ID_TEXTBOX87 97
#define ID_TEXTBOX88 98
#define ID_TEXTBOX89 99

#define ID_TEXTBOX200 200

#define ID_OUTPUT1 99
#define ID_OUTPUT2 100
#define ID_OUTPUT3 101
#define ID_OUTPUT4 102
#define ID_OUTPUT5 103
#define ID_OUTPUT6 104
#define ID_OUTPUT7 105
#define ID_OUTPUT8 106
#define ID_OUTPUT9 107
#define ID_OUTPUT10 108
#define ID_OUTPUT11 109
#define ID_OUTPUT12 110
#define ID_OUTPUT13 111
#define ID_OUTPUT14 112
#define ID_OUTPUT15 113
#define ID_OUTPUT16 114
#define ID_OUTPUT17 115
#define ID_OUTPUT18 116
#define ID_OUTPUT19 117
#define ID_OUTPUT20 118
#define ID_OUTPUT21 119
#define ID_OUTPUT22 120
#define ID_OUTPUT23 121
#define ID_OUTPUT24 122
#define ID_OUTPUT25 123
#define ID_OUTPUT26 124
#define ID_OUTPUT27 125
#define ID_OUTPUT28 126
#define ID_OUTPUT29 127
#define ID_OUTPUT30 128
#define ID_OUTPUT31 129


// Define macros to simplify creating the mapping for each struct member
#define MEMBER_MAPPING_FLOAT(member) {#member, [](const InputValues& s) -> float { return s.member; }, nullptr}
#define MEMBER_MAPPING_INT(member) {#member, nullptr, [](const InputValues& s) -> int { return s.member; }}

// Create an array of MemberMapping for the struct members with a common pattern (using only MEMBER_MAPPING... macros)
MemberMapping memberMappings[] = {
	MEMBER_MAPPING_FLOAT(timestep_minutes), MEMBER_MAPPING_FLOAT(timestep_hours), MEMBER_MAPPING_FLOAT(timewindow),
	MEMBER_MAPPING_FLOAT(Fixed_load1_scalar_lower), MEMBER_MAPPING_FLOAT(Fixed_load1_scalar_upper), MEMBER_MAPPING_FLOAT(Fixed_load1_scalar_step),
	MEMBER_MAPPING_FLOAT(Fixed_load2_scalar_lower), MEMBER_MAPPING_FLOAT(Fixed_load2_scalar_upper), MEMBER_MAPPING_FLOAT(Fixed_load2_scalar_step),
	MEMBER_MAPPING_FLOAT(Flex_load_max_lower), MEMBER_MAPPING_FLOAT(Flex_load_max_upper), MEMBER_MAPPING_FLOAT(Flex_load_max_step),
	MEMBER_MAPPING_FLOAT(Mop_load_max_lower), MEMBER_MAPPING_FLOAT(Mop_load_max_upper), MEMBER_MAPPING_FLOAT(Mop_load_max_step),
	MEMBER_MAPPING_FLOAT(ScalarRG1_lower), MEMBER_MAPPING_FLOAT(ScalarRG1_upper), MEMBER_MAPPING_FLOAT(ScalarRG1_step),
	MEMBER_MAPPING_FLOAT(ScalarRG2_lower), MEMBER_MAPPING_FLOAT(ScalarRG2_upper), MEMBER_MAPPING_FLOAT(ScalarRG2_step),
	MEMBER_MAPPING_FLOAT(ScalarRG3_lower), MEMBER_MAPPING_FLOAT(ScalarRG3_upper), MEMBER_MAPPING_FLOAT(ScalarRG3_step),
	MEMBER_MAPPING_FLOAT(ScalarRG4_lower), MEMBER_MAPPING_FLOAT(ScalarRG4_upper), MEMBER_MAPPING_FLOAT(ScalarRG4_step),
	MEMBER_MAPPING_FLOAT(ScalarHL1_lower), MEMBER_MAPPING_FLOAT(ScalarHL1_upper), MEMBER_MAPPING_FLOAT(ScalarHL1_step),
	MEMBER_MAPPING_FLOAT(ScalarHYield1_lower), MEMBER_MAPPING_FLOAT(ScalarHYield1_upper), MEMBER_MAPPING_FLOAT(ScalarHYield1_step),
	MEMBER_MAPPING_FLOAT(ScalarHYield2_lower), MEMBER_MAPPING_FLOAT(ScalarHYield2_upper), MEMBER_MAPPING_FLOAT(ScalarHYield2_step),
	MEMBER_MAPPING_FLOAT(ScalarHYield3_lower), MEMBER_MAPPING_FLOAT(ScalarHYield3_upper), MEMBER_MAPPING_FLOAT(ScalarHYield3_step),
	MEMBER_MAPPING_FLOAT(ScalarHYield4_lower), MEMBER_MAPPING_FLOAT(ScalarHYield4_upper), MEMBER_MAPPING_FLOAT(ScalarHYield4_step),
	MEMBER_MAPPING_FLOAT(GridImport_lower), MEMBER_MAPPING_FLOAT(GridImport_upper), MEMBER_MAPPING_FLOAT(GridImport_step),
	MEMBER_MAPPING_FLOAT(GridExport_lower), MEMBER_MAPPING_FLOAT(GridExport_upper), MEMBER_MAPPING_FLOAT(GridExport_step),
	MEMBER_MAPPING_FLOAT(Import_headroom_lower), MEMBER_MAPPING_FLOAT(Import_headroom_upper), MEMBER_MAPPING_FLOAT(Import_headroom_step),
	MEMBER_MAPPING_FLOAT(Export_headroom_lower), MEMBER_MAPPING_FLOAT(Export_headroom_upper), MEMBER_MAPPING_FLOAT(Export_headroom_step),
	MEMBER_MAPPING_FLOAT(ESS_charge_power_lower), MEMBER_MAPPING_FLOAT(ESS_charge_power_upper), MEMBER_MAPPING_FLOAT(ESS_charge_power_step),
	MEMBER_MAPPING_FLOAT(ESS_discharge_power_lower), MEMBER_MAPPING_FLOAT(ESS_discharge_power_upper), MEMBER_MAPPING_FLOAT(ESS_discharge_power_step),
	MEMBER_MAPPING_FLOAT(ESS_capacity_lower), MEMBER_MAPPING_FLOAT(ESS_capacity_upper), MEMBER_MAPPING_FLOAT(ESS_capacity_step),
	MEMBER_MAPPING_FLOAT(ESS_RTE_lower), MEMBER_MAPPING_FLOAT(ESS_RTE_upper), MEMBER_MAPPING_FLOAT(ESS_RTE_step),
	MEMBER_MAPPING_FLOAT(ESS_aux_load_lower), MEMBER_MAPPING_FLOAT(ESS_aux_load_upper), MEMBER_MAPPING_FLOAT(ESS_aux_load_step),
	MEMBER_MAPPING_FLOAT(ESS_start_SoC_lower), MEMBER_MAPPING_FLOAT(ESS_start_SoC_upper), MEMBER_MAPPING_FLOAT(ESS_start_SoC_step),
	MEMBER_MAPPING_INT(ESS_charge_mode_lower), MEMBER_MAPPING_INT(ESS_charge_mode_upper),
	MEMBER_MAPPING_INT(ESS_discharge_mode_lower), MEMBER_MAPPING_INT(ESS_discharge_mode_upper),
	MEMBER_MAPPING_FLOAT(import_kWh_price), 
	MEMBER_MAPPING_FLOAT(export_kWh_price),
	MEMBER_MAPPING_FLOAT(time_budget_min), MEMBER_MAPPING_INT(target_max_concurrency),
	MEMBER_MAPPING_FLOAT(CAPEX_limit), MEMBER_MAPPING_FLOAT(OPEX_limit)
};


// Define macros to simplify creating the mapping for each struct member
#define OUT_MEMBER_MAPPING_FLOAT(member) {#member, [](const OutputValues& s) -> float { return s.member; }, nullptr}
#define OUT_MEMBER_MAPPING_INT(member) {#member, nullptr, [](const OutputValues& s) -> int { return s.member; }}

OutMemberMapping OutmemberMappings[] = {
	OUT_MEMBER_MAPPING_FLOAT(maxVal),
	OUT_MEMBER_MAPPING_FLOAT(minVal),
	OUT_MEMBER_MAPPING_FLOAT(meanVal),
	OUT_MEMBER_MAPPING_FLOAT(est_seconds),
	OUT_MEMBER_MAPPING_FLOAT(est_hours),
	OUT_MEMBER_MAPPING_INT(num_scenarios),
	OUT_MEMBER_MAPPING_FLOAT(time_taken),
	OUT_MEMBER_MAPPING_FLOAT(Fixed_load1_scalar), OUT_MEMBER_MAPPING_FLOAT(Fixed_load2_scalar), OUT_MEMBER_MAPPING_FLOAT(Flex_load_max), OUT_MEMBER_MAPPING_FLOAT(Mop_load_max),
	OUT_MEMBER_MAPPING_FLOAT(ScalarRG1), OUT_MEMBER_MAPPING_FLOAT(ScalarRG2), OUT_MEMBER_MAPPING_FLOAT(ScalarRG3), OUT_MEMBER_MAPPING_FLOAT(ScalarRG4),
	OUT_MEMBER_MAPPING_FLOAT(ScalarHL1), OUT_MEMBER_MAPPING_FLOAT(ScalarHYield1), OUT_MEMBER_MAPPING_FLOAT(ScalarHYield2), OUT_MEMBER_MAPPING_FLOAT(ScalarHYield3), OUT_MEMBER_MAPPING_FLOAT(ScalarHYield4),
	OUT_MEMBER_MAPPING_FLOAT(GridImport), OUT_MEMBER_MAPPING_FLOAT(GridExport), OUT_MEMBER_MAPPING_FLOAT(Import_headroom), OUT_MEMBER_MAPPING_FLOAT(Export_headroom),
	OUT_MEMBER_MAPPING_FLOAT(ESS_charge_power), OUT_MEMBER_MAPPING_FLOAT(ESS_discharge_power), OUT_MEMBER_MAPPING_FLOAT(ESS_capacity), OUT_MEMBER_MAPPING_FLOAT(ESS_RTE), OUT_MEMBER_MAPPING_FLOAT(ESS_aux_load), OUT_MEMBER_MAPPING_FLOAT(ESS_start_SoC),
	OUT_MEMBER_MAPPING_INT(ESS_charge_mode), OUT_MEMBER_MAPPING_INT(ESS_discharge_mode),
	OUT_MEMBER_MAPPING_FLOAT(import_kWh_price), OUT_MEMBER_MAPPING_FLOAT(export_kWh_price),
	OUT_MEMBER_MAPPING_FLOAT(CAPEX), OUT_MEMBER_MAPPING_FLOAT(annualised), OUT_MEMBER_MAPPING_FLOAT(scenario_cost_balance), OUT_MEMBER_MAPPING_FLOAT(payback_horizon), OUT_MEMBER_MAPPING_FLOAT(scenario_carbon_balance),
	OUT_MEMBER_MAPPING_INT(CAPEX_index), OUT_MEMBER_MAPPING_INT(annualised_index), OUT_MEMBER_MAPPING_INT(scenario_cost_balance_index), OUT_MEMBER_MAPPING_INT(payback_horizon_index), OUT_MEMBER_MAPPING_INT(scenario_carbon_balance_index),
	OUT_MEMBER_MAPPING_INT(scenario_index),
	OUT_MEMBER_MAPPING_INT(num_scenarios), OUT_MEMBER_MAPPING_FLOAT(est_hours), OUT_MEMBER_MAPPING_FLOAT(est_seconds)
};

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




//Visual Form based stuff
// Global Variables:
HINSTANCE hInst;                                // current instance
WCHAR szTitle[MAX_LOADSTRING];                  // The title bar text
WCHAR szWindowClass[MAX_LOADSTRING];            // the main window class name

// Forward declarations of functions included in this code module:
ATOM                MyRegisterClass(HINSTANCE hInstance);
BOOL                InitInstance(HINSTANCE, int);
LRESULT CALLBACK    WndProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK    About(HWND, UINT, WPARAM, LPARAM);

// window scrolling:
//SCROLLINFO si = { 0 };
//si.cbSize = sizeof(si);
//si.fMask = SIF_RANGE | SIF_PAGE;
//si.nMin = 0;
//si.nMax = 100;
//si.nPage = 10;

HWND hTextbox1; HWND hTextbox2; HWND hTextbox3; HWND hTextbox4; HWND hTextbox5; HWND hTextbox6; HWND hTextbox7; HWND hTextbox8; HWND hTextbox9; HWND hTextbox10;
HWND hTextbox11; HWND hTextbox12; HWND hTextbox13; HWND hTextbox14; HWND hTextbox15; HWND hTextbox16; HWND hTextbox17; HWND hTextbox18; HWND hTextbox19; HWND hTextbox20;
HWND hTextbox21; HWND hTextbox22; HWND hTextbox23; HWND hTextbox24; HWND hTextbox25; HWND hTextbox26; HWND hTextbox27; HWND hTextbox28; HWND hTextbox29; HWND hTextbox30;
HWND hTextbox31; HWND hTextbox32; HWND hTextbox33; HWND hTextbox34; HWND hTextbox35; HWND hTextbox36; HWND hTextbox37; HWND hTextbox38; HWND hTextbox39; HWND hTextbox40;
HWND hTextbox41; HWND hTextbox42; HWND hTextbox43; HWND hTextbox44; HWND hTextbox45; HWND hTextbox46; HWND hTextbox47; HWND hTextbox48; HWND hTextbox49; HWND hTextbox50;
HWND hTextbox51; HWND hTextbox52; HWND hTextbox53; HWND hTextbox54; HWND hTextbox55; HWND hTextbox56; HWND hTextbox57; HWND hTextbox58; HWND hTextbox59; HWND hTextbox60;
HWND hTextbox61; HWND hTextbox62; HWND hTextbox63; HWND hTextbox64; HWND hTextbox65; HWND hTextbox66; HWND hTextbox67; HWND hTextbox68; HWND hTextbox69; HWND hTextbox70;
HWND hTextbox71; HWND hTextbox72; HWND hTextbox73; HWND hTextbox74; HWND hTextbox75; HWND hTextbox76; HWND hTextbox77; HWND hTextbox78; HWND hTextbox79; HWND hTextbox80;
HWND hTextbox81; HWND hTextbox82; HWND hTextbox83; HWND hTextbox84; HWND hTextbox85; HWND hTextbox86; HWND hTextbox87; HWND hTextbox88; HWND hTextbox89;

HWND hTextbox200;

HWND hOutput1; HWND hOutput2; HWND hOutput3; HWND hOutput4; HWND hOutput5; HWND hOutput6; HWND hOutput7; HWND hOutput8; HWND hOutput9; HWND hOutput10;
HWND hOutput11; HWND hOutput12; HWND hOutput13; HWND hOutput14; HWND hOutput15; HWND hOutput16; HWND hOutput17; HWND hOutput18; HWND hOutput19; HWND hOutput20;
HWND hOutput21; HWND hOutput22; HWND hOutput23; HWND hOutput24; HWND hOutput25; HWND hOutput26; HWND hOutput27; HWND hOutput28; HWND hOutput29; HWND hOutput30;
HWND hOutput31; HWND hOutput32; HWND hOutput33; HWND hOutput34; HWND hOutput35; HWND hOutput36;
	

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
    if (!InitInstance (hInstance, nCmdShow))
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

    return (int) msg.wParam;
}



//
//  FUNCTION: MyRegisterClass()
//
//  PURPOSE: Registers the window class.
//
ATOM MyRegisterClass(HINSTANCE hInstance)
{
    WNDCLASSEXW wcex;

    wcex.cbSize = sizeof(WNDCLASSEX);

    wcex.style          = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc    = WndProc;
    wcex.cbClsExtra     = 0;
    wcex.cbWndExtra     = 0;
    wcex.hInstance      = hInstance;
    wcex.hIcon          = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_EPFEFULL));
    wcex.hCursor        = LoadCursor(nullptr, IDC_ARROW);
    wcex.hbrBackground  = (HBRUSH)(COLOR_WINDOW+1);
    wcex.lpszMenuName   = MAKEINTRESOURCEW(IDC_EPFEFULL);
    wcex.lpszClassName  = szWindowClass;
    wcex.hIconSm        = LoadIcon(wcex.hInstance, MAKEINTRESOURCE(IDI_SMALL));

    return RegisterClassExW(&wcex);
}

//
//   FUNCTION: InitInstance(HINSTANCE, int)
//
//   PURPOSE: Saves instance handle and creates main window
//
//   COMMENTS:
//
//        In this function, we save the instance handle in a global variable and
//        create and display the main program window.
//

BOOL InitConsole()
{
	if (!AllocConsole()) {
		return FALSE;
	}

	FILE* pCout;
	freopen_s(&pCout, "CONOUT$", "w", stdout);

	//std::cout << "Console initialized!\n";

	return TRUE;
}

BOOL CloseConsole() {
	// Close the standard output stream
	fclose(stdout);

	// Detach and destroy the console
	if (!FreeConsole()) {
		return FALSE;
	}

	//std::cout << "Console closed!\n"; // This won't be shown in the console

	return TRUE;
}


BOOL InitInstance(HINSTANCE hInstance, int nCmdShow)
{
   hInst = hInstance; // Store instance handle in our global variable

   DWORD windowStyle = WS_OVERLAPPEDWINDOW | WS_HSCROLL | WS_VSCROLL;

   HWND hWnd = CreateWindowW(szWindowClass, 
	   szTitle, 
	   windowStyle, CW_USEDEFAULT, 0,
	   2500, //width
	   2000, // height
	   nullptr, nullptr, hInstance, nullptr);

   HWND hButton0 = CreateWindow(
	   L"BUTTON",  // Predefined class; Unicode assumed.
	   L"INITIALISE",      // Button text.
	   WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,  // Styles.
	   10,         // x position.
	   10,         // y position.
	   100,        // Button width.
	   30,         // Button height.
	   hWnd,       // Parent window.
	   (HMENU)ID_BUTTON0,       // No menu.
	   (HINSTANCE)GetWindowLongPtr(hWnd, GWLP_HINSTANCE),
	   NULL);      // Pointer not needed.
   // ... add more textboxes as needed

   HWND hButton1 = CreateWindow(
       L"BUTTON",  // Predefined class; Unicode assumed.
       L"RUN",      // Button text.
       WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,  // Styles.
       10,         // x position.
       80,         // y position.
       100,        // Button width.
       30,         // Button height.
       hWnd,       // Parent window.
       (HMENU)ID_BUTTON1,       // No menu.
       (HINSTANCE)GetWindowLongPtr(hWnd, GWLP_HINSTANCE),
       NULL);      // Pointer not needed.
  
   HWND hButton2 = CreateWindow(
	   L"BUTTON",  // Predefined class; Unicode assumed.
	   L"RECALL",      // Button text.
	   WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,  // Styles.
	   10,         // x position.
	   150,         // y position.
	   100,        // Button width.
	   30,         // Button height.
	   hWnd,       // Parent window.
	   (HMENU)ID_BUTTON2,       // No menu.
	   (HINSTANCE)GetWindowLongPtr(hWnd, GWLP_HINSTANCE),
	   NULL);      // Pointer not needed.

   HWND hLabelout18 = CreateWindowW(
	   L"STATIC",
	   L"INDEX",
	   WS_VISIBLE | WS_CHILD,
	   10,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   30,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox200 = CreateWindowW(
	   L"EDIT",
	   L"",  // initial text
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
	   10,   // x position
	   210,  // y position
	   100,  // width
	   30,   // height
	   hWnd,
	   (HMENU)ID_TEXTBOX200,
	   hInstance,
	   NULL);


   // ... add more textboxes as needed
   
   HWND hLabel00 = CreateWindowW(
	   L"STATIC",
	   L"ESTIMATED TIME",
	   WS_VISIBLE | WS_CHILD,
	   120,         // x position.
	   10,         // y position.
	   100,       //width
	   50,		//height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   HWND hLabel1 = CreateWindowW(
	   L"STATIC",
	   L"# Scenarios",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   10,  // y position (above the text box)
	   100, // width
	   20,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   //hTextbox1 = CreateWindowW(  now used for output box in initialsise
	  // L"EDIT",
	  // L"",  // Enter default value
	  // WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	  // 240,
	  // 30,
	  // 100,
	  // 30,
	  // hWnd,
	  // (HMENU)ID_TEXTBOX2,  // ID for the textbox
	  // hInstance,
	  // NULL);  

   HWND hLabel2 = CreateWindowW(
	   L"STATIC",
	   L"Hours",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   10,  // y position (above the text box)
	   100, // width
	   20,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   //hTextbox2 = CreateWindowW(
	  // L"EDIT",
	  // L"",  // No text initially.
	  // WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	  // 360,
	  // 30,
	  // 100,
	  // 30,
	  // hWnd,
	  // (HMENU)ID_TEXTBOX3,  // ID for the textbox
	  // hInstance,
	  // NULL);

   HWND hLabel3 = CreateWindowW(
	   L"STATIC",
	   L"Seconds",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   10,  // y position (above the text box)
	   100, // width
	   20,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   //hTextbox3 = CreateWindowW(
	  // L"EDIT",
	  // L"",  // No text initially.
	  // WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	  // 480,
	  // 30,
	  // 100,
	  // 30,
	  // hWnd,
	  // (HMENU)ID_TEXTBOX3,  // ID for the textbox
	  // hInstance,
	  // NULL);


   HWND hLabel0 = CreateWindowW(
	   L"STATIC",
	   L"INPUTS (overwrite default values)",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   80,  // y position (above the text box)
	   100, // width
	   80,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

  

   HWND hLabel4 = CreateWindowW(
	   L"STATIC",
	   L"Timestep, Minutes",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   80,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox4 = CreateWindowW(
	   L"EDIT",
	   L"60",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   130,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX4,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel5 = CreateWindowW(
	   L"STATIC",
	   L"Timestep, Hours",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   80,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox5 = CreateWindowW(
	   L"EDIT",
	   L"1",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   130,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX5,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel6 = CreateWindowW(
	   L"STATIC",
	   L"Time window, hours",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   80,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox6 = CreateWindowW(
	   L"EDIT",
	   L"8760",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   130,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX6,  // ID for the textbox
	   hInstance,
	   NULL);
  
   // new button row 

   HWND hLabel7 = CreateWindowW(
	   L"STATIC",
	   L"Fixed load1 scalar lower",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox7 = CreateWindowW(
	   L"EDIT",
	   L"1",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX7,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel8 = CreateWindowW(
	   L"STATIC",
	   L"Fixed load1 scalar upper",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox8 = CreateWindowW(
	   L"EDIT",
	   L"1",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX8,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel9 = CreateWindowW(
	   L"STATIC",
	   L"Fixed load1 scalar step",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox9 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX9,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel10 = CreateWindowW(
	   L"STATIC",
	   L"Fixed load2 scalar lower",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox10 = CreateWindowW(
	   L"EDIT",
	   L"3",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX10,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel11 = CreateWindowW(
	   L"STATIC",
	   L"Fixed load2 scalar upper",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox11 = CreateWindowW(
	   L"EDIT",
	   L"3",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX11,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel12 = CreateWindowW(
	   L"STATIC",
	   L"Fixed load2 scalar step",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox12 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX12,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel13 = CreateWindowW(
	   L"STATIC",
	   L"Flex max lower",
	   WS_VISIBLE | WS_CHILD,
	   840,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox13 = CreateWindowW(
	   L"EDIT",
	   L"50.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   840,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX13,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel14 = CreateWindowW(
	   L"STATIC",
	   L"Flex max lower upper",
	   WS_VISIBLE | WS_CHILD,
	   960,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox14 = CreateWindowW(
	   L"EDIT",
	   L"50.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   960,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX14,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel15 = CreateWindowW(
	   L"STATIC",
	   L"Flex max lower step",
	   WS_VISIBLE | WS_CHILD,
	   1080,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox15 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1080,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX15,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel16 = CreateWindowW(
	   L"STATIC",
	   L"Mop load max lower",
	   WS_VISIBLE | WS_CHILD,
	   1200,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox16 = CreateWindowW(
	   L"EDIT",
	   L"300.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1200,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX16,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel17 = CreateWindowW(
	   L"STATIC",
	   L"Mop load max upper",
	   WS_VISIBLE | WS_CHILD,
	   1320,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox17 = CreateWindowW(
	   L"EDIT",
	   L"300.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1320,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX17,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel18 = CreateWindowW(
	   L"STATIC",
	   L"Mop load max step",
	   WS_VISIBLE | WS_CHILD,
	   1440,  // x position
	   180,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox18 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1440,
	   230,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX18,  // ID for the textbox
	   hInstance,
	   NULL);

   // new GUI row 

   HWND hLabel19 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG1 lower",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox19 = CreateWindowW(
	   L"EDIT",
	   L"599.2",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX19,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel20 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG1 upper",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox20 = CreateWindowW(
	   L"EDIT",
	   L"599.2",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX20,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel21 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG1 step",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox21 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX21,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel22 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG2 lower",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox22 = CreateWindowW(
	   L"EDIT",
	   L"75.6",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX22,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel23 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG2 upper",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox23 = CreateWindowW(
	   L"EDIT",
	   L"75.6",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX23,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel24 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG2 step",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox24 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX24,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel25 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG3 lower",
	   WS_VISIBLE | WS_CHILD,
	   840,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox25 = CreateWindowW(
	   L"EDIT",
	   L"60.48",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   840,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX25,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel26 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG3 upper",
	   WS_VISIBLE | WS_CHILD,
	   960,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox26 = CreateWindowW(
	   L"EDIT",
	   L"60.48",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   960,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX26,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel27 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG3 step",
	   WS_VISIBLE | WS_CHILD,
	   1080,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox27 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1080,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX27,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel28 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG4 lower",
	   WS_VISIBLE | WS_CHILD,
	   1200,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox28 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1200,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX28,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel29 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG4 upper",
	   WS_VISIBLE | WS_CHILD,
	   1320,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox29 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1320,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX29,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel30 = CreateWindowW(
	   L"STATIC",
	   L"Scalar RG4 step",
	   WS_VISIBLE | WS_CHILD,
	   1440,  // x position
	   280,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox30 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1440,
	   330,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX30,  // ID for the textbox
	   hInstance,
	   NULL);

   // New GUI row

   HWND hLabel31 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HL1 lower",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox31 = CreateWindowW(
	   L"EDIT",
	   L"1.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX31,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel32 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HL1 upper",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox32 = CreateWindowW(
	   L"EDIT",
	   L"1.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX32,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel33 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HL1 step",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox33 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX33,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel34 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield1 lower",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox34 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX34,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel35 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield1 upper",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox35 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX35,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel36 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield1 step",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox36 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX36,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel37 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield2 lower",
	   WS_VISIBLE | WS_CHILD,
	   840,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox37 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   840,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX37,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel38 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield2 upper",
	   WS_VISIBLE | WS_CHILD,
	   960,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox38 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   960,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX38,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel39 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield2 step",
	   WS_VISIBLE | WS_CHILD,
	   1080,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox39 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1080,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX39,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel40 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield3 lower",
	   WS_VISIBLE | WS_CHILD,
	   1200,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox40 = CreateWindowW(
	   L"EDIT",
	   L"0.75",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1200,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX40,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel41 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield3 upper",
	   WS_VISIBLE | WS_CHILD,
	   1320,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox41 = CreateWindowW(
	   L"EDIT",
	   L"0.75",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1320,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX41,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel42 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield3 step",
	   WS_VISIBLE | WS_CHILD,
	   1440,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox42 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1440,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX42,  // ID for the textbox
	   hInstance,
	   NULL);


   HWND hLabel43 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield4 lower",
	   WS_VISIBLE | WS_CHILD,
	   1560,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox43 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1560,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX43,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel44 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield4 upper",
	   WS_VISIBLE | WS_CHILD,
	   1680,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox44 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1680,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX44,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel45 = CreateWindowW(
	   L"STATIC",
	   L"Scalar HYield4 step",
	   WS_VISIBLE | WS_CHILD,
	   1800,  // x position
	   380,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox45 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1800,
	   430,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX45,  // ID for the textbox
	   hInstance,
	   NULL);


   HWND hLabel46 = CreateWindowW(
	   L"STATIC",
	   L"Grid import lower",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox46 = CreateWindowW(
	   L"EDIT",
	   L"98.29",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX46,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel47 = CreateWindowW(
	   L"STATIC",
	   L"Grid import upper",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox47 = CreateWindowW(
	   L"EDIT",
	   L"98.29",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX47,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel48 = CreateWindowW(
	   L"STATIC",
	   L"Grid import step",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox48 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX48,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel49 = CreateWindowW(
	   L"STATIC",
	   L"Grid export lower",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox49 = CreateWindowW(
	   L"EDIT",
	   L"95.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX49,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel50 = CreateWindowW(
	   L"STATIC",
	   L"Grid export upper",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox50 = CreateWindowW(
	   L"EDIT",
	   L"95.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX50,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel51 = CreateWindowW(
	   L"STATIC",
	   L"Grid export step",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox51 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX51,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel52 = CreateWindowW(
	   L"STATIC",
	   L"Import headroom lower",
	   WS_VISIBLE | WS_CHILD,
	   840,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox52 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   840,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX52,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel53 = CreateWindowW(
	   L"STATIC",
	   L"Import headroom upper",
	   WS_VISIBLE | WS_CHILD,
	   960,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox53 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   960,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX53,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel54 = CreateWindowW(
	   L"STATIC",
	   L"Import headroom step",
	   WS_VISIBLE | WS_CHILD,
	   1080,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox54 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1080,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX54,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel55 = CreateWindowW(
	   L"STATIC",
	   L"Export headroom lower",
	   WS_VISIBLE | WS_CHILD,
	   1200,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox55 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1200,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX55,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel56 = CreateWindowW(
	   L"STATIC",
	   L"Export headroom upper",
	   WS_VISIBLE | WS_CHILD,
	   1320,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox56 = CreateWindowW(
	   L"EDIT",
	   L"0.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1320,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX56,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel57 = CreateWindowW(
	   L"STATIC",
	   L"Export headroom step",
	   WS_VISIBLE | WS_CHILD,
	   1440,  // x position
	   480,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox57 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1440,
	   530,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX57,  // ID for the textbox
	   hInstance,
	   NULL);


   HWND hLabel58 = CreateWindowW(
	   L"STATIC",
	   L"ESS charge power lower",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox58 = CreateWindowW(
	   L"EDIT",
	   L"300.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX58,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel59 = CreateWindowW(
	   L"STATIC",
	   L"ESS charge power upper",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox59 = CreateWindowW(
	   L"EDIT",
	   L"600.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX59,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel60 = CreateWindowW(
	   L"STATIC",
	   L"ESS charge power step",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox60 = CreateWindowW(
	   L"EDIT",
	   L"300.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX60,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel61 = CreateWindowW(
	   L"STATIC",
	   L"ESS discharge power lower",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox61 = CreateWindowW(
	   L"EDIT",
	   L"300.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX61,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel62 = CreateWindowW(
	   L"STATIC",
	   L"ESS discharge power upper",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox62 = CreateWindowW(
	   L"EDIT",
	   L"600.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX62,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel63 = CreateWindowW(
	   L"STATIC",
	   L"ESS discharge power step",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox63 = CreateWindowW(
	   L"EDIT",
	   L"300.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX63,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel64 = CreateWindowW(
	   L"STATIC",
	   L"ESS capacity lower",
	   WS_VISIBLE | WS_CHILD,
	   840,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox64 = CreateWindowW(
	   L"EDIT",
	   L"800.0",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   840,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX64,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel65 = CreateWindowW(
	   L"STATIC",
	   L"ESS capacity upper",
	   WS_VISIBLE | WS_CHILD,
	   960,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox65 = CreateWindowW(
	   L"EDIT",
	   L"900.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   960,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX65,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel66 = CreateWindowW(
	   L"STATIC",
	   L"ESS capacity step",
	   WS_VISIBLE | WS_CHILD,
	   1080,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox66 = CreateWindowW(
	   L"EDIT",
	   L"20",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1080,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX66,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel67 = CreateWindowW(
	   L"STATIC",
	   L"ESS RTE lower",
	   WS_VISIBLE | WS_CHILD,
	   1200,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);


   hTextbox67 = CreateWindowW(
	   L"EDIT",
	   L"0.86",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1200,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX16,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel68 = CreateWindowW(
	   L"STATIC",
	   L"ESS RTE upper",
	   WS_VISIBLE | WS_CHILD,
	   1320,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox68 = CreateWindowW(
	   L"EDIT",
	   L"0.86",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1320,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX68,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel69 = CreateWindowW(
	   L"STATIC",
	   L"ESS RTE step",
	   WS_VISIBLE | WS_CHILD,
	   1440,  // x position
	   580,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox69 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1440,
	   630,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX69,  // ID for the textbox
	   hInstance,
	   NULL);

   // new GUI row 

   HWND hLabel70 = CreateWindowW(
	   L"STATIC",
	   L"ESS aux load lower",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox70 = CreateWindowW(
	   L"EDIT",
	   L"0.75",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX70,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel71 = CreateWindowW(
	   L"STATIC",
	   L"ESS aux load upper",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox71 = CreateWindowW(
	   L"EDIT",
	   L"0.75",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX71,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel72 = CreateWindowW(
	   L"STATIC",
	   L"ESS aux load step",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox72 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX72,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel73= CreateWindowW(
	   L"STATIC",
	   L"ESS start SoC lower",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox73 = CreateWindowW(
	   L"EDIT",
	   L"0.5",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX73,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel74 = CreateWindowW(
	   L"STATIC",
	   L"ESS start SoC Upper",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox74 = CreateWindowW(
	   L"EDIT",
	   L"0.5",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX74,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel75 = CreateWindowW(
	   L"STATIC",
	   L"ESS start SoC step",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox75 = CreateWindowW(
	   L"EDIT",
	   L"0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX75,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel76 = CreateWindowW(
	   L"STATIC",
	   L"ESS charge mode lower",
	   WS_VISIBLE | WS_CHILD,
	   840,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox76 = CreateWindowW(
	   L"EDIT",
	   L"1",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   840,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX76,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel77 = CreateWindowW(
	   L"STATIC",
	   L"ESS charge mode upper",
	   WS_VISIBLE | WS_CHILD,
	   960,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox77 = CreateWindowW(
	   L"EDIT",
	   L"1",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   960,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX77,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel78 = CreateWindowW(
	   L"STATIC",
	   L"ESS discharge mode lower",
	   WS_VISIBLE | WS_CHILD,
	   1080,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox78 = CreateWindowW(
	   L"EDIT",
	   L"1",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1080,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX78,  // ID for the textbox
	   hInstance,
	   NULL);
   
   HWND hLabel79 = CreateWindowW(
	   L"STATIC",
	   L"ESS discharge mode upper",
	   WS_VISIBLE | WS_CHILD,
	   1200,  // x position
	   680,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox79= CreateWindowW(
	   L"EDIT",
	   L"1",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   1200,
	   730,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX79,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel80 = CreateWindowW(
	   L"STATIC",
	   L"Import Price p/kWh",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   780,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox80 = CreateWindowW(
	   L"EDIT",
	   L"30",  // Enter default value
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   120,
	   830,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX80,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel81 = CreateWindowW(
	   L"STATIC",
	   L"Export Price p/kWh",
	   WS_VISIBLE | WS_CHILD,
	   240,  // x position
	   780,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox81 = CreateWindowW(
	   L"EDIT",
	   L"5",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   240,
	   830,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX81,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel82 = CreateWindowW(
	   L"STATIC",
	   L"Time budget, minutes",
	   WS_VISIBLE | WS_CHILD,
	   360,  // x position
	   780,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox82 = CreateWindowW(
	   L"EDIT",
	   L"1.0",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   360,
	   830,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX85,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel83 = CreateWindowW(
	   L"STATIC",
	   L"Target Max Concurrency",
	   WS_VISIBLE | WS_CHILD,
	   480,  // x position
	   780,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox83 = CreateWindowW(
	   L"EDIT",
	   L"44",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   480,
	   830,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX86,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel84 = CreateWindowW(
	   L"STATIC",
	   L"CAPEX limit, £k",
	   WS_VISIBLE | WS_CHILD,
	   600,  // x position
	   780,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox84 = CreateWindowW(
	   L"EDIT",
	   L"500",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   600,
	   830,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX87,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabel85 = CreateWindowW(
	   L"STATIC",
	   L"OPEX limit, £k",
	   WS_VISIBLE | WS_CHILD,
	   720,  // x position
	   780,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   hTextbox85 = CreateWindowW(
	   L"EDIT",
	   L"20",  // No text initially.
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
	   720,
	   830,
	   100,
	   30,
	   hWnd,
	   (HMENU)ID_TEXTBOX88,  // ID for the textbox
	   hInstance,
	   NULL);

   HWND hLabelout0 = CreateWindowW(
	   L"STATIC",
	   L"OUTPUTS",
	   WS_VISIBLE | WS_CHILD,
	   10,  // x position
	   890,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

   HWND hLabelout1 = CreateWindowW(
	   L"STATIC",
	   L"Scenario Max Time, s",
	   WS_VISIBLE | WS_CHILD,
	   120,  // x position
	   890,  // y position (above the text box)
	   100, // width
	   50,  // height
	   hWnd,
	   NULL,
	   hInstance,
	   NULL);

    hOutput1 = CreateWindowW(
	   L"EDIT",
	   L"",  // initial text
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
	   120,   // x position
	   950,  // y position
	   100,  // width
	   30,   // height
	   hWnd,
	   (HMENU)ID_OUTPUT1,
	   hInstance,
	   NULL);

	HWND hLabelout2 = CreateWindowW(
		L"STATIC",
		L"Scenario Min Time, s",
		WS_VISIBLE | WS_CHILD,
		240,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

    hOutput2 = CreateWindowW(
	   L"EDIT",
	   L"",  // initial text
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
	   240,  // x position
	   950,  // y position
	   100,  // width
	   30,   // height
	   hWnd,
	   (HMENU)ID_OUTPUT2,
	   hInstance,
	   NULL);

	HWND hLabelout3 = CreateWindowW(
		L"STATIC",
		L"Scenario Mean Time, s",
		WS_VISIBLE | WS_CHILD,
		360,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput3 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		360,  // x position
		950,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT3,
		hInstance,
		NULL);

	HWND hLabelout4 = CreateWindowW(
		L"STATIC",
		L"Total time taken, s",
		WS_VISIBLE | WS_CHILD,
		480,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

    hOutput4 = CreateWindowW(
	   L"EDIT",
	   L"",  // initial text
	   WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
	   480,  // x position
	   950,  // y position
	   100,  // width
	   30,   // height
	   hWnd,
	   (HMENU)ID_OUTPUT4,
	   hInstance,
	   NULL);

	HWND hLabelout5 = CreateWindowW(
		L"STATIC",
		L"CAPEX, £",
		WS_VISIBLE | WS_CHILD,
		600,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput5 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		600,   // x position
		950,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT5,
		hInstance,
		NULL);

	HWND hLabelout6 = CreateWindowW(
		L"STATIC",
		L"Annualised, £",
		WS_VISIBLE | WS_CHILD,
		720,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput6 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		720,  // x position
		950,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT6,
		hInstance,
		NULL);

	HWND hLabelout7 = CreateWindowW(
		L"STATIC",
		L"Cost balance, £",
		WS_VISIBLE | WS_CHILD,
		840,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput7 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		840,  // x position
		950,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT7,
		hInstance,
		NULL);


	HWND hLabelout8 = CreateWindowW(
		L"STATIC",
		L"Breakeven years",
		WS_VISIBLE | WS_CHILD,
		960,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput8 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		960,  // x position
		950,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT8,
		hInstance,
		NULL);

	HWND hLabelout9 = CreateWindowW(
		L"STATIC",
		L"Carbon balance, kgC02e",
		WS_VISIBLE | WS_CHILD,
		1080,  // x position
		890,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput9 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		1080,  // x position
		950,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT9,
		hInstance,
		NULL);


	hOutput10 = CreateWindowW(
		L"EDIT",
		L"",  // Enter default value
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
		240,
		30,
		100,
		30,
		hWnd,
		(HMENU)ID_OUTPUT10,  // ID for the textbox
		hInstance,
		NULL);

	hOutput11 = CreateWindowW(
		L"EDIT",
		L"",  // No text initially.
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT,
		360,
		30,
		100,
		30,
		hWnd,
		(HMENU)ID_OUTPUT11,  // ID for the textbox
		hInstance,
		NULL);

	hOutput12 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		480,
		30,
		100,
		30,
		hWnd,
		(HMENU)ID_OUTPUT12,
		hInstance,
		NULL);

	HWND hLabelout13 = CreateWindowW(
		L"STATIC",
		L"INDEX",
		WS_VISIBLE | WS_CHILD,
		480,  // x position
		1010,  // y position (above the text box)
		100, // width
		50,  // height
		hWnd,
		NULL,
		hInstance,
		NULL);

	hOutput13 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		600,   // x position
		1010,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT13,
		hInstance,
		NULL);

	hOutput14 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		720,  // x position
		1010,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT14,
		hInstance,
		NULL);

	hOutput15= CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		840,  // x position
		1010,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT15,
		hInstance,
		NULL);

	hOutput16 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		960,  // x position
		1010,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT16,
		hInstance,
		NULL);

	hOutput17 = CreateWindowW(
		L"EDIT",
		L"",  // initial text
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		1080,  // x position
		1010,  // y position
		100,  // width
		30,   // height
		hWnd,
		(HMENU)ID_OUTPUT17,
		hInstance,
		NULL);


   // ... add more textboxes as needed

   if (!hWnd)
   {
      return FALSE;
   }

   ShowWindow(hWnd, nCmdShow);
   UpdateWindow(hWnd);

   return TRUE;
}

//handle scrolling

InputValues readInputFromForm() {

	wchar_t buffer1[100];
	wchar_t buffer2[100];
	wchar_t buffer3[100];
	wchar_t buffer4[100];
	wchar_t buffer5[100];
	wchar_t buffer6[100];
	wchar_t buffer7[100];
	wchar_t buffer8[100];
	wchar_t buffer9[100];
	wchar_t buffer10[100];
	wchar_t buffer11[100];
	wchar_t buffer12[100];
	wchar_t buffer13[100];
	wchar_t buffer14[100];
	wchar_t buffer15[100];
	wchar_t buffer16[100];
	wchar_t buffer17[100];
	wchar_t buffer18[100];
	wchar_t buffer19[100];
	wchar_t buffer20[100];
	wchar_t buffer21[100];
	wchar_t buffer22[100];
	wchar_t buffer23[100];
	wchar_t buffer24[100];
	wchar_t buffer25[100];
	wchar_t buffer26[100];
	wchar_t buffer27[100];
	wchar_t buffer28[100];
	wchar_t buffer29[100];
	wchar_t buffer30[100];
	wchar_t buffer31[100];
	wchar_t buffer32[100];
	wchar_t buffer33[100];
	wchar_t buffer34[100];
	wchar_t buffer35[100];
	wchar_t buffer36[100];
	wchar_t buffer37[100];
	wchar_t buffer38[100];
	wchar_t buffer39[100];
	wchar_t buffer40[100];
	wchar_t buffer41[100];
	wchar_t buffer42[100];
	wchar_t buffer43[100];
	wchar_t buffer44[100];
	wchar_t buffer45[100];
	wchar_t buffer46[100];
	wchar_t buffer47[100];
	wchar_t buffer48[100];
	wchar_t buffer49[100];
	wchar_t buffer50[100];
	wchar_t buffer51[100];
	wchar_t buffer52[100];
	wchar_t buffer53[100];
	wchar_t buffer54[100];
	wchar_t buffer55[100];
	wchar_t buffer56[100];
	wchar_t buffer57[100];
	wchar_t buffer58[100];
	wchar_t buffer59[100];
	wchar_t buffer60[100];
	wchar_t buffer61[100];
	wchar_t buffer62[100];
	wchar_t buffer63[100];
	wchar_t buffer64[100];
	wchar_t buffer65[100];
	wchar_t buffer66[100];
	wchar_t buffer67[100];
	wchar_t buffer68[100];
	wchar_t buffer69[100];
	wchar_t buffer70[100];
	wchar_t buffer71[100];
	wchar_t buffer72[100];
	wchar_t buffer73[100];
	wchar_t buffer74[100];
	wchar_t buffer75[100];
	wchar_t buffer76[100];
	wchar_t buffer77[100];
	wchar_t buffer78[100];
	wchar_t buffer79[100];
	wchar_t buffer80[100];
	wchar_t buffer81[100];
	wchar_t buffer82[100];
	wchar_t buffer83[100];
	wchar_t buffer84[100];
	wchar_t buffer85[100];

	GetWindowText(hTextbox1, buffer1, 100);
	GetWindowText(hTextbox2, buffer2, 100);
	GetWindowText(hTextbox3, buffer3, 100);
	GetWindowText(hTextbox4, buffer4, 100);
	GetWindowText(hTextbox5, buffer5, 100);
	GetWindowText(hTextbox6, buffer6, 100);
	GetWindowText(hTextbox7, buffer7, 100);
	GetWindowText(hTextbox8, buffer8, 100);
	GetWindowText(hTextbox9, buffer9, 100);
	GetWindowText(hTextbox10, buffer10, 100);
	GetWindowText(hTextbox11, buffer11, 100);
	GetWindowText(hTextbox12, buffer12, 100);
	GetWindowText(hTextbox13, buffer13, 100);
	GetWindowText(hTextbox14, buffer14, 100);
	GetWindowText(hTextbox15, buffer15, 100);
	GetWindowText(hTextbox16, buffer16, 100);
	GetWindowText(hTextbox17, buffer17, 100);
	GetWindowText(hTextbox18, buffer18, 100);
	GetWindowText(hTextbox19, buffer19, 100);
	GetWindowText(hTextbox20, buffer20, 100);
	GetWindowText(hTextbox21, buffer21, 100);
	GetWindowText(hTextbox22, buffer22, 100);
	GetWindowText(hTextbox23, buffer23, 100);
	GetWindowText(hTextbox24, buffer24, 100);
	GetWindowText(hTextbox25, buffer25, 100);
	GetWindowText(hTextbox26, buffer26, 100);
	GetWindowText(hTextbox27, buffer27, 100);
	GetWindowText(hTextbox28, buffer28, 100);
	GetWindowText(hTextbox29, buffer29, 100);
	GetWindowText(hTextbox30, buffer30, 100);
	GetWindowText(hTextbox31, buffer31, 100);
	GetWindowText(hTextbox32, buffer32, 100);
	GetWindowText(hTextbox33, buffer33, 100);
	GetWindowText(hTextbox34, buffer34, 100);
	GetWindowText(hTextbox35, buffer35, 100);
	GetWindowText(hTextbox36, buffer36, 100);
	GetWindowText(hTextbox37, buffer37, 100);
	GetWindowText(hTextbox38, buffer38, 100);
	GetWindowText(hTextbox39, buffer39, 100);
	GetWindowText(hTextbox40, buffer40, 100);
	GetWindowText(hTextbox41, buffer41, 100);
	GetWindowText(hTextbox42, buffer42, 100);
	GetWindowText(hTextbox43, buffer43, 100);
	GetWindowText(hTextbox44, buffer44, 100);
	GetWindowText(hTextbox45, buffer45, 100);
	GetWindowText(hTextbox46, buffer46, 100);
	GetWindowText(hTextbox47, buffer47, 100);
	GetWindowText(hTextbox48, buffer48, 100);
	GetWindowText(hTextbox49, buffer49, 100);
	GetWindowText(hTextbox50, buffer50, 100);
	GetWindowText(hTextbox51, buffer51, 100);
	GetWindowText(hTextbox52, buffer52, 100);
	GetWindowText(hTextbox53, buffer53, 100);
	GetWindowText(hTextbox54, buffer54, 100);
	GetWindowText(hTextbox55, buffer55, 100);
	GetWindowText(hTextbox56, buffer56, 100);
	GetWindowText(hTextbox57, buffer57, 100);
	GetWindowText(hTextbox58, buffer58, 100);
	GetWindowText(hTextbox59, buffer59, 100);
	GetWindowText(hTextbox60, buffer60, 100);
	GetWindowText(hTextbox61, buffer61, 100);
	GetWindowText(hTextbox62, buffer62, 100);
	GetWindowText(hTextbox63, buffer63, 100);
	GetWindowText(hTextbox64, buffer64, 100);
	GetWindowText(hTextbox65, buffer65, 100);
	GetWindowText(hTextbox66, buffer66, 100);
	GetWindowText(hTextbox67, buffer67, 100);
	GetWindowText(hTextbox68, buffer68, 100);
	GetWindowText(hTextbox69, buffer69, 100);
	GetWindowText(hTextbox70, buffer70, 100);
	GetWindowText(hTextbox71, buffer71, 100);
	GetWindowText(hTextbox72, buffer72, 100);
	GetWindowText(hTextbox73, buffer73, 100);
	GetWindowText(hTextbox74, buffer74, 100);
	GetWindowText(hTextbox75, buffer75, 100);
	GetWindowText(hTextbox76, buffer76, 100);
	GetWindowText(hTextbox77, buffer77, 100);
	GetWindowText(hTextbox78, buffer78, 100);
	GetWindowText(hTextbox79, buffer79, 100);
	GetWindowText(hTextbox80, buffer80, 100);
	GetWindowText(hTextbox81, buffer81, 100);
	GetWindowText(hTextbox82, buffer82, 100);
	GetWindowText(hTextbox83, buffer83, 100);
	GetWindowText(hTextbox84, buffer84, 100);
	GetWindowText(hTextbox85, buffer85, 100);

	// ... retrieve text from more textboxes as needed

	//InputValues inputvalues =

	/*float BESS_Energy_lower = _wtof(buffer1);
	float BESS_Energy_upper = _wtof(buffer2);
	float BESS_Energy_step = _wtof(buffer3); */

	float timestep_minutes = static_cast<float>(_wtof(buffer4));

	float timestep_hours = static_cast<float>(_wtof(buffer5));
	float timewindow = static_cast<float>(_wtof(buffer6));

	float Fixed_load1_scalar_lower = static_cast<float>(_wtof(buffer7));
	float Fixed_load1_scalar_upper = static_cast<float>(_wtof(buffer8));
	float Fixed_load1_scalar_step = static_cast<float>(_wtof(buffer9));

	float Fixed_load2_scalar_lower = static_cast<float>(_wtof(buffer10));
	float Fixed_load2_scalar_upper = static_cast<float>(_wtof(buffer11));
	float Fixed_load2_scalar_step = static_cast<float>(_wtof(buffer12));

	float Flex_load_max_lower = static_cast<float>(_wtof(buffer13));
	float Flex_load_max_upper = static_cast<float>(_wtof(buffer14));
	float Flex_load_max_step = static_cast<float>(_wtof(buffer15));

	float Mop_load_max_lower = static_cast<float>(_wtof(buffer16));
	float Mop_load_max_upper = static_cast<float>(_wtof(buffer17));
	float Mop_load_max_step = static_cast<float>(_wtof(buffer18));

	float ScalarRG1_lower = static_cast<float>(_wtof(buffer19));
	float ScalarRG1_upper = static_cast<float>(_wtof(buffer20));
	float ScalarRG1_step = static_cast<float>(_wtof(buffer21));

	float ScalarRG2_lower = static_cast<float>(_wtof(buffer22));
	float ScalarRG2_upper = static_cast<float>(_wtof(buffer23));
	float ScalarRG2_step = static_cast<float>(_wtof(buffer24));

	float ScalarRG3_lower = static_cast<float>(_wtof(buffer25));
	float ScalarRG3_upper = static_cast<float>(_wtof(buffer26));
	float ScalarRG3_step = static_cast<float>(_wtof(buffer27));

	float ScalarRG4_lower = static_cast<float>(_wtof(buffer28));
	float ScalarRG4_upper = static_cast<float>(_wtof(buffer29));
	float ScalarRG4_step = static_cast<float>(_wtof(buffer30));

	float ScalarHL1_lower = static_cast<float>(_wtof(buffer31));
	float ScalarHL1_upper = static_cast<float>(_wtof(buffer32));
	float ScalarHL1_step = static_cast<float>(_wtof(buffer33));

	float ScalarHYield1_lower = static_cast<float>(_wtof(buffer34));
	float ScalarHYield1_upper = static_cast<float>(_wtof(buffer35));
	float ScalarHYield1_step = static_cast<float>(_wtof(buffer36));

	float ScalarHYield2_lower = static_cast<float>(_wtof(buffer37));
	float ScalarHYield2_upper = static_cast<float>(_wtof(buffer38));
	float ScalarHYield2_step = static_cast<float>(_wtof(buffer39));

	float ScalarHYield3_lower = static_cast<float>(_wtof(buffer40));
	float ScalarHYield3_upper = static_cast<float>(_wtof(buffer41));
	float ScalarHYield3_step = static_cast<float>(_wtof(buffer42));

	float ScalarHYield4_lower = static_cast<float>(_wtof(buffer43));
	float ScalarHYield4_upper = static_cast<float>(_wtof(buffer44));
	float ScalarHYield4_step = static_cast<float>(_wtof(buffer45));

	float GridImport_lower = static_cast<float>(_wtof(buffer46));
	float GridImport_upper = static_cast<float>(_wtof(buffer47));
	float GridImport_step = static_cast<float>(_wtof(buffer48));

	float GridExport_lower = static_cast<float>(_wtof(buffer49));
	float GridExport_upper = static_cast<float>(_wtof(buffer50));
	float GridExport_step = static_cast<float>(_wtof(buffer51));

	float Import_headroom_lower = static_cast<float>(_wtof(buffer52));
	float Import_headroom_upper = static_cast<float>(_wtof(buffer53));
	float Import_headroom_step = static_cast<float>(_wtof(buffer54));

	float Export_headroom_lower = static_cast<float>(_wtof(buffer55));
	float Export_headroom_upper = static_cast<float>(_wtof(buffer56));
	float Export_headroom_step = static_cast<float>(_wtof(buffer57));

	float ESS_charge_power_lower = static_cast<float>(_wtof(buffer58));
	float ESS_charge_power_upper = static_cast<float>(_wtof(buffer59));
	float ESS_charge_power_step = static_cast<float>(_wtof(buffer60));

	float ESS_discharge_power_lower = static_cast<float>(_wtof(buffer61));
	float ESS_discharge_power_upper = static_cast<float>(_wtof(buffer62));
	float ESS_discharge_power_step = static_cast<float>(_wtof(buffer63));

	float ESS_capacity_lower = static_cast<float>(_wtof(buffer64));
	float ESS_capacity_upper = static_cast<float>(_wtof(buffer65));
	float ESS_capacity_step = static_cast<float>(_wtof(buffer66));

	float ESS_RTE_lower = static_cast<float>(_wtof(buffer67));
	float ESS_RTE_upper = static_cast<float>(_wtof(buffer68));
	float ESS_RTE_step = static_cast<float>(_wtof(buffer69));

	float ESS_aux_load_lower = static_cast<float>(_wtof(buffer70));
	float ESS_aux_load_upper = static_cast<float>(_wtof(buffer71));
	float ESS_aux_load_step = static_cast<float>(_wtof(buffer72)); // JSM changed ESS_aux_step to ESS_aux_load_step

	float ESS_start_SoC_lower = static_cast<float>(_wtof(buffer73));
	float ESS_start_SoC_upper = static_cast<float>(_wtof(buffer74));
	float ESS_start_SoC_step = static_cast<float>(_wtof(buffer75));

	int ESS_charge_mode_lower = static_cast<int>(_wtoi(buffer76));
	int ESS_charge_mode_upper = static_cast<int>(_wtoi(buffer77));

	int ESS_discharge_mode_lower = static_cast<int>(_wtoi(buffer78));
	int ESS_discharge_mode_upper = static_cast<int>(_wtoi(buffer79));

	float import_kWh_price = static_cast<float>(_wtof(buffer80));
	float export_kWh_price = static_cast<float>(_wtof(buffer81));

	float time_budget_min = static_cast<float>(_wtof(buffer82));

	int target_max_concurrency = static_cast<float>(_wtoi(buffer83));

	float CAPEX_limit = static_cast<float>(_wtof(buffer84));
	float OPEX_limit = static_cast<float>(_wtof(buffer85));

	InputValues inputValues = {
		timestep_minutes, timestep_hours, timewindow,
		Fixed_load1_scalar_lower, Fixed_load1_scalar_upper, Fixed_load1_scalar_step,
		Fixed_load2_scalar_lower, Fixed_load2_scalar_upper, Fixed_load2_scalar_step,
		Flex_load_max_lower, Flex_load_max_upper, Flex_load_max_step,
		Mop_load_max_lower, Mop_load_max_upper, Mop_load_max_step,
		ScalarRG1_lower, ScalarRG1_upper, ScalarRG1_step,
		ScalarRG2_lower, ScalarRG2_upper, ScalarRG2_step,
		ScalarRG3_lower, ScalarRG3_upper, ScalarRG3_step,
		ScalarRG4_lower, ScalarRG4_upper, ScalarRG4_step,
		ScalarHL1_lower, ScalarHL1_upper, ScalarHL1_step,
		ScalarHYield1_lower, ScalarHYield1_upper, ScalarHYield1_step,
		ScalarHYield2_lower, ScalarHYield2_upper, ScalarHYield2_step,
		ScalarHYield3_lower, ScalarHYield3_upper, ScalarHYield3_step,
		ScalarHYield4_lower, ScalarHYield4_upper, ScalarHYield4_step,
		GridImport_lower, GridImport_upper, GridImport_step,
		GridExport_lower, GridExport_upper, GridExport_step,
		Import_headroom_lower, Import_headroom_upper, Import_headroom_step,
		Export_headroom_lower, Export_headroom_upper, Export_headroom_step,
		ESS_charge_power_lower, ESS_charge_power_upper, ESS_charge_power_step,
		ESS_discharge_power_lower, ESS_discharge_power_upper, ESS_discharge_power_step,
		ESS_capacity_lower, ESS_capacity_upper, ESS_capacity_step,
		ESS_RTE_lower, ESS_RTE_upper, ESS_RTE_step,
		ESS_aux_load_lower, ESS_aux_load_upper, ESS_aux_load_step,
		ESS_start_SoC_lower, ESS_start_SoC_upper, ESS_start_SoC_step,
		ESS_charge_mode_lower, ESS_charge_mode_upper,
		ESS_discharge_mode_lower, ESS_discharge_mode_upper,
		import_kWh_price, export_kWh_price,
		time_budget_min, target_max_concurrency,
		CAPEX_limit, OPEX_limit
	};

	return inputValues;
}


void writeOutputToForm(const OutputValues& output) {
	std::cout << "Output.Max: " << output.maxVal << ", Output.Min: " << output.minVal << ", Output.Mean: " << output.meanVal << std::endl;
	wchar_t buffer[300];
	swprintf_s(buffer, 300, L"%f", output.maxVal);
	SetWindowText(hOutput1, buffer);
	swprintf_s(buffer, 300, L"%f", output.minVal);
	SetWindowText(hOutput2, buffer);
	swprintf_s(buffer, 300, L"%f", output.meanVal);
	SetWindowText(hOutput3, buffer);

	swprintf_s(buffer, 300, L"%f", output.CAPEX);
	SetWindowText(hOutput5, buffer);
	swprintf_s(buffer, 300, L"%f", output.annualised);
	SetWindowText(hOutput6, buffer);
	swprintf_s(buffer, 300, L"%f", output.scenario_cost_balance);
	SetWindowText(hOutput7, buffer);

	swprintf_s(buffer, 300, L"%f", output.payback_horizon);
	SetWindowText(hOutput8, buffer);
	swprintf_s(buffer, 300, L"%f", output.scenario_carbon_balance);
	SetWindowText(hOutput9, buffer);

	swprintf_s(buffer, 300, L"%d", output.CAPEX_index);
	SetWindowText(hOutput13, buffer);
	swprintf_s(buffer, 300, L"%d", output.annualised_index);
	SetWindowText(hOutput14, buffer);
	swprintf_s(buffer, 300, L"%d", output.scenario_cost_balance_index);
	SetWindowText(hOutput15, buffer);
	swprintf_s(buffer, 300, L"%d", output.payback_horizon_index);
	SetWindowText(hOutput16, buffer);
	swprintf_s(buffer, 300, L"%d", output.scenario_carbon_balance_index);
	SetWindowText(hOutput17, buffer);
}

void writeInitialiseEstimatesToForm(const OutputValues& output) {
	wchar_t buffer[300];
	swprintf_s(buffer, 300, L"%i", output.num_scenarios);
	SetWindowText(hOutput10, buffer);
	swprintf_s(buffer, 300, L"%f", output.est_hours);
	SetWindowText(hOutput11, buffer);
	swprintf_s(buffer, 300, L"%f", output.est_seconds);
	SetWindowText(hOutput12, buffer);
}

void writeTimingsToForm(std::chrono::steady_clock::time_point start_long) {

	auto end_long = std::chrono::high_resolution_clock::now();
	std::chrono::duration<double> total_elapsed = end_long - start_long;  // calculate total elaspsed run time
	std::cout << "Total Runtime: " << total_elapsed.count() << " seconds" << std::endl; // print elapsed run time
	float elapsed_float = static_cast<float>(total_elapsed.count());
	wchar_t buffer[300];
	swprintf_s(buffer, 300, L"%f", elapsed_float);
	SetWindowText(hOutput4, buffer);
}

void writeRecallValuesToForm(const OutputValues& output) {

	wchar_t buffer[300];
	swprintf_s(buffer, 300, L"%f", output.Fixed_load1_scalar);
	SetWindowText(hTextbox7, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox8, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox9, buffer);


	swprintf_s(buffer, 300, L"%f", output.Fixed_load2_scalar);
	SetWindowText(hTextbox10, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox11, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox12, buffer);


	swprintf_s(buffer, 300, L"%f", output.Flex_load_max);
	SetWindowText(hTextbox13, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox14, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox15, buffer);


	swprintf_s(buffer, 300, L"%f", output.Mop_load_max);
	SetWindowText(hTextbox16, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox17, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox18, buffer);


	swprintf_s(buffer, 300, L"%f", output.ScalarRG1);
	SetWindowText(hTextbox19, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox20, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox21, buffer);


	swprintf_s(buffer, 300, L"%f", output.ScalarRG2);
	SetWindowText(hTextbox22, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox23, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox24, buffer);


	swprintf_s(buffer, 300, L"%f", output.ScalarRG3);
	SetWindowText(hTextbox25, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox26, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox27, buffer);


	swprintf_s(buffer, 300, L"%f", output.ScalarRG4);
	SetWindowText(hTextbox28, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox29, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox30, buffer);


	swprintf_s(buffer, 300, L"%f", output.ScalarHL1);
	SetWindowText(hTextbox31, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox32, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox33, buffer);


	swprintf_s(buffer, 300, L"%f", output.ScalarHYield1);
	SetWindowText(hTextbox34, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox35, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox36, buffer);


	swprintf_s(buffer, 300, L"%f", output.ScalarHYield2);
	SetWindowText(hTextbox37, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox38, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox39, buffer);


	swprintf_s(buffer, 300, L"%f", output.ScalarHYield3);
	SetWindowText(hTextbox40, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox41, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox42, buffer);


	swprintf_s(buffer, 300, L"%f", output.ScalarHYield4);
	SetWindowText(hTextbox43, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox44, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox45, buffer);


	swprintf_s(buffer, 300, L"%f", output.GridImport);
	SetWindowText(hTextbox46, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox47, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox48, buffer);


	swprintf_s(buffer, 300, L"%f", output.GridExport);
	SetWindowText(hTextbox49, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox50, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox51, buffer);


	swprintf_s(buffer, 300, L"%f", output.Import_headroom);
	SetWindowText(hTextbox52, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox53, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox54, buffer);


	swprintf_s(buffer, 300, L"%f", output.Export_headroom);
	SetWindowText(hTextbox55, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox56, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox57, buffer);


	swprintf_s(buffer, 300, L"%f", output.ESS_charge_power);
	SetWindowText(hTextbox58, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox59, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox60, buffer);


	swprintf_s(buffer, 300, L"%f", output.ESS_discharge_power);
	SetWindowText(hTextbox61, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox62, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox63, buffer);


	swprintf_s(buffer, 300, L"%f", output.ESS_capacity);
	SetWindowText(hTextbox64, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox65, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox66, buffer);


	swprintf_s(buffer, 300, L"%f", output.ESS_RTE);
	SetWindowText(hTextbox67, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox68, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox69, buffer);


	swprintf_s(buffer, 300, L"%f", output.ESS_aux_load);
	SetWindowText(hTextbox70, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox71, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox72, buffer);


	swprintf_s(buffer, 300, L"%f", output.ESS_start_SoC);
	SetWindowText(hTextbox73, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox74, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox75, buffer);


	swprintf_s(buffer, 300, L"%d", output.ESS_charge_mode);
	SetWindowText(hTextbox76, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox77, buffer);


	swprintf_s(buffer, 300, L"%d", output.ESS_discharge_mode);
	SetWindowText(hTextbox78, buffer);


	swprintf_s(buffer, 300, L"%s", L"_");
	SetWindowText(hTextbox79, buffer);


	swprintf_s(buffer, 300, L"%f", output.import_kWh_price);
	SetWindowText(hTextbox80, buffer);


	swprintf_s(buffer, 300, L"%f", output.export_kWh_price);
	SetWindowText(hTextbox81, buffer);
}

//
//  FUNCTION: WndProc(HWND, UINT, WPARAM, LPARAM)
//
//  PURPOSE: Processes messages for the main window.
//
//  WM_COMMAND  - process the application menu
//  WM_PAINT    - Paint the main window
//  WM_DESTROY  - post a quit message and return
//
//
LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam)
{
	int wmID, wmEvent;

	SCROLLINFO si = { sizeof(si), SIF_ALL };

	auto optimiser = Optimiser();

	switch (message)
	{
	case WM_CREATE:
	{
		// Vertical Scroll Initialization
		SCROLLINFO siVert = { sizeof(siVert), SIF_RANGE | SIF_PAGE, 0, 400, 20 }; // Doubled the range
		SetScrollInfo(hWnd, SB_VERT, &siVert, TRUE);

		// Horizontal Scroll Initialization
		SCROLLINFO siHorz = { sizeof(siHorz), SIF_RANGE | SIF_PAGE, 0, 400, 20 }; // Doubled the range
		SetScrollInfo(hWnd, SB_HORZ, &siHorz, TRUE);
	}
	break;
	// ... other cases ..

	case WM_VSCROLL:
	{
		// First, get the current scroll info.
		si.fMask = SIF_ALL;
		GetScrollInfo(hWnd, SB_VERT, &si);
		int yPos = si.nPos;
		int yDelta;

		switch (LOWORD(wParam))
		{
		case SB_LINEUP:
			yPos--;
			break;
		case SB_LINEDOWN:
			yPos++;
			break;
		case SB_PAGEUP:
			yPos -= si.nPage;
			break;
		case SB_PAGEDOWN:
			yPos += si.nPage;
			break;
		case SB_THUMBTRACK:
			yPos = HIWORD(wParam);
			break;
		default:
			break;
		}

		// After modifications, set the new position and then re-display the thumb
		yPos = std::max(si.nMin, std::min(yPos, si.nMax - (int)si.nPage + 1));
		yDelta = si.nPos - yPos;

		if (yDelta != 0)
		{
			si.fMask = SIF_POS;
			si.nPos = yPos;
			SetScrollInfo(hWnd, SB_VERT, &si, TRUE);
			// Scroll the window accordingly
			ScrollWindow(hWnd, 0, yDelta, NULL, NULL);
			// Update the window
			UpdateWindow(hWnd);
		}
	}
	break;

	case WM_HSCROLL:
	{
		// First, get the current scroll info for horizontal scrolling.
		si.fMask = SIF_ALL;
		GetScrollInfo(hWnd, SB_HORZ, &si);
		int xPos = si.nPos;
		int xDelta;

		switch (LOWORD(wParam))
		{
		case SB_LINELEFT:
			xPos--;
			break;
		case SB_LINERIGHT:
			xPos++;
			break;
		case SB_PAGELEFT:
			xPos -= si.nPage;
			break;
		case SB_PAGERIGHT:
			xPos += si.nPage;
			break;
		case SB_THUMBTRACK:
			xPos = HIWORD(wParam);
			break;
		default:
			break;
		}

		xPos = std::max(si.nMin, std::min(xPos, si.nMax - (int)si.nPage + 1));
		xDelta = si.nPos - xPos;

		if (xDelta != 0)
		{
			si.fMask = SIF_POS;
			si.nPos = xPos;
			SetScrollInfo(hWnd, SB_HORZ, &si, TRUE);
			ScrollWindow(hWnd, xDelta, 0, NULL, NULL);
			UpdateWindow(hWnd);
		}
	}
	break;

	case WM_COMMAND:
	{
		auto start_long = std::chrono::high_resolution_clock::now();
		int wmId = LOWORD(wParam);
		int wmEvent = HIWORD(wParam);
		// Parse the menu selections:
		switch (wmId)
		{
		case ID_BUTTON1: // this the RUN button for main otpimisation
			if (wmEvent == BN_CLICKED) {

				InitConsole();
				InputValues inputValues = readInputFromForm();

				auto converted_json = handleJsonConversion(inputValues, memberMappings, std::size(memberMappings));

				OutputValues output = optimiser.runMainOptimisation(converted_json);

				writeOutputToForm(output);

				// Convert the OutputValues struct to a JSON object using the mapping
				nlohmann::json jsonObj = structToJsonOut(output, OutmemberMappings, std::size(OutmemberMappings));
				writeJsonToFile(jsonObj, "outputparameters.json");
				std::cout << "JSON file written successfully!" << std::endl;

				writeTimingsToForm(start_long);

				std::cout << "Sleeping for 5 seconds..."; // this allows time to read the console if needed. Adjust if needed
				//std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n'); // Clear the input buffer
				//std::cin.get(); // Wait for keystroke

				std::this_thread::sleep_for(std::chrono::seconds(5));


			}
			CloseConsole();
			break;

		case ID_BUTTON0: // this is the INITIALISE button to estimate the optimisation time
			if (wmEvent == BN_CLICKED) {

				InitConsole();
				InputValues inputValues = readInputFromForm();

				auto converted_json = handleJsonConversion(inputValues, memberMappings, std::size(memberMappings));

				OutputValues output = optimiser.initialiseOptimisation(converted_json);

				writeInitialiseEstimatesToForm(output);

				// Convert the InputValues struct to a JSON object using the mapping
				nlohmann::json jsonObj = structToJsonOut(output, OutmemberMappings, std::size(OutmemberMappings));

				// Write the JSON to a file
				writeJsonToFile(jsonObj, "outputparameters_init.json");
				std::cout << "JSON file written successfully!" << std::endl;

				writeTimingsToForm(start_long);

				std::cout << "Sleeping for 1 seconds..."; // this allows time to read the console if needed. Adjust if needed
				//std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n'); // Clear the input buffer
				//std::cin.get(); // Wait for keystroke

				std::this_thread::sleep_for(std::chrono::seconds(1));

			}
			CloseConsole();
			break;

		case ID_BUTTON2: // this is the RECALL button to recall a parameter slice by index
			if (wmEvent == BN_CLICKED) {
				InitConsole();
				InputValues inputValues = readInputFromForm();

				auto converted_json = handleJsonConversion(inputValues, memberMappings, std::size(memberMappings));

				wchar_t buffer100[100];
				GetWindowText(hTextbox200, buffer100, 100);
				int recall_index = _wtof(buffer100);
			
				OutputValues output = optimiser.RecallIndex(converted_json, recall_index);

				writeRecallValuesToForm(output);
			}
			CloseConsole();
			break;
		}
	}

	case WM_PAINT:
	{
		PAINTSTRUCT ps;
		HDC hdc = BeginPaint(hWnd, &ps);
		// TODO: Add any drawing code that uses hdc here...
		EndPaint(hWnd, &ps);
	}
	break;

	case WM_DESTROY:
	{
		PostQuitMessage(0);
		break;
	default:
		return DefWindowProc(hWnd, message, wParam, lParam);
	}
	return 0;

	}
}

// Message handler for about box.
INT_PTR CALLBACK About(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    UNREFERENCED_PARAMETER(lParam);
    switch (message)
    {
    case WM_INITDIALOG:
        return (INT_PTR)TRUE;

    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK || LOWORD(wParam) == IDCANCEL)
        {
            EndDialog(hDlg, LOWORD(wParam));
            return (INT_PTR)TRUE;
        }
        break;
    }
    return (INT_PTR)FALSE;
}
