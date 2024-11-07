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
        CAR_DATA,
        AI_DATA,
        LAP_TIME,
        // Add more types as needed
    };

    // Delete copy constructor and assignment operator
    LogManager(const LogManager&) = delete;
    LogManager& operator=(const LogManager&) = delete;

    // Get singleton instance
    static LogManager& getInstance();

    // Initialize logging system
    int startUp();

    // Shutdown logging system
    void shutDown();

    // Set whether to flush after each write
    void setFlush(bool do_flush);

    // Write to specific log file with printf-style formatting
    int writeLog(LogType type, const char* fmt, ...) const;

private:
    LogManager();
    ~LogManager();
    
    // Find next available log number for a specific type
    int findNextLogNumber(LogType type) const;
    std::string generateLogFileName(LogType type, int number) const;
    std::string getLogPrefix(LogType type) const;

    bool m_do_flush;
    std::map<LogType, FILE*> m_files;  // Map to store multiple file pointers
    static const std::string LOG_DIR;
};

#endif // LOGMANAGER_HPP
