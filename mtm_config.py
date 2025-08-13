# mtm_config.py
# Configuration management for the MTM Dashboard

import os
import configparser
import logging

# Default configuration values
DEFAULT_CONFIG = {
    'mtm_refresh_interval': 2000,        # 2 seconds
    'chart_update_interval': 30000,      # 30 seconds
    'cache_ttl': 0.5,                    # 0.5 seconds
    'server_port': 8556,                 # Default port
    'enable_background_scheduler': True  # Enable background scheduler
}

# Initialize empty config
config = {}

def load_config():
    """Load configuration from config.ini file with fallback to defaults"""
    global config
    
    # Start with default values
    config = DEFAULT_CONFIG.copy()
    
    # Path to config file
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    
    # Check if config file exists
    if not os.path.exists(config_path):
        logging.warning(f"Config file not found at {config_path}. Using defaults.")
        return config
    
    # Load configuration from file
    parser = configparser.ConfigParser()
    try:
        parser.read(config_path)
        
        if 'settings' in parser:
            settings = parser['settings']
            
            # Parse integer values
            for key in ['mtm_refresh_interval', 'chart_update_interval', 'server_port']:
                if key in settings:
                    try:
                        config[key] = int(settings[key])
                    except ValueError:
                        logging.warning(f"Invalid value for {key} in config.ini. Using default: {config[key]}")
            
            # Parse float values
            if 'cache_ttl' in settings:
                try:
                    config['cache_ttl'] = float(settings['cache_ttl'])
                except ValueError:
                    logging.warning(f"Invalid value for cache_ttl in config.ini. Using default: {config['cache_ttl']}")
            
            # Parse boolean values
            if 'enable_background_scheduler' in settings:
                value = settings['enable_background_scheduler'].lower()
                if value in ['true', 'yes', '1', 'on']:
                    config['enable_background_scheduler'] = True
                elif value in ['false', 'no', '0', 'off']:
                    config['enable_background_scheduler'] = False
                else:
                    logging.warning(f"Invalid value for enable_background_scheduler in config.ini. Using default: {config['enable_background_scheduler']}")
        
        logging.info(f"Loaded configuration: {config}")
        return config
        
    except Exception as e:
        logging.error(f"Error loading config file: {str(e)}")
        return config

# Load configuration on import
config = load_config()
