"""Utility functions for the package. Exports the logger."""

import logging
import logging.handlers
import os


class RelativePathNameFilter(logging.Filter):
    """
    A filter to include the relative pathname instead of the absolute pathname to the
    log.
    """

    def filter(self, record) -> bool:
        """
        Filters the log record to include the relative pathname.

        Parameters:
            record (logging.LogRecord): The log record.

        Returns:
            bool: True if the log record should be included, False otherwise.
        """
        if "opensurplusmanager" in record.pathname:
            record.relative_pathname = record.pathname.split("opensurplusmanager")[1]
        else:
            record.relative_pathname = record.pathname
        return True


def setup_logger() -> logging.Logger:
    """
    Setups the logger for the package. It will read the log level from the LOG_LEVEL
    environment variable and the log directory from the LOG_DIR environment variable.

    Formats the log message with the relative pathname to the log file.

    Returns:
        logging.Logger: The logger for the package.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    log_format = "[%(asctime)s] {%(relative_pathname)s:%(lineno)d} %(levelname)s \
        - %(message)s"
    date_format = "%d-%m-%Y %H:%M:%S"

    formatter = logging.Formatter(log_format, date_format)

    logger_setup = logging.getLogger()
    logger_setup.setLevel(log_level)

    log_dir = os.getenv("LOG_DIR", "./logs")
    log_file = os.path.join(log_dir, "opensurplusmanager.log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    open(log_file, "a", encoding="utf-8").close()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RelativePathNameFilter())

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=2 * 1024 * 1024, backupCount=3
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RelativePathNameFilter())

    logger_setup.addHandler(console_handler)
    logger_setup.addHandler(file_handler)

    return logger_setup


logger = setup_logger()
