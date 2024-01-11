#pragma once

#define NOMINMAX  // necessary before including windows.h
#include <Windows.h>

#include "../../EP/Definitions.h"
#include "../../EP/Optimisation/Optimiser.hpp"
#include "../../EP/io/FileHandling.hpp"

#define MAX_LOADSTRING 100
#define BUTTON_INITIALISE 0
#define BUTTON_OPTIMISE 1 
#define BUTTON_RECALL 200

#define ID_TEXTBOX_TIMESTEP_MINUTES 4
#define ID_TEXTBOX_TIMESTEP_HOURS 5
#define ID_TEXTBOX_TIME_WINDOW_HOURS 6
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
#define ID_TEXTBOX80 80
#define ID_TEXTBOX81 81
#define ID_TEXTBOX82 82
#define ID_TEXTBOX83 83
#define ID_TEXTBOX84 84
#define ID_TEXTBOX85 85
#define ID_TEXTBOX86 86
#define ID_TEXTBOX87 87
#define ID_TEXTBOX88 88
#define ID_TEXTBOX89 89
#define ID_TEXTBOX90 90
#define ID_TEXTBOX91 91
#define ID_TEXTBOX92 92
#define ID_TEXTBOX93 93
#define ID_TEXTBOX94 94
#define ID_TEXTBOX95 95
#define ID_TEXTBOX96 96
#define ID_TEXTBOX97 97
#define ID_TEXTBOX98 98
#define ID_TEXTBOX99 99

#define ID_TEXTBOX_INDEX 200

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

HWND hTextbox1; HWND hTextbox2; HWND hTextbox3; HWND hTextboxTimestepMinutes; HWND hTextboxTimestepHours; HWND hTextboxTimeWindowHours; HWND hTextbox7; HWND hTextbox8; HWND hTextbox9; HWND hTextbox10;
HWND hTextbox11; HWND hTextbox12; HWND hTextbox13; HWND hTextbox14; HWND hTextbox15; HWND hTextbox16; HWND hTextbox17; HWND hTextbox18; HWND hTextbox19; HWND hTextbox20;
HWND hTextbox21; HWND hTextbox22; HWND hTextbox23; HWND hTextbox24; HWND hTextbox25; HWND hTextbox26; HWND hTextbox27; HWND hTextbox28; HWND hTextbox29; HWND hTextbox30;
HWND hTextbox31; HWND hTextbox32; HWND hTextbox33; HWND hTextbox34; HWND hTextbox35; HWND hTextbox36; HWND hTextbox37; HWND hTextbox38; HWND hTextbox39; HWND hTextbox40;
HWND hTextbox41; HWND hTextbox42; HWND hTextbox43; HWND hTextbox44; HWND hTextbox45; HWND hTextbox46; HWND hTextbox47; HWND hTextbox48; HWND hTextbox49; HWND hTextbox50;
HWND hTextbox51; HWND hTextbox52; HWND hTextbox53; HWND hTextbox54; HWND hTextbox55; HWND hTextbox56; HWND hTextbox57; HWND hTextbox58; HWND hTextbox59; HWND hTextbox60;
HWND hTextbox61; HWND hTextbox62; HWND hTextbox63; HWND hTextbox64; HWND hTextbox65; HWND hTextbox66; HWND hTextbox67; HWND hTextbox68; HWND hTextbox69; HWND hTextbox70;
HWND hTextbox71; HWND hTextbox72; HWND hTextbox73; HWND hTextbox74; HWND hTextbox75; HWND hTextbox76; HWND hTextbox77; HWND hTextbox78; HWND hTextbox79; HWND hTextbox80;
HWND hTextbox81; HWND hTextbox82; HWND hTextbox83; HWND hTextbox84; HWND hTextbox85; HWND hTextbox86; HWND hTextbox87; HWND hTextbox88; HWND hTextbox89;

HWND hTextboxIndex;

