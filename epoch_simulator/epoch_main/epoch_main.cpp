#pragma once
#include "epoch_main.h"

#ifdef EPOCH_GUI
// run with the gui

#define NOMINMAX  // necessary before including windows.h
#include <windows.h>

#include "../epoch_main/GUI/gui.hpp"


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
#include "../epoch_lib/Optimisation/Optimiser.hpp"
#include "../epoch_lib/io/FileHandling.hpp"

#include <filesystem>

int main(int argc, char* argv[]) {

	std::string inputDataPath;
	if (argc < 2) {
		spdlog::warn("Missing argument: InputData path - implicitly using the current directory");
		spdlog::info("Usage: epoch.exe path_to_input_data");
		inputDataPath = "./";
	} else {
		inputDataPath = argv[1];
	}

	try {
		FileConfig fileConfig{inputDataPath};

		auto converted_json = readJsonFromFile(fileConfig.getInputJsonFilepath());

		auto optimiser = Optimiser(fileConfig);
		OutputValues output = optimiser.runMainOptimisation(converted_json);

		nlohmann::json jsonObj = outputToJson(output);
		writeJsonToFile(jsonObj, fileConfig.getOutputJsonFilepath());

	}
	catch (const std::exception& e) {
		spdlog::error(e.what());
		return 1;
	}
}

#endif