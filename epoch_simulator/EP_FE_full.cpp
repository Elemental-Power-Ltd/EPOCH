#pragma once
#include "EP_FE_full.h"

#ifdef EP_GUI
// run with the gui

#define NOMINMAX  // necessary before including windows.h
#include <windows.h>

#include "GUI/gui.hpp"


int APIENTRY wWinMain(_In_ HINSTANCE hInstance,
	_In_opt_ HINSTANCE hPrevInstance,
	_In_ LPWSTR    lpCmdLine,
	_In_ int       nCmdShow)
{
	UNREFERENCED_PARAMETER(hPrevInstance);
	UNREFERENCED_PARAMETER(lpCmdLine);

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

#else
// run the application headlessly

#include <iostream>
#include "EP/Optimisation/Optimiser.hpp"
#include "EP/io/FileHandling.hpp"


int main(int argc, char* argv[]) {

	std::cout << "Running in headless mode";

	auto converted_json = handleJsonConversion(defaultInput);

	std::cout << "Starting Optimisation";

	Optimiser optimiser{};
	OutputValues output = optimiser.runMainOptimisation(converted_json);

	std::cout << "Finished Optimisation";

	nlohmann::json jsonObj = outputToJson(output);
	writeJsonToFile(jsonObj, "outputparameters.json");

	std::cout << "Wrote results to file";

}

#endif