HWND hOutput1; HWND hOutput2; HWND hOutput3; HWND hOutput4; HWND hOutput5; HWND hOutput6; HWND hOutput7; HWND hOutput8; HWND hOutput9; HWND hOutput10;
HWND hOutput11; HWND hOutput12; HWND hOutput13; HWND hOutput14; HWND hOutput15; HWND hOutput16; HWND hOutput17; HWND hOutput18; HWND hOutput19; HWND hOutput20;
HWND hOutput21; HWND hOutput22; HWND hOutput23; HWND hOutput24; HWND hOutput25; HWND hOutput26; HWND hOutput27; HWND hOutput28; HWND hOutput29; HWND hOutput30;
HWND hOutput31; HWND hOutput32; HWND hOutput33; HWND hOutput34; HWND hOutput35; HWND hOutput36;


//
//  FUNCTION: MyRegisterClass()
//
//  PURPOSE: Registers the window class.
//
ATOM MyRegisterClass(HINSTANCE hInstance)
{
	WNDCLASSEXW wcex;

	wcex.cbSize = sizeof(WNDCLASSEX);

	wcex.style = CS_HREDRAW | CS_VREDRAW;
	wcex.lpfnWndProc = WndProc;
	wcex.cbClsExtra = 0;
	wcex.cbWndExtra = 0;
	wcex.hInstance = hInstance;
	wcex.hIcon = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_EPMAIN));
	wcex.hCursor = LoadCursor(nullptr, IDC_ARROW);
	wcex.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
	wcex.lpszMenuName = MAKEINTRESOURCEW(IDC_EPMAIN);
	wcex.lpszClassName = szWindowClass;
	wcex.hIconSm = LoadIcon(wcex.hInstance, MAKEINTRESOURCE(IDI_SMALL));

	return RegisterClassExW(&wcex);
}



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


HWND makeTextBox(HWND parent, HINSTANCE hInstance, HMENU textboxID, int x, int y, int w, int h, LPCWSTR initialText) {
	return CreateWindowW(
		L"EDIT",
		initialText,
		WS_VISIBLE | WS_CHILD | WS_BORDER | ES_LEFT, //| ES_READONLY,
		x, y, w, h,
		parent,
		(HMENU)textboxID,
		hInstance,
		NULL);
}

