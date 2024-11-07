#include "logmanager.hpp"
#include <dirent.h>
#include <sstream>
#include <stdarg.h>
#include <sys/stat.h>

const std::string LogManager::LOG_DIR = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/logs/";

LogManager::LogManager() : m_do_flush(true) {}

LogManager::~LogManager()
{
    shutDown();
}

std::string LogManager::getLogPrefix(LogType type) const
{
    switch(type) {
        case LogType::CAR_DATA:
            return "cardata_";
        case LogType::AI_DATA:
            return "aidata_";
        case LogType::LAP_TIME:
            return "laptime_";
        default:
            return "unknown_";
    }
}

std::string LogManager::generateLogFileName(LogType type, int number) const
{
    std::ostringstream oss;
    oss << LOG_DIR << getLogPrefix(type) << number << ".log";
    return oss.str();
}

int LogManager::startUp()
{
    // Create directory if it doesn't exist
    mkdir(LOG_DIR.c_str(), 0777);

    // Initialize all log files
    for (int i = 0; i < 3; i++) {  // Assuming 3 LogTypes
        LogType type = static_cast<LogType>(i);
        int nextNumber = findNextLogNumber(type);
        std::string filename = generateLogFileName(type, nextNumber);
        FILE* file = fopen(filename.c_str(), "w");
        if (!file) {
            return -1;
        }
        m_files[type] = file;
    }
    return 0;
}

void LogManager::shutDown()
{
    for (auto& pair : m_files) {
        if (pair.second) {
            fclose(pair.second);
        }
    }
    m_files.clear();
}

int LogManager::writeLog(LogType type, const char* fmt, ...) const
{
    auto it = m_files.find(type);
    if (it == m_files.end() || !it->second) {
        return -1;
    }

    va_list args;
    va_start(args, fmt);
    int bytes_written = vfprintf(it->second, fmt, args);
    va_end(args);

    if (m_do_flush) {
        fflush(it->second);
    }

    return bytes_written;
} 