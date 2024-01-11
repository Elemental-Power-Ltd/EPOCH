#pragma once
#include "EP_main.h"

#ifdef EP_GUI
// run with the gui

#define NOMINMAX  // necessary before including windows.h
#include <windows.h>

#include "../EP_main/GUI/gui.hpp"


int APIENTRY wWinMain(_In_ HINSTANCE hInstance,
	_In_opt_ HINSTANCE hPrevInstance,
	_In_ LPWSTR    lpCmdLine,
	_In_ int       nCmdShow)
{
	UNREFERENCED_PARAMETER(hPrevInstance);
	UNREFERENCED_PARAMETER(lpCmdLine);

	// Initialize global strings
	LoadStringW(hInstance, IDS_APP_TITLE, szTitle, MAX_LOADSTRING);
	LoadStringW(hInstance, IDC_EPMAIN, szWindowClass, MAX_LOADSTRING);
	MyRegisterClass(hInstance);

	// Perform application initialization:
	if (!InitInstance(hInstance, nCmdShow))
	{
		return FALSE;
	}

	HACCEL hAccelTable = LoadAccelerators(hInstance, MAKEINTRESOURCE(IDC_EPMAIN));

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
#include "../EP/Optimisation/Optimiser.hpp"
#include "../EP/io/FileHandling.hpp"


int main(int argc, char* argv[]) {

	std::cout << "Running in headless mode" << std::endl;

	FileConfig fileConfig{};
	auto converted_json = handleJsonConversion(defaultInput, fileConfig.getInputDir());

	std::cout << "Starting Optimisation" << std::endl;

	auto optimiser = Optimiser(fileConfig);
	OutputValues output = optimiser.runMainOptimisation(converted_json);

	std::cout << "Finished Optimisation" << std::endl;

	nlohmann::json jsonObj = outputToJson(output);
	writeJsonToFile(jsonObj, fileConfig.getOutputJsonFilepath());

	std::cout << "Wrote results to file" << std::endl;

}

#endif