#ifndef __LOG_MANAGER_H__
#define __LOG_MANAGER_H__

// System includes.
#include <stdio.h>

// Engine includes.
// #include "manager.hpp"
#include <string>

// namespace df {

const std::string LOGFILE_NAME = "dragonfly.log";

class LogManager {
private:
    LogManager(); // Private since a singleton.
    LogManager(LogManager const&); // Don't allow copy.
    void operator=(LogManager const&); // Don't allow assignment.
    bool m_do_flush; // True if flush to disk after each write.
    FILE* m_p_f; // Pointer to log file struct.

public:
    // If log file is open, close it.
    ~LogManager();

    // Get the one and only instance of the LogManager.
    static LogManager& getInstance();

    // Start up the LogManager (open log file "dragonfly.log").
    int startUp();

    // Shut down the LogManager (close log file).
    void shutDown();

    // Set flush of log file after each write.
    void setFlush(bool do_flush = true);

    // Write to log file. Supports sprintf() for formatting of strings.
    // Return number of bytes written, -1 if error.
    int writeLog(const char* fmt, ...) const;
};

// } // end of namespace df

#endif // LOG_MANAGER_H
