"""
YAML logger utility for LSL.

This module provides a YAML-formatted logger for both server and client
components of LSL, with support for log rotation and structured logging.
"""
import os
import sys
import yaml
import logging
import logging.handlers
import datetime
from typing import Dict, Optional, Any, Union

# Dictionary to store loggers by name
_loggers = {}

class YAMLFormatter(logging.Formatter):
    """
    Custom formatter that formats log messages as YAML documents.
    Each log entry is a separate YAML document with structured fields.
    """
    
    def __init__(self):
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as a YAML document.
        
        Args:
            record (logging.LogRecord): The log record to format
            
        Returns:
            str: YAML-formatted log entry
        """
        # Create a dictionary with standard log fields
        log_dict = {
            'timestamp': datetime.datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
        }
        
        # Add source location information
        if record.pathname and record.lineno:
            log_dict['source'] = {
                'file': os.path.basename(record.pathname),
                'line': record.lineno,
                'function': record.funcName
            }
        
        # Add exception info if present
        if record.exc_info:
            exception_type, exception_value, _ = record.exc_info
            log_dict['exception'] = {
                'type': exception_type.__name__,
                'message': str(exception_value)
            }
            
        # Add any extra attributes from the record
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            for key, value in record.extra.items():
                if key not in log_dict:
                    log_dict[key] = value
        
        # Convert to YAML and add document separator
        yaml_text = yaml.dump(log_dict, default_flow_style=False, sort_keys=False)
        return '---\n' + yaml_text


class YAMLLogger(logging.Logger):
    """
    Custom logger class that extends standard Logger to add extra context to logs.
    """
    
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, **kwargs):
        """
        Override _log to support passing extra context via keyword arguments.
        
        Args:
            level: The logging level
            msg: The log message
            args: Message formatting arguments
            exc_info: Exception information
            extra: Extra context as a dictionary
            stack_info: Include stack information
            **kwargs: Additional keyword arguments treated as extra context
        """
        # Merge kwargs into extra dict if provided
        if kwargs:
            if extra is None:
                extra = {'extra': kwargs}
            else:
                if 'extra' not in extra:
                    extra['extra'] = kwargs
                else:
                    extra['extra'].update(kwargs)
                
        super()._log(level, msg, args, exc_info, extra, stack_info)


def setup_logger(name: str, log_file: str, level: int = logging.DEBUG, 
                 max_size: int = 10 * 1024 * 1024, backup_count: int = 5) -> logging.Logger:
    """
    Set up a logger with YAML formatting and file rotation.
    
    Args:
        name (str): Name of the logger
        log_file (str): Path to the log file
        level (int, optional): Logging level. Defaults to logging.DEBUG.
        max_size (int, optional): Maximum log file size before rotation in bytes. 
                                  Defaults to 10MB.
        backup_count (int, optional): Number of backup files to keep. Defaults to 5.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Register the custom logger class
    logging.setLoggerClass(YAMLLogger)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Check if we've already configured this logger
    if logger.handlers:
        return logger
    
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create formatter
    formatter = YAMLFormatter()
    
    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Store the logger for future reference
    _loggers[name] = logger
    
    return logger


def get_logger(name: str, log_file: Optional[str] = None, 
               level: int = logging.DEBUG) -> logging.Logger:
    """
    Get a logger by name, creating it if necessary.
    
    Args:
        name (str): Name of the logger
        log_file (Optional[str], optional): Path to the log file if creating a new logger.
                                            Ignored if the logger already exists.
        level (int, optional): Logging level for new loggers. Defaults to logging.DEBUG.
        
    Returns:
        logging.Logger: The requested logger
        
    Raises:
        ValueError: If the logger doesn't exist and log_file is not provided
    """
    # Return existing logger if available
    if name in _loggers:
        return _loggers[name]
    
    # Create new logger if log_file is provided
    if log_file:
        return setup_logger(name, log_file, level)
    else:
        raise ValueError(f"Logger {name} not found and no log_file provided to create it")
