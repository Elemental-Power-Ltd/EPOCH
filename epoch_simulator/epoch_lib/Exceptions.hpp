#pragma once

#include <stdexcept>
#include <string>

class FileReadException : public std::runtime_error {
public:
    FileReadException(const std::string& filename)
        : std::runtime_error("Failed to read from file: " + filename) {}
};

class FileWriteException : public std::runtime_error {
public:
    FileWriteException(const std::string& filename)
        : std::runtime_error("Failed to write to file: " + filename) {}
};