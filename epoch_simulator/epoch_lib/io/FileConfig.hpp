
#pragma once

#include <string>
#include <filesystem>

#include "../Exceptions.hpp"

class FileConfig
{
public: 
    // Simple Constructor allowing control of the names of the directories but not any of the files
    FileConfig(
        std::filesystem::path inputDir,
        std::filesystem::path outputDir,
        std::filesystem::path configDir
    )
        : mInputDir(inputDir),
        mOutputDir(outputDir),
        mConfigDir(configDir),
      
        inputParameters("inputParameters.json"),
        taskData("taskData.json"),
        siteData("siteData.json"),
        resultsFilename("AllResults.csv"),
        outputJsonFilename("outputParameters.json")
    {
        createOutputDir(outputDir);
    }

    void createOutputDir(std::filesystem::path outputDir) const {
        // create the output directory if it doesn't already exist
        try {
            std::filesystem::create_directories(outputDir);
        }
        catch (const std::exception&) {
            throw std::runtime_error("Failed to create Output Directory");
        }
    }

    // all files will be in one of the InputData, OutputData or ConfigData directories
    // These functions return the full paths to the desired file

    std::filesystem::path getInputJsonFilepath() const {
        return mInputDir / inputParameters;
    }

    std::filesystem::path getSiteDataFilepath() const {
        return mInputDir / siteData;
    }

    std::filesystem::path getTaskDataFilepath() const {
        return mInputDir / taskData;
    }

    std::filesystem::path getOutputCSVFilepath() const {
        return mOutputDir / resultsFilename;
    }

    std::filesystem::path getOutputJsonFilepath() const {
        return mOutputDir / outputJsonFilename;
    }

    // for more fine-grained controlled, get the directory
    // and then choose the filename at the call site
    std::filesystem::path getInputDir() const {
        return mInputDir;
    }

    std::filesystem::path getOutputDir() const {
        return mOutputDir;
    }

    std::filesystem::path getConfigDir() const {
        return mConfigDir;
    }

private:
    std::filesystem::path mInputDir;
    std::filesystem::path mOutputDir;
    std::filesystem::path mConfigDir;

    // inputDir files
    std::filesystem::path inputParameters;
    std::filesystem::path taskData;
    std::filesystem::path siteData;

    // outputDir files
    std::filesystem::path resultsFilename;
    // The output JSON from runMainOptimisation
    std::filesystem::path outputJsonFilename;

    // configDir files
};