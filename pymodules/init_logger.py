# -*- coding: utf-8 -*-

import logging

# Set loggers
class IOManagerLogger():
    def __init__(self, logger_name, log_path):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create a formatter
        self.formatter = logging.Formatter('(%(name)s) %(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # Create a console handler and set level to debug
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(self.formatter)
        self.logger.addHandler(stream_handler)

        # Create a file handler for logging to a file
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
        
    def disable_stream_handler(self):
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                self.logger.removeHandler(handler)
                break
            
    def enable_stream_handler(self):
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                return
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(self.formatter)
        self.logger.addHandler(stream_handler)

        
if __name__ == "__main__":
    log_file_path = r"C:\workspace\test.log"  # Specify your log file path here
    logger = IOManagerLogger("IOManager", log_file_path)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
