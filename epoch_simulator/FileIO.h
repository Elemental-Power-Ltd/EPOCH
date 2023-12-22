
#pragma once
#include <string>

class FileIO
{
public: 
    FileIO(
        std::string longfilepath = "",//"C:/Users/splb2/OneDrive/Documents/Self employment/Consultancy/RHS Holosphere Corfe/Elemental Power/Solar PV MVP/C++ Backend Sep 23/EP_FE_full",
        std::string eloadfilename = "CSVEload.csv",
        std::string hloadfilename = "CSVHload.csv",
        std::string rgenfilename = "CSVRGen.csv",
        std::string outfilename = "EP_BE_out_parallel.csv")
        : longfilepath(longfilepath),
        eloadfilename(eloadfilename),
        hloadfilename(hloadfilename),
        rgenfilename(rgenfilename),
        outfilename(outfilename) {} 

    // member function to concatenate strings
    std::string concatenateStrings(const std::string& str1, const std::string& str2) {
        return str1 + str2;
    }

    // accessor member functions 
    std::string getEloadfilepath() {
        abspath = concatenateStrings(longfilepath, eloadfilename);
        return abspath;
    }

    std::string getHloadfilepath() {
        abspath = concatenateStrings(longfilepath, hloadfilename);
        return abspath;
    }

    std::string getRgenfilepath() {
        abspath = concatenateStrings(longfilepath, rgenfilename);
        return abspath;
    }

    std::string getOutfilepath() {
        abspath = concatenateStrings(longfilepath, outfilename);
        return abspath;
    }

private:
    std::string longfilepath;
    std::string eloadfilename;
    std::string hloadfilename;
    std::string rgenfilename;
    std::string outfilename;
    std::string abspath;  // Added this declaration
};