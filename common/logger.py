import logging
from enum import IntEnum
from dataclasses import dataclass
import copy

class Level(IntEnum):
    NOTSET = logging.NOTSET # no logging
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARN
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    FATAL = logging.FATAL
    CRITICAL = logging.CRITICAL

class Logger():
    """
    Logger class for the measurement framework

    Class variables:

    :param str log_format_string: Universal logging format for all the modules using this class
    :param str filename: The file where all the logs are stored from all the modules using this class
    """

    log_format_string = '%(asctime)s [%(levelname)s]  %(name)s:    %(message)s'
    filename = "app.log"    
    
    @dataclass
    class Settings():
        """
        Settings sub-class for the Logger

        Note: when passing and modifying Settings classes multiple times, use the copy function

        :param str module_name: Name of the module using the Logger, not optional
                                this must be provided at the initialization of the new Logger
        :param str logfile_name: If provided, the Logger instance will write a separate logfile simultaneously,
                                with this name, no filename extension is required
        :param bool console_logging: Enable/disable console logging for this instance, default: True
        :param logging_level: The level of the logging messages are displayed, refer to Level class
        """
        module_name: str = None
        logfile_name: str = None
        console_logging: bool = True
        logging_level :int = Level.DEBUG
        
        def copy(self): # passing a settings object as a copy is recommended
            return copy.copy(self)
        

    def __new__(cls,settings :Settings):
        
        #Calling default basic config
        logging.basicConfig(filename=cls.filename,filemode="w",format=cls.log_format_string)
        logger = logging.getLogger(settings.module_name)
        log_formatter = logging.Formatter(fmt=cls.log_format_string)
        # optional logging to console
        if settings.console_logging:
            log_console = logging.StreamHandler()
            log_console.setFormatter(log_formatter)
            logger.addHandler(log_console)
        if settings.logfile_name is not None:
            log_file = logging.FileHandler(filename=settings.logfile_name +".log",mode='w')
            log_file.setFormatter(log_formatter)
            logger.addHandler(log_file)
        logger.setLevel(settings.logging_level)
        return logger