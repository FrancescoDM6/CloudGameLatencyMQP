#ifndef LOGMANAGER_HPP
#define LOGMANAGER_HPP

#include <string>
#include <cstdio>

class LogManager
{
public:
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

    // Write to log file with printf-style formatting
    int writeLog(const char* fmt, ...) const;

private:
    LogManager();
    ~LogManager();
    
    // Find next available log number
    int findNextLogNumber() const;
    std::string generateLogFileName(int number) const;

    bool m_do_flush;
    FILE* m_p_f;
    static const std::string LOG_DIR;
    static const std::string LOG_PREFIX;
    static const std::string LOG_EXTENSION;
};

#endif // LOGMANAGER_HPP
