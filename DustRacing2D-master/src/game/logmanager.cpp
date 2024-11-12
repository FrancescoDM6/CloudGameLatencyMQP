#include "logmanager.hpp"
#include "timing.hpp"
#include <dirent.h>
#include <sstream>
#include <stdarg.h>
#include <sys/stat.h>
#include <chrono>
#include <ctime>

const std::string LogManager::LOG_DIR = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/logs/";

LogManager::LogManager() : m_do_flush(false) {}

LogManager::~LogManager()
{
    shutDown();
}

LogManager& LogManager::getInstance()
{
    static LogManager instance;
    return instance;
}

std::string LogManager::getLogPrefix(LogType type) const
{
    switch(type) {
        case LogType::DEFAULT:
            return "logfile_";
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

int LogManager::findNextLogNumber(LogType type) const
{
    DIR* dir = opendir(LOG_DIR.c_str());
    if (!dir)
    {
        mkdir(LOG_DIR.c_str(), 0777);
        return 1;
    }

    int maxNumber = 0;
    struct dirent* entry;
    while ((entry = readdir(dir)) != NULL)
    {
        std::string name = entry->d_name;
        std::string prefix = getLogPrefix(type);
        if (name.find(prefix) == 0)
        {
            size_t numStart = prefix.length();
            size_t numEnd = name.find(".log");
            if (numEnd != std::string::npos)
            {
                try {
                    int num = std::stoi(name.substr(numStart, numEnd - numStart));
                    if (num > maxNumber)
                        maxNumber = num;
                } catch (...) {}
            }
        }
    }
    closedir(dir);
    return maxNumber + 1;
}

std::string LogManager::generateLogFileName(LogType type, int number) const
{
    std::ostringstream oss;
    oss << LOG_DIR << getLogPrefix(type) << number << ".log";
    return oss.str();
}

int LogManager::startUp()
{
    mkdir(LOG_DIR.c_str(), 0777);

    // Initialize all log files
    for (int i = 0; i < 3; i++) {
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

void LogManager::setFlush(bool do_flush)
{
    m_do_flush = do_flush;
}

// Default logging method (uses CAR_DATA)
int LogManager::writeLog(const char* fmt, ...) const
{
    return writeLog(LogType::DEFAULT, fmt);
}

int LogManager::writeLog(LogType type, const char* fmt, ...) const
{
    auto it = m_files.find(type);
    if (it == m_files.end() || !it->second) {
        return -1;
    }

    // Get system time
    auto now = std::chrono::system_clock::now();
    std::time_t currentTime = std::chrono::system_clock::to_time_t(now);
    char timeBuffer[20];
    std::strftime(timeBuffer, sizeof(timeBuffer), "%Y-%m-%d %H:%M:%S", std::localtime(&currentTime));

    // Get in-game time (milliseconds since game start)
    int msec = TimingContext::getInstance().getElapsedTime();
    const int hr = msec % 3600000;
    const int mm = hr / 60000;
    const int mr = hr % 60000;
    const int ss = mr / 1000;
    const int ms = mr % 1000;
    
    char gameTimeBuffer[20];
    snprintf(gameTimeBuffer, sizeof(gameTimeBuffer), "%02d:%02d.%02d", mm, ss, ms / 10);

    // Write both timestamps first
    fprintf(it->second, "[SYS: %s][GAME: %s] ", timeBuffer, gameTimeBuffer);

    // Write the actual message
    va_list args;
    va_start(args, fmt);
    int bytes_written = vfprintf(it->second, fmt, args);
    va_end(args);

    if (m_do_flush) {
        fflush(it->second);
    }

    return bytes_written;
} 