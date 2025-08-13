# mtm_persistence_stabilized.py
# Optimized application startup and shutdown events with improved performance

import atexit
import signal
import sys
import time
import threading
from mtm_imports import *
from mtm_db_stabilized import init_db, cleanup_old_history
from mtm_cache_stabilized import cleanup_cache
from mtm_background_stabilized import cleanup_background

class ApplicationManager:
    """Manages application lifecycle with proper cleanup"""
    
    def __init__(self):
        self._initialized = False
        self._shutdown_handlers = []
        self._setup_signal_handlers()
    
    def initialize(self):
        """Initialize the application"""
        try:
            if self._initialized:
                logger.warning("Application already initialized")
                return True
            
            # Initialize database
            from mtm_db_stabilized import db_manager
            logger.info("Database initialized on startup.")
            
            # Register shutdown handlers
            self._register_shutdown_handlers()
            
            self._initialized = True
            logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
            return False
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()
            sys.exit(0)
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except Exception as e:
            logger.warning(f"Could not setup signal handlers: {str(e)}")
    
    def _register_shutdown_handlers(self):
        """Register shutdown handlers"""
        def shutdown_handler():
            self.shutdown()
        
        atexit.register(shutdown_handler)
        logger.info("Registered shutdown handlers")
    
    def add_shutdown_handler(self, handler):
        """Add a custom shutdown handler"""
        self._shutdown_handlers.append(handler)
    
    def shutdown(self):
        """Perform graceful shutdown"""
        if not self._initialized:
            return
        
        logger.info("Starting application shutdown...")
        
        # Run custom shutdown handlers
        for handler in self._shutdown_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error in shutdown handler: {str(e)}", exc_info=True)
        
        # Cleanup background resources
        try:
            cleanup_background()
        except Exception as e:
            logger.error(f"Error cleaning up background resources: {str(e)}", exc_info=True)
        
        # Cleanup cache
        try:
            cleanup_cache()
        except Exception as e:
            logger.error(f"Error cleaning up cache: {str(e)}", exc_info=True)
        
        # Cleanup database
        try:
            cleanup_old_history(days_to_keep=7)
        except Exception as e:
            logger.error(f"Error cleaning up database: {str(e)}", exc_info=True)
        
        logger.info("Application shutdown completed")

# Global application manager
app_manager = ApplicationManager()

def load_state():
    """Initializes the database when the application starts with optimized settings."""
    try:
        init_db()
        
        # Clean up old history data on startup to prevent database bloat
        cleanup_old_history(days_to_keep=7)
        
        logger.info("Database initialized on startup with optimized settings.")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        return False

def save_state():
    """Optimized state saving - now handled by batch processing in cache."""
    # State is now saved automatically through batch processing
    # This function is kept for compatibility
    pass

def start_auto_save():
    """Optimized auto-save functionality."""
    logger.info("Auto-save is now handled by batch processing for better performance.")
    
    # Start periodic cleanup of old data
    def cleanup_worker():
        while True:
            try:
                time.sleep(3600)  # Run every hour
                cleanup_old_history(days_to_keep=7)
            except Exception as e:
                logger.error(f"Error in cleanup worker: {str(e)}", exc_info=True)
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    logger.info("Periodic cleanup worker started")

def register_shutdown_handler():
    """Register an exit handler to properly clean up resources."""
    def on_exit():
        logger.info("Application shutting down, cleaning up resources...")
        
        # Clean up background tasks
        try:
            from mtm_background_stabilized import cleanup_background_tasks
            cleanup_background_tasks()
        except Exception as e:
            logger.error(f"Error cleaning up background tasks: {str(e)}")
        
        # Process any remaining batch updates
        try:
            from mtm_cache_stabilized import process_batch_updates
            process_batch_updates()
        except Exception as e:
            logger.error(f"Error processing final batch updates: {str(e)}")
        
        logger.info("Application shutdown cleanup completed.")
    
    atexit.register(on_exit)
    logger.info("Registered optimized shutdown handler.")

def add_custom_shutdown_handler(handler):
    """Add a custom shutdown handler"""
    app_manager.add_shutdown_handler(handler)

def force_shutdown():
    """Force shutdown the application"""
    app_manager.shutdown()

# Legacy functions for compatibility
def cleanup_on_exit():
    """Legacy cleanup function"""
    app_manager.shutdown() 