import logging
import sqlite3
import threading
import os
from sqlalchemy import create_engine, inspect, text
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
            from src.models.item_model import Item
            
            # Check if the database exists and has the required schema
            self._check_and_update_schema()
            
            # Create all tables if they don't exist
            Base.metadata.create_all(self.engine)
            self.logger.info("Database initialized successfully")
            return True
        except SQLAlchemyError as e:
            self.logger.error(f"Database initialization error: {str(e)}")
            return False
    
    def _check_and_update_schema(self):
        """Check if database schema needs updates and apply them"""
        self.logger.info("Checking database schema for updates")
        inspector = inspect(self.engine)
        
        # Check clients table for missing columns
        if inspector.has_table('clients'):
            columns = [col['name'] for col in inspector.get_columns('clients')]
            
            # Add mobile column if phone exists but mobile doesn't
            if 'phone' in columns and 'mobile' not in columns:
                self.logger.info("Adding mobile column to clients table")
                self._execute_sql("ALTER TABLE clients ADD COLUMN mobile STRING")
                # Copy data from phone to mobile for existing records
                self._execute_sql("UPDATE clients SET mobile = phone WHERE mobile IS NULL")
            
            # Check for missing payment_terms column
            if 'payment_terms' not in columns:
                self.logger.info("Adding payment_terms column to clients table")
                self._execute_sql("ALTER TABLE clients ADD COLUMN payment_terms INTEGER DEFAULT 30")
            
            # Check for missing credit_limit column
            if 'credit_limit' not in columns:
                self.logger.info("Adding credit_limit column to clients table")
                self._execute_sql("ALTER TABLE clients ADD COLUMN credit_limit FLOAT DEFAULT 0.0")
        
        # Check if items table has the correct structure
        # The table will be created if it doesn't exist, but we check for updates
        if inspector.has_table('items'):
            columns = [col['name'] for col in inspector.get_columns('items')]
            
            # Check for missing item_code column (in case created with older version)
            if 'item_code' not in columns:
                self.logger.info("Adding item_code column to items table")
                self._execute_sql("ALTER TABLE items ADD COLUMN item_code STRING")
                
            # Check for missing date_added column
            if 'date_added' not in columns:
                self.logger.info("Adding date_added column to items table")
                self._execute_sql("ALTER TABLE items ADD COLUMN date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    
    def _execute_sql(self, sql_statement):
        """Execute a raw SQL statement"""
        try:
            with self.engine.connect() as connection:
                connection.execute(text(sql_statement))
                connection.commit()
            return True
        except SQLAlchemyError as e:
            self.logger.error(f"Error executing SQL: {str(e)}")
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