HWND makeLabel(HWND parent, HINSTANCE hInstance, LPCWSTR text, int x, int y, int w, int h) {
	return CreateWindowW(
		L"STATIC",
		text,
		WS_VISIBLE | WS_CHILD,
		x, y, w, h,
		parent,
		NULL,
		hInstance,
		NULL);
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

	HWND hButtonInitialise = CreateWindow(
		L"BUTTON",  // Predefined class; Unicode assumed.
		L"INITIALISE",      // Button text.
		WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,  // Styles.
		10,         // x position.
		10,         // y position.
		100,        // Button width.
		30,         // Button height.
		hWnd,       // Parent window.
		(HMENU)BUTTON_INITIALISE,       // No menu.
		(HINSTANCE)GetWindowLongPtr(hWnd, GWLP_HINSTANCE),
		NULL);      // Pointer not needed.
	// ... add more textboxes as needed

	HWND hButtonOptimise = CreateWindow(
		L"BUTTON",  // Predefined class; Unicode assumed.
		L"RUN",      // Button text.
		WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,  // Styles.
		10,         // x position.
		80,         // y position.
		100,        // Button width.
		30,         // Button height.
		hWnd,       // Parent window.
		(HMENU)BUTTON_OPTIMISE,       // No menu.
		(HINSTANCE)GetWindowLongPtr(hWnd, GWLP_HINSTANCE),
		NULL);      // Pointer not needed.

	HWND hButtonRecall = CreateWindow(
		L"BUTTON",  // Predefined class; Unicode assumed.
		L"RECALL",      // Button text.
		WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,  // Styles.
		10,         // x position.
		150,         // y position.
		100,        // Button width.
		30,         // Button height.
		hWnd,       // Parent window.
		(HMENU)BUTTON_RECALL,       // No menu.
		(HINSTANCE)GetWindowLongPtr(hWnd, GWLP_HINSTANCE),
		NULL);      // Pointer not needed.

	HWND hLabelIndex = makeLabel(hWnd, hInstance, L"INDEX", 10, 180, 100, 30);

	hTextboxIndex = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX_INDEX, 10, 210, 100, 30, L"");

	HWND hLabelEstimatedTime = makeLabel(hWnd, hInstance, L"ESTIMATED TIME", 120, 10, 100, 50);

	HWND hLabelNumScenarios = makeLabel(hWnd, hInstance, L"# Scenarios", 240, 10, 100, 20);

	HWND hLabelHours = makeLabel(hWnd, hInstance, L"Hours", 360, 10, 100, 20);

	HWND hLabelSeconds = makeLabel(hWnd, hInstance, L"Seconds", 480, 10, 100, 20);

	HWND hLabelInputs = makeLabel(hWnd, hInstance, L"INPUTS (overwrite default values)", 120, 80, 100, 80);

	HWND hLabelTimestepMinutes = makeLabel(hWnd, hInstance, L"Timestep, Minutes", 240, 80, 100, 50);

	hTextboxTimestepMinutes = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX_TIMESTEP_MINUTES, 240, 130, 100, 30, L"60");

	HWND hLabelTimestepHours = makeLabel(hWnd, hInstance, L"Timestep, Hours", 360, 80, 100, 50);

	hTextboxTimestepHours = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX_TIMESTEP_HOURS, 360, 130, 100, 30, L"1");

	HWND hLabelTimeWindowHours = makeLabel(hWnd, hInstance, L"Time window, hours", 480, 80, 100, 50);

	hTextboxTimeWindowHours = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX_TIME_WINDOW_HOURS, 480, 130, 100, 30, L"8760");

	// new button row 

	HWND hLabel7 = makeLabel(hWnd, hInstance, L"Fixed load1 scalar lower", 120, 180, 100, 50);
	hTextbox7 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX7, 120, 230, 100, 30, L"1");

	HWND hLabel8 = makeLabel(hWnd, hInstance, L"Fixed load1 scalar upper", 240, 180, 100, 50);
	hTextbox8 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX8, 240, 230, 100, 30, L"1");

	HWND hLabel9 = makeLabel(hWnd, hInstance, L"Fixed load1 scalar step", 360, 180, 100, 50);
	hTextbox9 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX9, 360, 230, 100, 30, L"0");

	HWND hLabel10 = makeLabel(hWnd, hInstance, L"Fixed load2 scalar lower", 480, 180, 100, 50);
	hTextbox10 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX10, 480, 230, 100, 30, L"3");

	HWND hLabel11 = makeLabel(hWnd, hInstance, L"Fixed load2 scalar upper", 600, 180, 100, 50);
	hTextbox11 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX11, 600, 230, 100, 30, L"3");

	HWND hLabel12 = makeLabel(hWnd, hInstance, L"Fixed load2 scalar step", 720, 180, 100, 50);
	hTextbox12 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX12, 720, 230, 100, 30, L"0");

	HWND hLabel13 = makeLabel(hWnd, hInstance, L"Flex max lower", 840, 180, 100, 50);
	hTextbox13 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX13, 840, 230, 100, 30, L"50.0");

	HWND hLabel14 = makeLabel(hWnd, hInstance, L"Flex max lower upper", 960, 180, 100, 50);
	hTextbox14 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX14, 960, 230, 100, 30, L"50.0");

	HWND hLabel15 = makeLabel(hWnd, hInstance, L"Flex max lower step", 1080, 180, 100, 50);
	hTextbox15 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX15, 1080, 230, 100, 30, L"0");

	HWND hLabel16 = makeLabel(hWnd, hInstance, L"Mop load max lower", 1200, 180, 100, 50);
	hTextbox16 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX16, 1200, 230, 100, 30, L"300.0");

	HWND hLabel17 = makeLabel(hWnd, hInstance, L"Mop load max upper", 1320, 180, 100, 50);
	hTextbox17 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX17, 1320, 230, 100, 30, L"300.0");

	HWND hLabel18 = makeLabel(hWnd, hInstance, L"Mop load max step", 1440, 180, 100, 50);
	hTextbox18 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX18, 1440, 230, 100, 30, L"0");

	// new GUI row 

	HWND hLabel19 = makeLabel(hWnd, hInstance, L"Scalar RG1 lower", 120, 280, 100, 50);
	hTextbox19 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX19, 120, 330, 100, 30, L"599.2");

	HWND hLabel20 = makeLabel(hWnd, hInstance, L"Scalar RG1 upper", 240, 280, 100, 50);
	hTextbox20 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX20, 240, 330, 100, 30, L"599.2");

	HWND hLabel21 = makeLabel(hWnd, hInstance, L"Scalar RG1 step", 360, 280, 100, 50);
	hTextbox21 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX21, 360, 330, 100, 30, L"0");

	HWND hLabel22 = makeLabel(hWnd, hInstance, L"Scalar RG2 lower", 480, 280, 100, 50);
	hTextbox22 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX22, 480, 330, 100, 30, L"75.6");

	HWND hLabel23 = makeLabel(hWnd, hInstance, L"Scalar RG2 upper", 600, 280, 100, 50);
	hTextbox23 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX23, 600, 330, 100, 30, L"75.6");

	HWND hLabel24 = makeLabel(hWnd, hInstance, L"Scalar RG2 step", 720, 280, 100, 50);
	hTextbox24 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX24, 720, 330, 100, 30, L"0");

	HWND hLabel25 = makeLabel(hWnd, hInstance, L"Scalar RG3 lower", 840, 280, 100, 50);
	hTextbox25 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX25, 840, 330, 100, 30, L"60.48");

	HWND hLabel26 = makeLabel(hWnd, hInstance, L"Scalar RG3 upper", 960, 280, 100, 50);
	hTextbox26 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX26, 960, 330, 100, 30, L"60.48");

	HWND hLabel27 = makeLabel(hWnd, hInstance, L"Scalar RG3 step", 1080, 280, 100, 50);
	hTextbox27 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX27, 1080, 330, 100, 30, L"0");

	HWND hLabel28 = makeLabel(hWnd, hInstance, L"Scalar RG4 lower", 1200, 280, 100, 50);
	hTextbox28 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX28, 1200, 330, 100, 30, L"0.0");

	HWND hLabel29 = makeLabel(hWnd, hInstance, L"Scalar RG4 upper", 1320, 280, 100, 50);
	hTextbox29 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX29, 1320, 330, 100, 30, L"0.0");

	HWND hLabel30 = makeLabel(hWnd, hInstance, L"Scalar RG4 step", 1440, 280, 100, 50);
	hTextbox30 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX30, 1440, 330, 100, 30, L"0");

	// New GUI row

	HWND hLabel31 = makeLabel(hWnd, hInstance, L"Scalar HL1 lower", 120, 380, 100, 50);
	hTextbox31 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX31, 120, 430, 100, 30, L"1.0");

	HWND hLabel32 = makeLabel(hWnd, hInstance, L"Scalar HL1 upper", 240, 380, 100, 50);
	hTextbox32 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX32, 240, 430, 100, 30, L"1.0");

	HWND hLabel33 = makeLabel(hWnd, hInstance, L"Scalar HL1 step", 360, 380, 100, 50);
	hTextbox33 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX33, 360, 430, 100, 30, L"0");

	HWND hLabel34 = makeLabel(hWnd, hInstance, L"Scalar HYield1 lower", 480, 380, 100, 50);
	hTextbox34 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX34, 480, 430, 100, 30, L"0.0");

	HWND hLabel35 = makeLabel(hWnd, hInstance, L"Scalar HYield1 upper", 600, 380, 100, 50);
	hTextbox35 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX35, 600, 430, 100, 30, L"0.0");

	HWND hLabel36 = makeLabel(hWnd, hInstance, L"Scalar HYield1 step", 720, 380, 100, 50);
	hTextbox36 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX36, 720, 430, 100, 30, L"0");

	HWND hLabel37 = makeLabel(hWnd, hInstance, L"Scalar HYield2 lower", 840, 380, 100, 50);
	hTextbox37 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX37, 840, 430, 100, 30, L"0.0");

	HWND hLabel38 = makeLabel(hWnd, hInstance, L"Scalar HYield2 upper", 960, 380, 100, 50);
	hTextbox38 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX38, 960, 430, 100, 30, L"0.0");

	HWND hLabel39 = makeLabel(hWnd, hInstance, L"Scalar HYield2 step", 1080, 380, 100, 50);
	hTextbox39 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX39, 1080, 430, 100, 30, L"0");

	HWND hLabel40 = makeLabel(hWnd, hInstance, L"Scalar HYield3 lower", 1200, 380, 100, 50);
	hTextbox40 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX40, 1200, 430, 100, 30, L"0.75");

	HWND hLabel41 = makeLabel(hWnd, hInstance, L"Scalar HYield3 upper", 1320, 380, 100, 50);
	hTextbox41 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX41, 1320, 430, 100, 30, L"0.75");

	HWND hLabel42 = makeLabel(hWnd, hInstance, L"Scalar HYield3 step", 1440, 380, 100, 50);
	hTextbox42 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX42, 1440, 430, 100, 30, L"0");

	HWND hLabel43 = makeLabel(hWnd, hInstance, L"Scalar HYield4 lower", 1560, 380, 100, 50);
	hTextbox43 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX43, 1560, 430, 100, 30, L"0.0");

	HWND hLabel44 = makeLabel(hWnd, hInstance, L"Scalar HYield4 upper", 1680, 380, 100, 50);
	hTextbox44 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX44, 1680, 430, 100, 30, L"0.0");

	HWND hLabel45 = makeLabel(hWnd, hInstance, L"Scalar HYield4 step", 1800, 380, 100, 50);
	hTextbox45 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX45, 1800, 430, 100, 30, L"0");

	// New GUI row

	HWND hLabel46 = makeLabel(hWnd, hInstance, L"Grid import lower", 120, 480, 100, 50);
	hTextbox46 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX46, 120, 530, 100, 30, L"98.29");

	HWND hLabel47 = makeLabel(hWnd, hInstance, L"Grid import upper", 240, 480, 100, 50);
	hTextbox47 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX47, 240, 530, 100, 30, L"98.29");

	HWND hLabel48 = makeLabel(hWnd, hInstance, L"Grid import step", 360, 480, 100, 50);
	hTextbox48 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX48, 360, 530, 100, 30, L"0.0");

	HWND hLabel49 = makeLabel(hWnd, hInstance, L"Grid export lower", 480, 480, 100, 50);
	hTextbox49 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX49, 480, 530, 100, 30, L"95.0");

	HWND hLabel50 = makeLabel(hWnd, hInstance, L"Grid export upper", 600, 480, 100, 50);
	hTextbox50 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX50, 600, 530, 100, 30, L"95.0");

	HWND hLabel51 = makeLabel(hWnd, hInstance, L"Grid export step", 720, 480, 100, 50);
	hTextbox51 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX51, 720, 530, 100, 30, L"0");

	HWND hLabel52 = makeLabel(hWnd, hInstance, L"Import headroom lower", 840, 480, 100, 50);
	hTextbox52 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX52, 840, 530, 100, 30, L"0.0");

	HWND hLabel53 = makeLabel(hWnd, hInstance, L"Import headroom upper", 960, 480, 100, 50);
	hTextbox53 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX53, 960, 530, 100, 30, L"0.0");

	HWND hLabel54 = makeLabel(hWnd, hInstance, L"Import headroom step", 1080, 480, 100, 50);
	hTextbox54 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX54, 1080, 530, 100, 30, L"0");

	HWND hLabel55 = makeLabel(hWnd, hInstance, L"Export headroom lower", 1200, 480, 100, 50);
	hTextbox55 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX55, 1200, 530, 100, 30, L"0.0");

	HWND hLabel56 = makeLabel(hWnd, hInstance, L"Export headroom upper", 1320, 480, 100, 50);
	hTextbox56 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX56, 1320, 530, 100, 30, L"0.0");

	HWND hLabel57 = makeLabel(hWnd, hInstance, L"Export headroom step", 1440, 480, 100, 50);
	hTextbox57 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX57, 1440, 530, 100, 30, L"0");

	// New GUI row

	HWND hLabel58 = makeLabel(hWnd, hInstance, L"ESS charge power lower", 120, 580, 100, 50);
	hTextbox58 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX58, 120, 630, 100, 30, L"300.0");

	HWND hLabel59 = makeLabel(hWnd, hInstance, L"ESS charge power upper", 240, 580, 100, 50);
	hTextbox59 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX59, 240, 630, 100, 30, L"600.0");

	HWND hLabel60 = makeLabel(hWnd, hInstance, L"ESS charge power step", 360, 580, 100, 50);
	hTextbox60 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX60, 360, 630, 100, 30, L"300.0");

	HWND hLabel61 = makeLabel(hWnd, hInstance, L"ESS discharge power lower", 480, 580, 100, 50);
	hTextbox61 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX61, 480, 630, 100, 30, L"300.0");

	HWND hLabel62 = makeLabel(hWnd, hInstance, L"ESS discharge power upper", 600, 580, 100, 50);
	hTextbox62 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX62, 600, 630, 100, 30, L"600.0");

	HWND hLabel63 = makeLabel(hWnd, hInstance, L"ESS discharge power step", 720, 580, 100, 50);
	hTextbox63 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX63, 720, 630, 100, 30, L"300.0");

	HWND hLabel64 = makeLabel(hWnd, hInstance, L"ESS capacity lower", 840, 580, 100, 50);
	hTextbox64 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX64, 840, 630, 100, 30, L"800.0");

	HWND hLabel65 = makeLabel(hWnd, hInstance, L"ESS capacity upper", 960, 580, 100, 50);
	hTextbox65 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX65, 960, 630, 100, 30, L"900.0");

	HWND hLabel66 = makeLabel(hWnd, hInstance, L"ESS capacity step", 1080, 580, 100, 50);
	hTextbox66 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX66, 1080, 630, 100, 30, L"20");

	HWND hLabel67 = makeLabel(hWnd, hInstance, L"ESS RTE lower", 1200, 580, 100, 50);
	hTextbox67 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX67, 1200, 630, 100, 30, L"0.86");

	HWND hLabel68 = makeLabel(hWnd, hInstance, L"ESS RTE upper", 1320, 580, 100, 50);
	hTextbox68 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX68, 1320, 630, 100, 30, L"0.86");

	HWND hLabel69 = makeLabel(hWnd, hInstance, L"ESS RTE step", 1440, 580, 100, 50);
	hTextbox69 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX69, 1440, 630, 100, 30, L"0");

	// new GUI row 

	HWND hLabel70 = makeLabel(hWnd, hInstance, L"ESS aux load lower", 120, 680, 100, 50);
	hTextbox70 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX70, 120, 730, 100, 30, L"0.75");

	HWND hLabel71 = makeLabel(hWnd, hInstance, L"ESS aux load upper", 240, 680, 100, 50);
	hTextbox71 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX71, 240, 730, 100, 30, L"0.75");

	HWND hLabel72 = makeLabel(hWnd, hInstance, L"ESS aux load step", 360, 680, 100, 50);
	hTextbox72 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX72, 360, 730, 100, 30, L"0");

	HWND hLabel73 = makeLabel(hWnd, hInstance, L"ESS start SoC lower", 480, 680, 100, 50);
	hTextbox73 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX73, 480, 730, 100, 30, L"0.5");

	HWND hLabel74 = makeLabel(hWnd, hInstance, L"ESS start SoC Upper", 600, 680, 100, 50);
	hTextbox74 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX74, 600, 730, 100, 30, L"0.5");

	HWND hLabel75 = makeLabel(hWnd, hInstance, L"ESS start SoC step", 720, 680, 100, 50);
	hTextbox75 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX75, 720, 730, 100, 30, L"0");

	HWND hLabel76 = makeLabel(hWnd, hInstance, L"ESS charge mode lower", 840, 680, 100, 50);
	hTextbox76 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX76, 840, 730, 100, 30, L"1");

	HWND hLabel77 = makeLabel(hWnd, hInstance, L"ESS charge mode upper", 960, 680, 100, 50);
	hTextbox77 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX77, 960, 730, 100, 30, L"1");

	HWND hLabel78 = makeLabel(hWnd, hInstance, L"ESS discharge mode lower", 1080, 680, 100, 50);
	hTextbox78 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX78, 1080, 730, 100, 30, L"1");

	HWND hLabel79 = makeLabel(hWnd, hInstance, L"ESS discharge mode upper", 1200, 680, 100, 50);
	hTextbox79 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX79, 1200, 730, 100, 30, L"1");

	// new GUI row 
	HWND hLabel80 = makeLabel(hWnd, hInstance, L"Import Price p/kWh", 120, 780, 100, 50);
	hTextbox80 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX80, 120, 830, 100, 30, L"30");

	HWND hLabel81 = makeLabel(hWnd, hInstance, L"Export Price p/kWh", 240, 780, 100, 50);
	hTextbox81 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX81, 240, 830, 100, 30, L"5");

	HWND hLabel82 = makeLabel(hWnd, hInstance, L"Time budget, minutes", 360, 780, 100, 50);
	hTextbox82 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX85, 360, 830, 100, 30, L"1.0");

	HWND hLabel83 = makeLabel(hWnd, hInstance, L"Target Max Concurrency", 480, 780, 100, 50);
	hTextbox83 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX86, 480, 830, 100, 30, L"44");

	HWND hLabel84 = makeLabel(hWnd, hInstance, L"CAPEX limit, £k", 600, 780, 100, 50);
	hTextbox84 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX87, 600, 830, 100, 30, L"500");

	HWND hLabel85 = makeLabel(hWnd, hInstance, L"OPEX limit, £k", 720, 780, 100, 50);
	hTextbox85 = makeTextBox(hWnd, hInstance, (HMENU)ID_TEXTBOX88, 720, 830, 100, 30, L"20");

	// new GUI row 

	HWND hLabelout0 = makeLabel(hWnd, hInstance, L"OUTPUTS", 10, 890, 100, 50);

	HWND hLabelout1 = makeLabel(hWnd, hInstance, L"Scenario Max Time, s", 120, 890, 100, 50);

	hOutput1 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT1, 120, 950, 100, 30, L"");

	HWND hLabelout2 = makeLabel(hWnd, hInstance, L"Scenario Min Time, s", 240, 890, 100, 50);
	hOutput2 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT2, 240, 950, 100, 30, L"");

	HWND hLabelout3 = makeLabel(hWnd, hInstance, L"Scenario Mean Time, s", 360, 890, 100, 50);
	hOutput3 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT3, 360, 950, 100, 30, L"");

	HWND hLabelout4 = makeLabel(hWnd, hInstance, L"Total time taken, s", 480, 890, 100, 50);
	hOutput4 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT4, 480, 950, 100, 30, L"");

	HWND hLabelout5 = makeLabel(hWnd, hInstance, L"Min CAPEX, £", 600, 890, 100, 50);
	hOutput5 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT5, 600, 950, 100, 30, L"");

	HWND hLabelout6 = makeLabel(hWnd, hInstance, L"Min Annualised, £", 720, 890, 100, 50);
	hOutput6 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT6, 720, 950, 100, 30, L"");

	HWND hLabelout7 = makeLabel(hWnd, hInstance, L"Max Cost balance, £", 840, 890, 100, 50);
	hOutput7 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT7, 840, 950, 100, 30, L"");

	HWND hLabelout8 = makeLabel(hWnd, hInstance, L"Min Breakeven years", 960, 890, 100, 50);
	hOutput8 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT8, 960, 950, 100, 30, L"");

	HWND hLabelout9 = makeLabel(hWnd, hInstance, L"Max Carbon balance, kgC02e", 1080, 890, 100, 50);
	hOutput9 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT9, 1080, 950, 100, 30, L"");

	hOutput10 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT10, 240, 30, 100, 30, L"");
	hOutput11 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT11, 360, 30, 100, 30, L"");
	hOutput12 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT12, 480, 30, 100, 30, L"");

	HWND hLabelout13 = makeLabel(hWnd, hInstance, L"INDEX", 480, 1010, 100, 50);
	hOutput13 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT13, 600, 1010, 100, 30, L"");
	hOutput14 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT14, 720, 1010, 100, 30, L"");
	hOutput15 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT15, 840, 1010, 100, 30, L"");
	hOutput16 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT16, 960, 1010, 100, 30, L"");
	hOutput17 = makeTextBox(hWnd, hInstance, (HMENU)ID_OUTPUT17, 1080, 1010, 100, 30, L"");

	// ... add more textboxes as needed

	if (!hWnd)
	{
		return FALSE;
	}

	ShowWindow(hWnd, nCmdShow);
	UpdateWindow(hWnd);

	return TRUE;
}


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
	GetWindowText(hTextboxTimestepMinutes, buffer4, 100);
	GetWindowText(hTextboxTimestepHours, buffer5, 100);
	GetWindowText(hTextboxTimeWindowHours, buffer6, 100);
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

	FileConfig fileConfig{};
	auto optimiser = Optimiser(fileConfig);

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
		case BUTTON_OPTIMISE: // this the RUN button for main otpimisation
			if (wmEvent == BN_CLICKED) {

				InitConsole();
				InputValues inputValues = readInputFromForm();

				auto converted_json = handleJsonConversion(inputValues, fileConfig.getInputDir());

				OutputValues output = optimiser.runMainOptimisation(converted_json);

				writeOutputToForm(output);

				// Convert the OutputValues struct to a JSON object using the mapping
				nlohmann::json jsonObj = outputToJson(output);
				writeJsonToFile(jsonObj, fileConfig.getOutputJsonFilepath());
				std::cout << "JSON file written successfully!" << std::endl;

				writeTimingsToForm(start_long);

				std::cout << "Sleeping for 5 seconds..."; // this allows time to read the console if needed. Adjust if needed
				//std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n'); // Clear the input buffer
				//std::cin.get(); // Wait for keystroke

				std::this_thread::sleep_for(std::chrono::seconds(5));


			}
			CloseConsole();
			break;

		case BUTTON_INITIALISE: // this is the INITIALISE button to estimate the optimisation time
			if (wmEvent == BN_CLICKED) {

				InitConsole();
				InputValues inputValues = readInputFromForm();

				auto converted_json = handleJsonConversion(inputValues, fileConfig.getInputDir());

				OutputValues output = optimiser.initialiseOptimisation(converted_json);

				writeInitialiseEstimatesToForm(output);

				// Convert the InputValues struct to a JSON object using the mapping
				nlohmann::json jsonObj = outputToJson(output);

				// Write the JSON to a file
				writeJsonToFile(jsonObj, fileConfig.getOutputJsonInitFilepath());
				std::cout << "JSON file written successfully!" << std::endl;

				writeTimingsToForm(start_long);

				std::cout << "Sleeping for 1 seconds..."; // this allows time to read the console if needed. Adjust if needed
				//std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n'); // Clear the input buffer
				//std::cin.get(); // Wait for keystroke

				std::this_thread::sleep_for(std::chrono::seconds(1));

			}
			CloseConsole();
			break;

		case BUTTON_RECALL: // this is the RECALL button to recall a parameter slice by index
			if (wmEvent == BN_CLICKED) {
				InitConsole();
				InputValues inputValues = readInputFromForm();

				auto converted_json = handleJsonConversion(inputValues, fileConfig.getInputDir());

				wchar_t buffer100[100];
				GetWindowText(hTextboxIndex, buffer100, 100);
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

