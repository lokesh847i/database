# mtm_test.py
# Test script to simulate the behavior of MTM persistence

import json
import os
import time
from datetime import datetime

# Mock the logger
class MockLogger:
    def info(self, msg):
        print(f"INFO: {msg}")
    
    def error(self, msg, exc_info=False):
        print(f"ERROR: {msg}")

logger = MockLogger()

# Create a mock mtm_cache
mtm_cache = {
    "last_updated": {},
    "cache_ttl": 0.5,
    "data": {},
    "stats": {},
    "last_reset_date": datetime.now().strftime("%Y-%m-%d"),
    "opening_mtm": {},
    "opening_hour_hit": {},
    "history": {},
    "time_markers": {}
}

# Mock config
config = {
    "auto_save_interval": 60
}
# Persistence file
PERSISTENCE_FILE = "mtm_persistence_test.json"

# Initialize user stats
def init_user_stats(user_id):
    if user_id not in mtm_cache["stats"]:
        mtm_cache["stats"][user_id] = {
            "max_mtm": -float('inf'),
            "min_mtm": float('inf'),
            "current_mtm": 0
        }

# Update stats
def update_user_stats(user_id, mtm_value):
    init_user_stats(user_id)
    mtm_cache["stats"][user_id]["current_mtm"] = mtm_value
    if mtm_value > mtm_cache["stats"][user_id]["max_mtm"]:
        mtm_cache["stats"][user_id]["max_mtm"] = mtm_value
    if mtm_value < mtm_cache["stats"][user_id]["min_mtm"]:
        mtm_cache["stats"][user_id]["min_mtm"] = mtm_value

