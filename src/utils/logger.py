import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logger():
    """Set up the application logger"""
    # Create logs directory if it doesn't exist
    logs_dir = Path.cwd() / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Create a log file with current date
    log_filename = f"invoice_manager_{datetime.now().strftime('%Y%m%d')}.log"
    log_path = logs_dir / log_filename
    
    # Configure the root logger
    logger = logging.getLogger('invoice_manager')
    logger.setLevel(logging.DEBUG)
    
    # Create a file handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
