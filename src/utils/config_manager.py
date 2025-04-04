import json
import os
import logging
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file=None):
        self.logger = logging.getLogger('invoice_manager')
        
        if config_file:
            self.config_file = config_file
        else:
            # Default config file location
            config_dir = Path.cwd() / 'config'
            config_dir.mkdir(exist_ok=True)
            self.config_file = config_dir / 'config.json'
        
        # Default configuration
        self.config = {
            'database': {
                'type': 'sqlite',
                'path': 'invoice_manager.db',
                'host': 'localhost',
                'port': 3306,
                'name': 'invoice_manager',
                'user': 'root',
                'password': ''
            },
            'appearance': {
                'theme': 'blue',
                'mode': 'system'
            },
            'business': {
                'name': 'Your Business',
                'address': '',
                'city': '',
                'state': '',
                'zip': '',
                'phone': '',
                'email': '',
                'website': '',
                'logo': ''
            },
            'invoice': {
                'due_days': 30,
                'tax_rate': 0.0,
                'default_commission_rate': 0.0
            }
        }
        
        # Load configuration from file or create default
        self.load()
    
    def load(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Update config with loaded values
                    self._update_dict_recursive(self.config, loaded_config)
                    self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                # Save default configuration
                self.save()
                self.logger.info(f"Default configuration created at {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
    
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
                self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
    
    def get(self, section, key=None):
        """Get configuration value"""
        try:
            if key:
                return self.config.get(section, {}).get(key)
            return self.config.get(section, {})
        except Exception as e:
            self.logger.error(f"Error getting configuration: {str(e)}")
            return None
    
    def set(self, section, key, value):
        """Set configuration value"""
        try:
            if section not in self.config:
                self.config[section] = {}
            self.config[section][key] = value
            self.save()
            self.logger.info(f"Configuration updated: {section}.{key}")
        except Exception as e:
            self.logger.error(f"Error setting configuration: {str(e)}")
    
    def get_database_uri(self):
        """Get database URI based on configuration"""
        db_config = self.config['database']
        db_type = db_config['type']
        
        if db_type == 'sqlite':
            # SQLite connection - file-based
            db_path = os.path.join(os.getcwd(), db_config['path'])
            return f"sqlite:///{db_path}"
        elif db_type == 'mysql':
            # MySQL connection
            host = db_config['host']
            port = db_config['port']
            name = db_config['name']
            user = db_config['user']
            password = db_config['password']
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
        else:
            self.logger.error(f"Unsupported database type: {db_type}")
            # Default to SQLite
            return "sqlite:///invoice_manager.db"
    
    def _update_dict_recursive(self, d, u):
        """Update dictionary recursively"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_dict_recursive(d[k], v)
            else:
                d[k] = v
