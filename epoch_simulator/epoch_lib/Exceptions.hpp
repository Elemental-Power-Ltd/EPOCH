#pragma once

#include <stdexcept>
#include <string>

// Base class for custom exceptions
class EpochBaseException : public std::runtime_error {
public:
    explicit EpochBaseException(const std::string& msg) : std::runtime_error(msg) {}
};

class FileReadException : public EpochBaseException {
public:
    explicit FileReadException(const std::string& filename)
        : EpochBaseException("Failed to read from file: " + filename) {}
};

class FileWriteException : public EpochBaseException {
public:
    explicit FileWriteException(const std::string& filename)
        : EpochBaseException("Failed to write to file: " + filename) {}
};

class ConfigException : public EpochBaseException {
public:
    explicit ConfigException(const std::string& msg)
        : EpochBaseException(msg) {}
};
