# mtm_cache_stabilized.py
# Optimized cache and utility functions with improved performance

import threading
import time
from collections import OrderedDict
from mtm_imports import *
from mtm_db_stabilized import (
    get_user_stats, update_user_stats_db, add_mtm_history,
    get_app_state, set_app_state, clear_history_db, reset_all_stats_db,
    get_opening_mtm as get_opening_mtm_db,
    set_opening_mtm as set_opening_mtm_db,
    is_opening_mtm_captured as is_opening_mtm_captured_db,
    reset_opening_mtm_db
)

# Optimized in-memory cache with better performance
mtm_cache = {
    "last_updated": {},      # Track last update time for API caching
    "cache_ttl": 5.0,        # Increased to 5 seconds for better performance
    "data": {},              # Cache for raw API responses from clients
    "stats": {},             # In-memory copy of stats for quick access
    "opening_mtm": {},       # In-memory copy of opening MTM values
    "opening_hour_hit": {},  # Track if opening hour fetch has been done for a user
    "time_markers": {},      # To avoid duplicate history entries for the same time interval
    "batch_updates": {},     # Batch database updates
    "last_batch_time": 0,    # Last batch update time
    "batch_interval": 10     # Batch updates every 10 seconds
}

# Thread-safe lock for cache operations
cache_lock = threading.Lock()

def init_user_stats(user_id: str):
    """Initialize user stats in both cache and database if not present."""
    with cache_lock:
        if user_id not in mtm_cache["stats"]:
            # Try to load from DB first
            stats = get_user_stats(user_id)
            if stats:
                mtm_cache["stats"][user_id] = stats
            else:
                # Not in DB, so initialize
                mtm_cache["stats"][user_id] = {
                    "max_mtm": -float('inf'),
                    "min_mtm": float('inf'),
                    "current_mtm": 0
                }
                # Also add to DB
                update_user_stats_db(user_id, 0, -float('inf'), float('inf'))

def update_user_stats(user_id: str, mtm_value: float):
    """Update user stats in cache and queue for batch database update."""
    with cache_lock:
        init_user_stats(user_id)
        
        stats = mtm_cache["stats"][user_id]
        stats["current_mtm"] = mtm_value
        
        if mtm_value > stats["max_mtm"]:
            stats["max_mtm"] = mtm_value
        if mtm_value < stats["min_mtm"]:
            stats["min_mtm"] = mtm_value
        
        # Queue for batch update instead of immediate DB write
        mtm_cache["batch_updates"][user_id] = {
            "current_mtm": stats["current_mtm"],
            "max_mtm": stats["max_mtm"],
            "min_mtm": stats["min_mtm"]
        }
        
        # Append to history in the database (only every 30 seconds)
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        time_key = current_time[:6] + ("00" if int(current_time[6:]) < 30 else "30")
        
        if mtm_cache["time_markers"].get(user_id, {}).get(time_key) is not True:
            ts = now.strftime("%H:%M:%S")
            add_mtm_history(user_id, ts, mtm_value)
            if user_id not in mtm_cache["time_markers"]:
                mtm_cache["time_markers"][user_id] = {}
            mtm_cache["time_markers"][user_id][time_key] = True
            logger.debug(f"Added history point for {user_id} at {ts}: {mtm_value}")

def process_batch_updates():
    """Process batched database updates to reduce I/O."""
    with cache_lock:
        if not mtm_cache["batch_updates"]:
            return
        
        current_time = time.time()
        if current_time - mtm_cache["last_batch_time"] < mtm_cache["batch_interval"]:
            return
        
        # Process all batched updates
        for user_id, stats in mtm_cache["batch_updates"].items():
            update_user_stats_db(
                user_id, 
                stats["current_mtm"], 
                stats["max_mtm"], 
                stats["min_mtm"]
            )
        
        # Clear batch updates
        mtm_cache["batch_updates"] = {}
        mtm_cache["last_batch_time"] = current_time
        logger.debug(f"Processed batch updates for {len(mtm_cache['batch_updates'])} users")

def check_daily_reset():
    """Check if the date has changed and reset data if necessary."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    last_reset_date = get_app_state("last_reset_date", default=current_date)
    
    if current_date != last_reset_date:
        logger.info(f"Performing daily stats reset. Last reset: {last_reset_date}, Current date: {current_date}")
        
        # Reset data in the database
        reset_all_stats_db()
        clear_history_db()
        reset_opening_mtm_db()
        
        # Update the reset date in the database
        set_app_state("last_reset_date", current_date)
        
        # Clear in-memory caches
        with cache_lock:
            mtm_cache["stats"] = {}
            mtm_cache["opening_mtm"] = {}
            mtm_cache["opening_hour_hit"] = {}
            mtm_cache["time_markers"] = {}
            mtm_cache["batch_updates"] = {}
        
        logger.info("Daily reset complete.")
        return True
    return False

def get_cached_data(user_id: str):
    """Get cached data with thread safety."""
    with cache_lock:
        return {
            "data": mtm_cache["data"].get(user_id),
            "last_updated": mtm_cache["last_updated"].get(user_id),
            "stats": mtm_cache["stats"].get(user_id)
        }

def set_cached_data(user_id: str, data: str, stats: dict = None):
    """Set cached data with thread safety."""
    with cache_lock:
        mtm_cache["data"][user_id] = data
        mtm_cache["last_updated"][user_id] = time.time()
        if stats:
            mtm_cache["stats"][user_id] = stats

def is_cache_valid(user_id: str):
    """Check if cache is valid for a user."""
    with cache_lock:
        if user_id not in mtm_cache["last_updated"]:
            return False
        return time.time() - mtm_cache["last_updated"][user_id] < mtm_cache["cache_ttl"]

def load_from_db():
    """Load necessary data from the database into the in-memory cache on startup."""
    logger.info("Data will be loaded from the database on demand.")

# Start background batch processor
def start_batch_processor():
    """Start background thread to process batch updates."""
    def batch_worker():
        while True:
            try:
                process_batch_updates()
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in batch processor: {str(e)}", exc_info=True)
                time.sleep(5)  # Wait longer on error
    
    batch_thread = threading.Thread(target=batch_worker, daemon=True)
    batch_thread.start()
    logger.info("Batch processor started")

# Initialize batch processor
start_batch_processor() 