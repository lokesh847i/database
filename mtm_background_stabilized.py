# mtm_background_stabilized.py
# Optimized background functions with improved performance and stability

import threading
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from mtm_imports import *
from mtm_cache_stabilized import *
from mtm_server import *
import aiohttp

# Global event loop for background operations
background_loop = None
background_tasks = {}

def get_or_create_event_loop():
    """Get or create an event loop for background operations."""
    global background_loop
    if background_loop is None:
        try:
            background_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(background_loop)
        except RuntimeError:
            background_loop = asyncio.get_event_loop()
    return background_loop

# Function to fetch MTM data for a user in the background
async def fetch_user_mtm_background(user_id: str, user_ip: str):
    """Fetch MTM data for a user in the background with improved error handling."""
    try:
        full_url = f"http://{user_ip}/MTM"
        logger.debug(f"Background fetching from {full_url} for user {user_id}")
        
        # Use session for connection pooling
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(full_url, params={"UserID": user_id}) as response:
                if response.status != 200:
                    logger.warning(f"Background fetch failed for {user_id}: HTTP {response.status}")
                    return
                
                data = await response.json()
                if isinstance(data, str):
                    data = json.loads(data)
                
                # Extract MTM value
                mtm_value = float(data["response"])
                logger.debug(f"Background fetch successful for {user_id}, MTM: {mtm_value}")
                
                # Store value depending on current time
                now = datetime.now()
                current_time_str = now.strftime("%H:%M")
                current_hour, current_minute = now.hour, now.minute
                current_time_val = current_hour * 100 + current_minute
                
                # Get settings from users.json
                users_data = get_user_data()
                opening_hour = users_data.get("opening_mtm", "09:15")
                start_time = users_data.get("start_time", "09:16")
                
                # Parse times
                opening_hour_parts = opening_hour.split(":")
                start_time_parts = start_time.split(":")
                
                opening_hour_val = int(opening_hour_parts[0]) * 100 + int(opening_hour_parts[1])
                start_time_val = int(start_time_parts[0]) * 100 + int(start_time_parts[1])
                
                # If at opening hour, store as opening MTM
                if current_time_val == opening_hour_val:
                    logger.info(f"Background fetch at opening hour for {user_id} - storing as opening MTM")
                    set_opening_mtm_db(user_id, mtm_value)
                    
                    # Save state immediately after capturing opening MTM
                    from mtm_persistence_stabilized import save_state
                    save_state()
                    logger.info(f"Saved state immediately after capturing opening MTM for {user_id} in background")
                
                # If after start time, update regular stats
                if current_time_val >= start_time_val:
                    # Calculate relative MTM (current value minus opening hour value)
                    opening_hour_mtm = get_opening_mtm_db(user_id)
                    relative_mtm = mtm_value - opening_hour_mtm
                    
                    # Update user stats with the relative MTM value
                    update_user_stats(user_id, relative_mtm)
                    
                    # Also store the raw response in the cache
                    set_cached_data(user_id, json.dumps(data))
    
    except asyncio.TimeoutError:
        logger.warning(f"Background fetch timeout for {user_id}")
    except Exception as e:
        logger.error(f"Background fetch error for {user_id}: {str(e)}", exc_info=True)

def schedule_background_fetch(user_id: str, user_ip: str, delay: float = 0):
    """Schedule a background fetch with proper task management."""
    global background_tasks
    
    # Cancel existing task if any
    if user_id in background_tasks:
        background_tasks[user_id].cancel()
    
    # Create new task
    loop = get_or_create_event_loop()
    task = loop.create_task(fetch_user_mtm_background(user_id, user_ip))
    background_tasks[user_id] = task
    
    # Add callback to clean up completed tasks
    def cleanup_task(task):
        if user_id in background_tasks:
            del background_tasks[user_id]
    
    task.add_done_callback(cleanup_task)

# Optimized background scheduler function
def start_background_scheduler():
    """Start an optimized background scheduler with reduced resource usage."""
    def run_scheduler():
        logger.info("Starting optimized background scheduler")
        last_opening_check = None
        last_start_check = None
        
        while True:
            try:
                # Get current time
                now = datetime.now()
                current_time_str = now.strftime("%H:%M")
                
                # Get settings from users.json
                users_data = get_user_data()
                opening_hour = users_data.get("opening_mtm", "09:15")
                start_time = users_data.get("start_time", "09:16")
                
                # Check if it's opening hour (only once per minute)
                if current_time_str == opening_hour and last_opening_check != current_time_str:
                    logger.info(f"It's opening hour: {opening_hour}")
                    last_opening_check = current_time_str
                    
                    # Fetch for all users that haven't been fetched yet
                    for user in users_data.get("users", []):
                        user_id = user.get("userId")
                        user_ip = user.get("ip")
                        
                        if user_id and user_ip and not is_opening_mtm_captured_db(user_id):
                            logger.info(f"Scheduling background fetch for {user_id} at opening hour")
                            schedule_background_fetch(user_id, user_ip)
                
                # Check if it's start time (only once per minute)
                if current_time_str == start_time and last_start_check != current_time_str:
                    logger.info(f"It's start time: {start_time}")
                    last_start_check = current_time_str
                    
                    # Fetch for all users
                    for user in users_data.get("users", []):
                        user_id = user.get("userId")
                        user_ip = user.get("ip")
                        
                        if user_id and user_ip:
                            schedule_background_fetch(user_id, user_ip)
                
                # Regular fetching after start time (every 30 seconds instead of every second)
                elif current_time_str > start_time and now.second % 30 == 0:
                    # Fetch for all users every 30 seconds
                    for user in users_data.get("users", []):
                        user_id = user.get("userId")
                        user_ip = user.get("ip")
                        
                        if user_id and user_ip:
                            schedule_background_fetch(user_id, user_ip)
                
                # Sleep for 5 seconds instead of 1 second to reduce CPU usage
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in background scheduler: {str(e)}", exc_info=True)
                # Sleep longer on error to prevent spam
                time.sleep(10)
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Optimized background scheduler started in separate thread")

def cleanup_background_tasks():
    """Clean up background tasks on shutdown."""
    global background_tasks
    for task in background_tasks.values():
        if not task.done():
            task.cancel()
    background_tasks.clear()
    logger.info("Background tasks cleaned up")

# Performance monitoring
def get_background_stats():
    """Get background scheduler statistics."""
    return {
        "active_tasks": len(background_tasks),
        "task_details": {user_id: task.done() for user_id, task in background_tasks.items()}
    }

# Global scheduler instance
background_scheduler = BackgroundScheduler()

def start_background_scheduler():
    """Start the background scheduler"""
    try:
        background_scheduler.start()
    except Exception as e:
        logger.error(f"Error starting background scheduler: {str(e)}", exc_info=True)

def stop_background_scheduler():
    """Stop the background scheduler"""
    try:
        background_scheduler.stop()
    except Exception as e:
        logger.error(f"Error stopping background scheduler: {str(e)}", exc_info=True)

# Legacy async function for compatibility
async def fetch_user_mtm_background(user_id: str, user_ip: str):
    """Legacy async function for compatibility"""
    try:
        # Run the synchronous version in a thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            background_scheduler._executor,
            background_scheduler._fetch_user_mtm,
            user_id,
            user_ip
        )
    except Exception as e:
        logger.error(f"Error in async background fetch for {user_id}: {str(e)}", exc_info=True)

# Cleanup function for application shutdown
def cleanup_background():
    """Clean up background resources"""
    try:
        stop_background_scheduler()
        logger.info("Background resources cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up background resources: {str(e)}", exc_info=True) 