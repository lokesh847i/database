# mtm_background.py
# File 8: Background functions

from mtm_imports import *
from mtm_cache import *
from mtm_server import *

# Function to fetch MTM data for a user in the background
async def fetch_user_mtm_background(user_id: str, user_ip: str):
    """Fetch MTM data for a user in the background"""
    try:
        full_url = f"http://{user_ip}/MTM"
        logger.info(f"Background fetching from {full_url} for user {user_id}")
        
        # Forward the request to the client machine
        response = requests.get(
            full_url,
            headers=headers,
            params={"UserID": user_id},
            timeout=5
        )
        
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        if isinstance(data, str):
            data = json.loads(data)
        
        # Extract MTM value
        mtm_value = float(data["response"])
        logger.info(f"Background fetch successful for {user_id}, MTM: {mtm_value}")
        
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
            mtm_cache["opening_mtm"][user_id] = mtm_value
            mtm_cache["opening_hour_hit"][user_id] = True
            
            # Save state immediately after capturing opening MTM
            from mtm_persistence import save_state
            save_state()
            logger.info(f"Saved state immediately after capturing opening MTM for {user_id} in background")
        
        # If after start time, update regular stats
        if current_time_val >= start_time_val:
            # Calculate relative MTM (current value minus opening hour value)
            opening_hour_mtm = mtm_cache["opening_mtm"].get(user_id, 0)
            relative_mtm = mtm_value - opening_hour_mtm
            
            # Update user stats with the relative MTM value
            update_user_stats(user_id, relative_mtm)
            
            # Also store the raw response in the cache
            mtm_cache["data"][user_id] = json.dumps(data)
            mtm_cache["last_updated"][user_id] = time.time()
    
    except Exception as e:
        logger.error(f"Background fetch error for {user_id}: {str(e)}", exc_info=True)

# Background scheduler function
def start_background_scheduler():
    """Start a background scheduler that checks the time and fetches data"""
    def run_scheduler():
        logger.info("Starting background scheduler")
        while True:
            try:
                # Get current time
                now = datetime.now()
                current_time_str = now.strftime("%H:%M")
                
                # Get settings from users.json
                users_data = get_user_data()
                opening_hour = users_data.get("opening_mtm", "09:15")
                start_time = users_data.get("start_time", "09:16")
                
                # Check if it's opening hour or start time
                is_opening_hour = current_time_str == opening_hour
                is_start_time = current_time_str == start_time
                is_after_start = current_time_str > start_time
                
                # If it's opening hour and we haven't fetched for some users
                if is_opening_hour:
                    logger.info(f"It's opening hour: {opening_hour}")
                    
                    # Fetch for all users that haven't been fetched yet
                    for user in users_data.get("users", []):
                        user_id = user.get("userId")
                        user_ip = user.get("ip")
                        
                        if user_id and user_ip and user_id not in mtm_cache["opening_hour_hit"]:
                            logger.info(f"Scheduling background fetch for {user_id} at opening hour")
                            # Create a new event loop for the async function
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(fetch_user_mtm_background(user_id, user_ip))
                
                # If it's start time or after start time, initiate regular fetching
                if is_start_time or (is_after_start and now.second == 0):  # Only fetch at xx:xx:00
                    # Only log if it's exactly start time
                    if is_start_time:
                        logger.info(f"It's start time: {start_time}")
                    
                    # Fetch for all users
                    for user in users_data.get("users", []):
                        user_id = user.get("userId")
                        user_ip = user.get("ip")
                        
                        if user_id and user_ip:
                            # Only fetch every minute after start time
                            if is_start_time or now.second == 0:
                                # Create a new event loop for the async function
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(fetch_user_mtm_background(user_id, user_ip))
                
                # Sleep for 1 second before checking again
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in background scheduler: {str(e)}", exc_info=True)
                # Sleep a bit longer on error to prevent spam
                time.sleep(5)
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Background scheduler started in separate thread")
