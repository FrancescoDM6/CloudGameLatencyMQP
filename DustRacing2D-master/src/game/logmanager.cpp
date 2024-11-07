#include "logmanager.hpp"
#include <dirent.h>
#include <sstream>
#include <stdarg.h>
#include <sys/stat.h>

const std::string LogManager::LOG_DIR = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/logs/";
const std::string LogManager::LOG_PREFIX = "cardata_";
const std::string LogManager::LOG_EXTENSION = ".log";

LogManager::LogManager() 
    : m_do_flush(false)
    , m_p_f(nullptr) 
{
}

LogManager::~LogManager()
{
    shutDown();
}

LogManager& LogManager::getInstance()
{
    static LogManager instance;
    return instance;
}

int LogManager::findNextLogNumber() const
{
    DIR* dir = opendir(LOG_DIR.c_str());
    if (!dir)
    {
        // Directory doesn't exist, create it and start with 1
        mkdir(LOG_DIR.c_str(), 0777);
        return 1;
    }

    int maxNumber = 0;
    struct dirent* entry;
    while ((entry = readdir(dir)) != NULL)
    {
        std::string name = entry->d_name;
        if (name.find(LOG_PREFIX) == 0)  // If filename starts with prefix
        {
            // Extract number from filename
            size_t numStart = LOG_PREFIX.length();
            size_t numEnd = name.find(LOG_EXTENSION);
            if (numEnd != std::string::npos)
            {
                try {
                    int num = std::stoi(name.substr(numStart, numEnd - numStart));
                    if (num > maxNumber)
                        maxNumber = num;
                } catch (...) {
                    // Ignore invalid filenames
                }
            }
        }
    }
    closedir(dir);
    return maxNumber + 1;
}

std::string LogManager::generateLogFileName(int number) const
{
    std::ostringstream oss;
    oss << LOG_DIR << LOG_PREFIX << number << LOG_EXTENSION;
    return oss.str();
}

int LogManager::startUp()
{
    if (m_p_f)
    {
        // Already started
        return 0;
    }

    int nextNumber = findNextLogNumber();
    std::string filename = generateLogFileName(nextNumber);
    m_p_f = fopen(filename.c_str(), "w");
    if (!m_p_f)
    {
        return -1;
    }

    // Write header to log file
    fprintf(m_p_f, "=== Log file #%d ===\n\n", nextNumber);
    if (m_do_flush) 
    {
        fflush(m_p_f);
    }
    return 0;
}

void LogManager::shutDown()
{
    if (m_p_f)
    {
        fprintf(m_p_f, "\n=== End of log ===\n");
        fclose(m_p_f);
        m_p_f = nullptr;
    }
}

void LogManager::setFlush(bool do_flush)
{
    m_do_flush = do_flush;
}

int LogManager::writeLog(const char* fmt, ...) const
{
    if (!m_p_f)
    {
        return -1;  // Return error if file not open
    }

    va_list args;
    va_start(args, fmt);
    int bytes_written = vfprintf(m_p_f, fmt, args);
    va_end(args);

    if (m_do_flush)
    {
        fflush(m_p_f);
    }

    return bytes_written;
} 