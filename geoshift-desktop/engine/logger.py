import logging
import os
from datetime import datetime

def setup_logger(name='geoshift', log_dir='logs'):
    """
    Setup centralized logger for the application.
    
    Args:
        name: Logger name
        log_dir: Directory to store log files
    
    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler (detailed logs)
    log_filename = os.path.join(log_dir, f'geoshift_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler (simple logs)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create default logger instance
logger = setup_logger()
