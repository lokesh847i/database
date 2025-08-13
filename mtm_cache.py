# mtm_cache.py
# File 2: Cache and utility functions

from mtm_imports import *
from mtm_db import (
    get_user_stats, update_user_stats_db, add_mtm_history,
    get_app_state, set_app_state, clear_history_db, reset_all_stats_db,
    get_opening_mtm as get_opening_mtm_db,
    set_opening_mtm as set_opening_mtm_db,
    is_opening_mtm_captured as is_opening_mtm_captured_db,
    reset_opening_mtm_db
)

# In-memory cache for recent data and frequently accessed information
mtm_cache = {
    "last_updated": {},  # Track last update time for API caching
    "cache_ttl": 0.5,
    "data": {},          # Cache for raw API responses from clients
    "stats": {},         # In-memory copy of stats for quick access
    "opening_mtm": {},   # In-memory copy of opening MTM values
    "opening_hour_hit": {}, # Track if opening hour fetch has been done for a user
    "time_markers": {}   # To avoid duplicate history entries for the same time interval
}

def init_user_stats(user_id: str):
    """Initialize user stats in both cache and database if not present."""
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
    """Update user stats in cache and database, and record history."""
    init_user_stats(user_id)
    
    stats = mtm_cache["stats"][user_id]
    stats["current_mtm"] = mtm_value
    
    if mtm_value > stats["max_mtm"]:
        stats["max_mtm"] = mtm_value
    if mtm_value < stats["min_mtm"]:
        stats["min_mtm"] = mtm_value
        
    # Update the database
    update_user_stats_db(user_id, stats["current_mtm"], stats["max_mtm"], stats["min_mtm"])
    
    # Append to history in the database
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    time_key = current_time[:6] + ("00" if int(current_time[6:]) < 30 else "30")
    
    if mtm_cache["time_markers"].get(user_id, {}).get(time_key) is not True:
        ts = now.strftime("%H:%M:%S")
        add_mtm_history(user_id, ts, mtm_value)
        if user_id not in mtm_cache["time_markers"]:
            mtm_cache["time_markers"][user_id] = {}
        mtm_cache["time_markers"][user_id][time_key] = True
        logger.info(f"Added history point for {user_id} at {ts}: {mtm_value}")

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
        mtm_cache["stats"] = {}
        mtm_cache["opening_mtm"] = {}
        mtm_cache["opening_hour_hit"] = {}
        mtm_cache["time_markers"] = {}
        
        logger.info("Daily reset complete.")
        return True
    return False

def load_from_db():
    """Load necessary data from the database into the in-memory cache on startup."""
    # The cache is loaded on-demand by init_user_stats and other functions.
    # This function can be used for any pre-loading if needed in the future.
    logger.info("Data will be loaded from the database on demand.")

# The reset functions below are now handled by check_daily_reset
# and the corresponding db functions. They are kept for compatibility
# in case they are called from other parts of the code, but the logic
# is now centralized in check_daily_reset.

def reset_user_stats(user_id: str):
    # This logic is now part of the daily reset
    pass

def reset_all_stats():
    # This logic is now part of the daily reset
    pass
