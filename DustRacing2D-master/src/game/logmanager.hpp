#ifndef LOGMANAGER_HPP
#define LOGMANAGER_HPP

#include <string>
#include <cstdio>
#include <map>

class LogManager
{
public:
    // Enum for different log types
    enum class LogType {
        DEFAULT,
        CAR_DATA,
        AI_DATA,
        LAP_TIME
    };

    LogManager(const LogManager&) = delete;
    LogManager& operator=(const LogManager&) = delete;

    static LogManager& getInstance();
    int startUp();
    void shutDown();
    void setFlush(bool do_flush);
    
    // Default write method (uses CAR_DATA type)
    int writeLog(const char* fmt, ...) const;
    // Specific log type write method
    int writeLog(LogType type, const char* fmt, ...) const;

private:
    LogManager();
    ~LogManager();
    
    int findNextLogNumber(LogType type) const;
    std::string generateLogFileName(LogType type, int number) const;
    std::string getLogPrefix(LogType type) const;

    bool m_do_flush;
    std::map<LogType, FILE*> m_files;
    static const std::string LOG_DIR;
};

#endif // LOGMANAGER_HPP