# Save state function
def save_state():
    """Save the current state to a file"""
    try:
        # Create a dictionary with all the data we need to persist
        state = {
            "stats": mtm_cache["stats"],
            "opening_mtm": mtm_cache["opening_mtm"],
            "opening_hour_hit": mtm_cache["opening_hour_hit"],
            "history": mtm_cache["history"],
            "time_markers": mtm_cache["time_markers"],
            "last_reset_date": mtm_cache["last_reset_date"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add a flag to indicate if we've already captured opening MTM today
        state["opening_mtm_captured"] = True
        
        # Write to file
        with open(PERSISTENCE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"State saved to {PERSISTENCE_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save state: {str(e)}")
        return False
# Load state function
def load_state():
    """Load the state from a file if it exists and is from today"""
    try:
        # Check if file exists
        if not os.path.exists(PERSISTENCE_FILE):
            logger.info(f"No persistence file found at {PERSISTENCE_FILE}")
            return False
        
        # Read the file
        with open(PERSISTENCE_FILE, 'r') as f:
            state = json.load(f)
        
        # Check if the state is from today
        last_reset_date = state.get("last_reset_date")
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        if last_reset_date != current_date:
            logger.info(f"Persistence file is from a different day ({last_reset_date}), clearing opening MTM and not using it")
            # Clear opening MTM data for the new day
            mtm_cache["opening_mtm"] = {}
            mtm_cache["opening_hour_hit"] = {}
            return False
        
        # Check if opening MTM was already captured today
        opening_mtm_captured = state.get("opening_mtm_captured", False)
        
        # Update the cache with the loaded state
        mtm_cache["stats"] = state.get("stats", {})
        
        # Only restore opening MTM if it was captured today
        if opening_mtm_captured:
            mtm_cache["opening_mtm"] = state.get("opening_mtm", {})
            mtm_cache["opening_hour_hit"] = state.get("opening_hour_hit", {})
            logger.info("Restored opening MTM values from persistence file")
        else:
            logger.info("Opening MTM not yet captured today, will capture at opening time")
        
        mtm_cache["history"] = state.get("history", {})
        mtm_cache["time_markers"] = state.get("time_markers", {})
        mtm_cache["last_reset_date"] = last_reset_date
        
        timestamp = state.get("timestamp", "unknown")
        logger.info(f"State loaded from {PERSISTENCE_FILE} (saved at {timestamp})")
        return True
    except Exception as e:
        logger.error(f"Failed to load state: {str(e)}")
        return False
# Reset user stats
def reset_user_stats(user_id):
    mtm_cache["stats"][user_id] = {
        "max_mtm": -float('inf'),
        "min_mtm": float('inf'),
        "current_mtm": mtm_cache["stats"].get(user_id, {}).get("current_mtm", 0)
    }
    # For a new day, we need to reset opening hour data
    if user_id in mtm_cache["opening_mtm"]:
        logger.info(f"Resetting opening MTM for {user_id} due to daily reset")
        mtm_cache["opening_mtm"][user_id] = 0
    if user_id in mtm_cache["opening_hour_hit"]:
        mtm_cache["opening_hour_hit"].pop(user_id)
    # Reset history for this user
    if user_id in mtm_cache["history"]:
        mtm_cache["history"][user_id] = []
    # Clear time markers
    if user_id in mtm_cache["time_markers"]:
        mtm_cache["time_markers"][user_id] = {}

# Simulate opening MTM capture
def simulate_opening_mtm_capture(user_id, mtm_value):
    logger.info(f"Simulating opening MTM capture for {user_id} with value {mtm_value}")
    mtm_cache["opening_mtm"][user_id] = mtm_value
    mtm_cache["opening_hour_hit"][user_id] = True
    save_state()
    logger.info(f"Saved state immediately after capturing opening MTM for {user_id}")

# Simulate MTM updates after opening
def simulate_mtm_updates(user_id, mtm_values):
    for i, value in enumerate(mtm_values):
        # Calculate relative to opening MTM
        opening_mtm = mtm_cache["opening_mtm"].get(user_id, 0)
        relative_mtm = value - opening_mtm
        logger.info(f"Update {i+1}: Absolute MTM={value}, Opening MTM={opening_mtm}, Relative MTM={relative_mtm}")
        update_user_stats(user_id, relative_mtm)
    
    # Save state after updates
    save_state()
# Simulate program restart
def simulate_restart():
    global mtm_cache
    
    logger.info("Simulating program restart...")
    
    # Reset cache to simulate restart
    mtm_cache = {
        "last_updated": {},
        "cache_ttl": 0.5,
        "data": {},
        "stats": {},
        "last_reset_date": datetime.now().strftime("%Y-%m-%d"),
        "opening_mtm": {},
        "opening_hour_hit": {},
        "history": {},
        "time_markers": {}
    }
    
    # Load state
    loaded = load_state()
    if loaded:
        logger.info("Successfully loaded previous state on restart")
    else:
        logger.info("No previous state loaded, starting fresh")

# Simulate new day
def simulate_new_day():
    global mtm_cache
    
    logger.info("Simulating a new day...")
    
    # Change the last reset date to yesterday to simulate a new day
    yesterday = "2024-05-24"  # Just an example date
    mtm_cache["last_reset_date"] = yesterday
    
    # Save with yesterday's date
    save_state()
    
    # Now restart and it should detect a new day
    simulate_restart()
# Run the test scenarios
def run_tests():
    # Test users
    users = ["USER1", "USER2"]
    
    # Remove test file if it exists
    if os.path.exists(PERSISTENCE_FILE):
        os.remove(PERSISTENCE_FILE)
    
    print("\n=== SCENARIO 1: Initial start, capture opening MTM ===")
    # Initial start
    logger.info("Initial program start")
    
    # Capture opening MTM for users
    simulate_opening_mtm_capture("USER1", 100.0)
    simulate_opening_mtm_capture("USER2", 200.0)
    
    # Check the state
    print("\nState after opening MTM capture:")
    print(f"USER1 opening MTM: {mtm_cache['opening_mtm'].get('USER1')}")
    print(f"USER2 opening MTM: {mtm_cache['opening_mtm'].get('USER2')}")
    
    print("\n=== SCENARIO 2: Normal MTM updates ===")
    # Update MTM values
    simulate_mtm_updates("USER1", [110.0, 90.0, 120.0])
    simulate_mtm_updates("USER2", [210.0, 190.0, 220.0])
    
    # Check min/max MTM
    print("\nState after MTM updates:")
    print(f"USER1 stats: {mtm_cache['stats'].get('USER1')}")
    print(f"USER2 stats: {mtm_cache['stats'].get('USER2')}")
        
    print("\n=== SCENARIO 3: Program restart on same day ===")
    # Simulate restart
    simulate_restart()
    
    # Check if opening MTM was restored
    print("\nState after restart:")
    print(f"USER1 opening MTM: {mtm_cache['opening_mtm'].get('USER1')}")
    print(f"USER2 opening MTM: {mtm_cache['opening_mtm'].get('USER2')}")
    print(f"USER1 stats: {mtm_cache['stats'].get('USER1')}")
    print(f"USER2 stats: {mtm_cache['stats'].get('USER2')}")
    
    # Update MTM values again to ensure they're relative to the restored opening MTM
    print("\nUpdating MTM values after restart:")
    simulate_mtm_updates("USER1", [130.0])
    simulate_mtm_updates("USER2", [230.0])
    
    print("\nState after post-restart updates:")
    print(f"USER1 stats: {mtm_cache['stats'].get('USER1')}")
    print(f"USER2 stats: {mtm_cache['stats'].get('USER2')}")
    
    print("\n=== SCENARIO 4: New day restart ===")
    # Simulate a new day
    simulate_new_day()
    
    # Check if opening MTM was cleared
    print("\nState after new day restart:")
    print(f"USER1 opening MTM: {mtm_cache['opening_mtm'].get('USER1')}")
    print(f"USER2 opening MTM: {mtm_cache['opening_mtm'].get('USER2')}")
    
    # Capture new opening MTM
    print("\nCapturing new opening MTM on new day:")
    simulate_opening_mtm_capture("USER1", 105.0)
    simulate_opening_mtm_capture("USER2", 205.0)
    
    print("\nState after new opening MTM capture:")
    print(f"USER1 opening MTM: {mtm_cache['opening_mtm'].get('USER1')}")
    print(f"USER2 opening MTM: {mtm_cache['opening_mtm'].get('USER2')}")
    
    # Cleanup
    if os.path.exists(PERSISTENCE_FILE):
        os.remove(PERSISTENCE_FILE)

if __name__ == "__main__":
    run_tests()