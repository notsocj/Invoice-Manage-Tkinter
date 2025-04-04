import logging
import sqlite3
import threading
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

Base = declarative_base()

class Database:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance.initialized = False
            return cls._instance
    
    def __init__(self, db_uri=None):
        if not hasattr(self, 'initialized') or not self.initialized:
            self.logger = logging.getLogger('invoice_manager')
            self.db_uri = db_uri or 'sqlite:///invoice_manager.db'
            self.engine = None
            self.session_factory = None
            self.Session = None
            self.initialized = True
    
    def initialize(self):
        """Initialize the database connection and create tables if they don't exist"""
        try:
            self.logger.info(f"Initializing database with URI: {self.db_uri}")
            self.engine = create_engine(self.db_uri, echo=False)
            self.session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(self.session_factory)
            
            # Import models here to avoid circular imports
            from src.models.client_model import Client
            from src.models.invoice_model import Invoice
            from src.models.payment_model import Payment
            
            # Create all tables if they don't exist
            Base.metadata.create_all(self.engine)
            self.logger.info("Database initialized successfully")
            return True
        except SQLAlchemyError as e:
            self.logger.error(f"Database initialization error: {str(e)}")
            return False
            
    def get_session(self):
        """Get a database session"""
        if not self.Session:
            self.initialize()
        return self.Session()
    
    def close(self):
        """Close the database connection"""
        if self.Session:
            self.Session.remove()
            self.logger.info("Database connection closed")
