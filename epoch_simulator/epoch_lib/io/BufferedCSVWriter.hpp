#pragma once

#include <filesystem>
#include <fstream>
#include <mutex>

#include <spdlog/spdlog.h>

#include "FileHandling.hpp"

constexpr int BUFFER_CAPACITY = 10000;

// A class for appending/streaming results to a csv file 
// with a buffer to reduce the number of times the file must be opened
class BufferedCSVWriter {
public:
	BufferedCSVWriter(std::filesystem::path filepath);
	~BufferedCSVWriter();

	// Disallow copying and moving of this class
	BufferedCSVWriter(const BufferedCSVWriter&) = delete;
	BufferedCSVWriter& operator=(const BufferedCSVWriter&) = delete;
	BufferedCSVWriter(BufferedCSVWriter&&) = delete;
	BufferedCSVWriter& operator=(BufferedCSVWriter&&) = delete;


	void writeResult(const ObjectiveResult& result);

private:
	void flushBuffer();

	std::filesystem::path mFilepath;
	std::vector<ObjectiveResult> mResultsBuffer;
	std::mutex mMutex;
};


