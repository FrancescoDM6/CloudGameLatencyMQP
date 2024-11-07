#include "logmanager.hpp"
#include <stdarg.h>  // For va_list, va_start, va_end

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

int LogManager::startUp()
{
    m_p_f = fopen(LOGFILE_NAME.c_str(), "a");
    if (!m_p_f)
    {
        return -1;  // Return error if file can't be opened
    }
    return 0;  // Success
}

void LogManager::shutDown()
{
    if (m_p_f)
    {
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