#include "BufferedCSVWriter.hpp"
#include <limits>

BufferedCSVWriter::BufferedCSVWriter(std::filesystem::path filepath)
	: mFilepath(filepath),
	mResultsBuffer(),
	mMutex()
{
	mResultsBuffer.reserve(BUFFER_CAPACITY);

	std::ofstream outFile(filepath);

	if (!outFile.is_open()) {
		spdlog::error("Failed to open the output file!");
		throw FileWriteException(filepath.filename().string());
	}

	// write the column headers
	writeObjectiveResultHeader(outFile);
}

BufferedCSVWriter::~BufferedCSVWriter()
{
	// always flush the buffer in the destructor
	flushBuffer();
}

void BufferedCSVWriter::writeResult(const ObjectiveResult & result)
{
	std::lock_guard<std::mutex> guard(mMutex);
	if (mResultsBuffer.size() >= BUFFER_CAPACITY) {
		flushBuffer();
	}

	mResultsBuffer.emplace_back(result);
	
}

void BufferedCSVWriter::flushBuffer()
{
	// open the file in append mode
	std::ofstream outFile(mFilepath, std::ios::app);

	outFile << std::fixed;
	outFile << std::setprecision(std::numeric_limits<float>::digits10 + 1);

	if (!outFile.is_open()) {
		spdlog::error("Failed to open the output file!");
		throw FileReadException(mFilepath.filename().string());
	}

	// write all of the results
	for (const auto& result : mResultsBuffer) {
		writeObjectiveResultRow(outFile, result);
	}

	// empty the buffer
	mResultsBuffer = {};
}

