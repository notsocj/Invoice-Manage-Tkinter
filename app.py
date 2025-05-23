import os
import sys
import logging
from pathlib import Path
from src.controllers.main_controller import MainController
from src.models.database import Database
from src.utils.config_manager import ConfigManager
from src.utils.logger import setup_logger

def main():
    # Set up logging
    setup_logger()
    logger = logging.getLogger('invoice_manager')
    logger.info("Starting Invoice Manager application")
    
    # Create 'temp' directory if it doesn't exist
    temp_dir = os.path.join(os.getcwd(), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Load configuration
    config = ConfigManager()
    
    # Initialize database connection
    db = Database(config.get_database_uri())
    db.initialize()
    
    # Start the controller which will initialize the UI
    app = MainController(db)
    app.run()
    
    logger.info("Application closed")

if __name__ == "__main__":
    main()
