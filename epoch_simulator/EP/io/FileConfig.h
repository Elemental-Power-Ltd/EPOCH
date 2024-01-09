
#pragma once

#include <string>
#include <filesystem>

class FileConfig
{
public: 
    FileConfig(
        std::filesystem::path rootDir = "",
        std::filesystem::path inputDir = "InputData",
        std::filesystem::path outputDir = "OutputData",

        std::filesystem::path eloadFilename = "CSVEload.csv",
        std::filesystem::path hloadFilename = "CSVHload.csv",
        std::filesystem::path rgenFilename = "CSVRGen.csv",

        std::filesystem::path resultsFilename = "EP_Results.csv",
        std::filesystem::path outputJsonFilename = "outputparameters.json",
        std::filesystem::path outputJsonInitFilename = "outputparameters_init.json"
    )
        : rootDir(rootDir),
        inputDir(inputDir),
        outputDir(outputDir),
        eloadFilename(eloadFilename),
        hloadFilename(hloadFilename),
        rgenFilename(rgenFilename),
        resultsFilename(resultsFilename),
        outputJsonFilename(outputJsonFilename),
        outputJsonInitFilename(outputJsonInitFilename)
    {
        // create the output directory if it doesn't already exist
        std::filesystem::path outputPath = rootDir / outputDir;

        // deliberately choose not to try-catch this here as we want to fail if we can't write any output
        std::filesystem::create_directories(outputPath);
    } 

    // all files are stored in either the inputDir or outputDir subdirectory
    // so the full filepath will be:
    //      rootDirectory / subdirectory / filepath

    std::filesystem::path getEloadFilepath() {
        return rootDir / inputDir / eloadFilename;
    }

    std::filesystem::path getHloadFilepath() {
        return rootDir / inputDir / hloadFilename;
    }

    std::filesystem::path getRgenFilepath() {
        return rootDir / inputDir / rgenFilename;
    }

    std::filesystem::path getOutputCSVFilepath() {
        return rootDir / outputDir / resultsFilename;
    }

    std::filesystem::path getOutputJsonFilepath() {
        return rootDir / outputDir / outputJsonFilename;
    }

    std::filesystem::path getOutputJsonInitFilepath() {
        return rootDir / outputDir / outputJsonInitFilename;
    }

    std::filesystem::path getInputDir() {
        return rootDir / inputDir;
    }

    std::filesystem::path getOutputDir() {
        return rootDir / outputDir;
    }

private:
    std::filesystem::path rootDir;
    std::filesystem::path inputDir;
    std::filesystem::path outputDir;

    std::filesystem::path eloadFilename;
    std::filesystem::path hloadFilename;
    std::filesystem::path rgenFilename;

    std::filesystem::path resultsFilename;

    // The output JSON from runMainOptimisation
    std::filesystem::path outputJsonFilename;
    // The output JSON from initialiseOptimisation
    std::filesystem::path outputJsonInitFilename;
};