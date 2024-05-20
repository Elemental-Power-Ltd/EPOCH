
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
        : inputDir(inputDir),
        outputDir(outputDir),
        configDir(configDir),
        eloadFilename("CSVEload.csv"),
        hloadFilename("CSVHload.csv"),
        rgenFilename("CSVRGen.csv"),
        airtempFilename("CSVAirtemp.csv"),
        importtariffFilename("CSVImporttariff.csv"),
        gridCO2Filename("CSVGridCO2.csv"),
        ASHPinputFilename("CSVASHPinput.csv"),
        ASHPoutputFilename("CSVASHPoutput.csv"),
      
        inputParameters("inputParameters.json"),
        resultsFilename("AllResults.csv"),
        outputJsonFilename("outputParameters.json"),
        outputJsonInitFilename("outputParameters_fromInitialise.json")
    
    {
        createOutputDir(outputDir);
    }

    // Constructor providing full control of all directories and filenames
    FileConfig(
        std::filesystem::path inputDir,
        std::filesystem::path outputDir,
        std::filesystem::path configDir,

        std::filesystem::path eloadFilename,
        std::filesystem::path hloadFilename,
        std::filesystem::path rgenFilename,

        std::filesystem::path airtempFilename,
        std::filesystem::path importtariffFilename,
        std::filesystem::path gridCO2Filename,
        std::filesystem::path ASHPinputFilename,
        std::filesystem::path ASHPoutputFilename,

        std::filesystem::path inputParameters,
        std::filesystem::path resultsFilename,
        std::filesystem::path outputJsonFilename,
        std::filesystem::path outputJsonInitFilename
    )
        : inputDir(inputDir),
        outputDir(outputDir),
        configDir(configDir),
        eloadFilename(eloadFilename),
        hloadFilename(hloadFilename),
        rgenFilename(rgenFilename),
        airtempFilename(airtempFilename),
        importtariffFilename(importtariffFilename),
        gridCO2Filename(gridCO2Filename),
        ASHPinputFilename(ASHPinputFilename),
        ASHPoutputFilename(ASHPoutputFilename),

        inputParameters(inputParameters),
        resultsFilename(resultsFilename),
        outputJsonFilename(outputJsonFilename),
        outputJsonInitFilename(outputJsonInitFilename)
    {
        createOutputDir(outputDir);
    }

    void createOutputDir(std::filesystem::path outputDir) const {
        // create the output directory if it doesn't already exist
        try {
            std::filesystem::create_directories(outputDir);
        }
        catch (const std::exception& e) {
            throw std::runtime_error("Failed to create Output Directory");
        }
    }

    // all files will be in one of the InputData, OutputData or ConfigData directories
    // These functions return the full paths to the desired file

    std::filesystem::path getEloadFilepath() const {
        return inputDir / eloadFilename;
    }

    std::filesystem::path getHloadFilepath() const {
        return inputDir / hloadFilename;
    }

    std::filesystem::path getRgenFilepath() const {
        return inputDir / rgenFilename;
    }

    std::filesystem::path getAirtempFilepath() const {
        return inputDir / airtempFilename;
    }

    std::filesystem::path getImporttariffFilepath() const {
        return inputDir / importtariffFilename;
    }

    std::filesystem::path getGridCO2Filepath() const {
        return inputDir / gridCO2Filename;
    }

    std::filesystem::path getASHPinputFilepath() const {
        return inputDir / ASHPinputFilename;
    }

    std::filesystem::path getASHPoutputFilepath() const {
        return inputDir / ASHPoutputFilename;
    }

    std::filesystem::path getInputJsonFilepath() const {
        return inputDir / inputParameters;
    }

    std::filesystem::path getOutputCSVFilepath() const {
        return outputDir / resultsFilename;
    }

    std::filesystem::path getOutputJsonFilepath() const {
        return outputDir / outputJsonFilename;
    }

    std::filesystem::path getOutputJsonInitFilepath() const {
        return outputDir / outputJsonInitFilename;
    }

    // for more fine-grained controlled, get the directory
    // and then choose the filename at the call site
    std::filesystem::path getInputDir() const {
        return inputDir;
    }

    std::filesystem::path getOutputDir() const {
        return outputDir;
    }

    std::filesystem::path getConfigDir() const {
        return configDir;
    }

private:
    std::filesystem::path inputDir;
    std::filesystem::path outputDir;
    std::filesystem::path configDir;

    // inputDir files
    std::filesystem::path eloadFilename;
    std::filesystem::path hloadFilename;
    std::filesystem::path rgenFilename;

    std::filesystem::path airtempFilename;
    std::filesystem::path importtariffFilename;
    std::filesystem::path gridCO2Filename;
    std::filesystem::path ASHPinputFilename;
    std::filesystem::path ASHPoutputFilename;

    std::filesystem::path inputParameters;

    // outputDir files
    std::filesystem::path resultsFilename;
    // The output JSON from runMainOptimisation
    std::filesystem::path outputJsonFilename;
    // The output JSON from initialiseOptimisation
    std::filesystem::path outputJsonInitFilename;

    // configDir files
};