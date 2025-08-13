# mtm_persistence.py
# Handles application startup and shutdown events.

from mtm_imports import *
from mtm_db import close_db, init_db

def load_state():
    """Initializes the database when the application starts."""
    init_db()
    logger.info("Database initialized on startup.")
    return True

def save_state():
    """Placeholder function, as data is now saved directly to the database."""
    # This function is no longer needed for saving state, as it's done in real-time.
    # It can be used for any final cleanup if necessary.
    pass

def start_auto_save():
    """This function is no longer needed as auto-save to JSON is removed."""
    logger.info("JSON auto-save is disabled. Data is saved to SQLite in real-time.")
    pass

# Register shutdown handler to close the database connection on exit
import atexit

def register_shutdown_handler():
    """Register an exit handler to properly close the database connection."""
    def on_exit():
        logger.info("Application shutting down, closing database connection...")
        close_db()
    
    atexit.register(on_exit)
    logger.info("Registered shutdown handler to close database connection.")