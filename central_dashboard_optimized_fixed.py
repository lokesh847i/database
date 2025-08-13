# central_dashboard_optimized_fixed.py
# Optimized main application file with improved performance and stability

from mtm_imports import *
from mtm_config import config
from mtm_cache_stabilized import *
from mtm_server import *
from mtm_html import DASHBOARD_HTML
from mtm_background_stabilized import *
from mtm_persistence_stabilized import load_state, save_state, start_auto_save, register_shutdown_handler
from mtm_db_stabilized import get_opening_mtm as get_opening_mtm_db, set_opening_mtm as set_opening_mtm_db, is_opening_mtm_captured as is_opening_mtm_captured_db

# Apply optimized configuration
mtm_cache["cache_ttl"] = config.get("cache_ttl", 5.0)

# Import API endpoints after DASHBOARD_HTML is defined
from mtm_api_part1 import *
from mtm_api_part4 import *

# Define the optimized MTM endpoint
@app.get("/MTM")
async def get_mtm(request: Request, UserID: str = ""):
    """Optimized endpoint that fetches MTM data from the client machine"""
    logger.debug(f"MTM endpoint accessed with UserID: {UserID}")
    
    # Check if daily reset is needed (only once per request)
    check_daily_reset()
    
    # Validate that a user ID was provided
    if not UserID:
        logger.error("No UserID provided")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "response": 0, "error": "UserID parameter is required"}
        )
    
    try:
        # Get user IP from users.json
        users_data = get_user_data()
        user_ip = None
        
        # Find the specific user in the users data
        for user in users_data["users"]:
            if user["userId"] == UserID:
                user_ip = user.get("ip")
                break
        
        if not user_ip:
            logger.error(f"No IP found for user {UserID}")
            return JSONResponse(
                status_code=404,
                content={"status": "error", "response": 0, "error": f"User {UserID} not found or no IP configured"}
            )
        
        # Get current time to check against opening hour and start time
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        # Extract time parts for comparison
        current_hour, current_minute = now.hour, now.minute
        current_time_val = current_hour * 100 + current_minute
        
        # Get the opening hour and start time from users.json
        opening_hour = users_data.get("opening_mtm", "09:15")
        start_time = users_data.get("start_time", "09:16")
        
        # Parse opening hour and start time
        opening_hour_parts = opening_hour.split(":")
        start_time_parts = start_time.split(":")
        
        opening_hour_val = int(opening_hour_parts[0]) * 100 + int(opening_hour_parts[1])
        start_time_val = int(start_time_parts[0]) * 100 + int(start_time_parts[1])
        
        logger.debug(f"Time check for {UserID}: Current={current_time_str} ({current_time_val}), Opening={opening_hour} ({opening_hour_val}), Start={start_time} ({start_time_val})")
        
        # BEFORE opening hour - don't fetch at all, just return zeros
        if current_time_val < opening_hour_val:
            logger.debug(f"Before opening hour for {UserID} - {current_time_val} < {opening_hour_val} - not fetching, returning zeros")
            
            # Get opening hour value (should be 0 before opening hour)
            opening_hour_mtm = get_opening_mtm_db(UserID)
            
            return JSONResponse(
                content={
                    "status": "success",
                    "response": 0,  # Current MTM as 0
                    "max_mtm": 0,   # Max MTM as 0
                    "min_mtm": 0,   # Min MTM as 0
                    "opening_mtm": opening_hour_mtm,
                    "cached": False
                }
            )
        
        # AT opening hour, fetch MTM and store it
        elif current_time_val == opening_hour_val and not is_opening_mtm_captured_db(UserID):
            logger.info(f"Exactly at opening hour for {UserID} - {current_time_val} == {opening_hour_val} - fetching for opening hour")
            
            # Fetch from client machine
            full_url = f"http://{user_ip}/MTM"
            logger.info(f"Fetching opening hour MTM from {full_url} for user {UserID}")
            response = requests.get(
                full_url,
                headers=headers,
                params={"UserID": UserID},
                timeout=10  # Increased timeout
            )
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            if isinstance(data, str):
                data = json.loads(data)
            
            # Extract MTM value
            mtm_value = float(data["response"])
            
            # Store the opening hour MTM value in the database
            set_opening_mtm_db(UserID, mtm_value)
            logger.info(f"Stored opening hour MTM for {UserID} in DB: {mtm_value}")
            
            # Get opening hour value for this user
            opening_hour_mtm = get_opening_mtm_db(UserID)
            
            # Calculate relative MTM (current value minus opening hour value)
            relative_mtm = mtm_value - opening_hour_mtm
            
            # Update user stats with the relative MTM value
            update_user_stats(UserID, relative_mtm)
            
            # Return response with stats
            response_data = {
                "status": "success",
                "response": relative_mtm,  # Return relative MTM instead of absolute
                "max_mtm": mtm_cache["stats"][UserID]["max_mtm"],
                "min_mtm": mtm_cache["stats"][UserID]["min_mtm"],
                "opening_mtm": opening_hour_mtm,
                "cached": False
            }
            
            return JSONResponse(content=response_data)
        
        # At opening hour but ALREADY hit - return opening hour MTM but zeros for current/max/min
        elif current_time_val == opening_hour_val and is_opening_mtm_captured_db(UserID):
            logger.debug(f"Still at opening hour for {UserID} but already hit - returning zeros with stored opening hour")
            
            # Get opening hour value
            opening_hour_mtm = get_opening_mtm_db(UserID)
            
            return JSONResponse(
                content={
                    "status": "success",
                    "response": 0,  # Current MTM as 0 (no change from opening)
                    "max_mtm": 0,   # Max MTM as 0
                    "min_mtm": 0,   # Min MTM as 0
                    "opening_mtm": opening_hour_mtm,
                    "cached": False
                }
            )
        
        # BETWEEN opening hour and start time
        elif current_time_val > opening_hour_val and current_time_val < start_time_val:
            logger.debug(f"Between opening and start for {UserID} - {opening_hour_val} < {current_time_val} < {start_time_val} - returning zeros with stored opening hour")
            
            # Get opening hour value
            opening_hour_mtm = get_opening_mtm_db(UserID)
            
            return JSONResponse(
                content={
                    "status": "success",
                    "response": 0,  # Current MTM as 0 (no change from opening)
                    "max_mtm": 0,   # Max MTM as 0
                    "min_mtm": 0,   # Min MTM as 0
                    "opening_mtm": opening_hour_mtm,
                    "cached": False
                }
            )
        
        # After start time, use optimized cache logic
        # Use cache if available and not expired
        if is_cache_valid(UserID):
            logger.debug(f"Using cached data for {UserID}")
            
            # Get opening hour value for this user
            opening_hour_mtm = get_opening_mtm_db(UserID)
            
            # Get cached stats
            cached_data = get_cached_data(UserID)
            stats = cached_data["stats"]
            
            # Return the cached response with the updated stats
            response_data = {
                "status": "success",
                "response": stats["current_mtm"],  # Already stored as relative
                "max_mtm": stats["max_mtm"],
                "min_mtm": stats["min_mtm"],
                "opening_mtm": opening_hour_mtm,
                "cached": True
            }
            
            return JSONResponse(content=response_data)
        
        # If we get here, we need to fetch fresh MTM data
        full_url = f"http://{user_ip}/MTM"
        logger.debug(f"Fetching regular MTM from {full_url} for user {UserID}")
        
        # Forward the request to the client machine
        response = requests.get(
            full_url,
            headers=headers,
            params={"UserID": UserID},
            timeout=10  # Increased timeout
        )
        
        response.raise_for_status()  # Raise exception for bad status codes
        
        logger.debug(f"Response received: Status {response.status_code}")
        
        # Try to parse the response as JSON
        try:
            data = response.json()
            if isinstance(data, str):
                # If the response is a JSON string, parse it again
                data = json.loads(data)
            logger.debug(f"Parsed JSON data: {data}")
            
            # Extract MTM value
            mtm_value = float(data["response"])
            
            # Update cache with optimized functions
            set_cached_data(user_id=UserID, data=response.text)
            
            # Get opening hour value for this user
            opening_hour_mtm = get_opening_mtm_db(UserID)
            
            # Calculate relative MTM (current value minus opening hour value)
            relative_mtm = mtm_value - opening_hour_mtm
            
            # Update user stats with the relative MTM value
            update_user_stats(UserID, relative_mtm)
            
            # Get updated stats
            cached_data = get_cached_data(UserID)
            stats = cached_data["stats"]
            
            # Return response with stats
            response_data = {
                "status": "success",
                "response": relative_mtm,  # Return relative MTM instead of absolute
                "max_mtm": stats["max_mtm"],
                "min_mtm": stats["min_mtm"],
                "opening_mtm": opening_hour_mtm,
                "cached": False
            }
            
            return JSONResponse(content=response_data)
            
        except json.JSONDecodeError:
            # If not JSON, return the raw text
            return response.text
            
    except requests.RequestException as e:
        error_msg = f"Failed to fetch MTM data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "response": 0, "error": error_msg}
        )
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "response": 0, "error": error_msg}
        )

# Endpoint to get configuration values
@app.get("/config")
async def get_config():
    """Return the current configuration values"""
    return JSONResponse(content={
        "mtm_refresh_interval": config["mtm_refresh_interval"],
        "chart_update_interval": config["chart_update_interval"],
        "cache_ttl": config["cache_ttl"],
        "server_port": config["server_port"]
    })

# Performance monitoring endpoint
@app.get("/performance")
async def get_performance_stats():
    """Get performance statistics"""
    try:
        from mtm_db_stabilized import get_database_stats
        from mtm_background_stabilized import get_background_stats
        
        db_stats = get_database_stats()
        bg_stats = get_background_stats()
        
        return JSONResponse(content={
            "database": db_stats,
            "background": bg_stats,
            "cache": {
                "cache_ttl": mtm_cache["cache_ttl"],
                "batch_updates_pending": len(mtm_cache["batch_updates"])
            }
        })
    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        return JSONResponse(content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting MarvelQuant Central Hub (Optimized Version)...")
    logger.info(f"Using configuration: MTM refresh={config['mtm_refresh_interval']}ms, Chart update={config['chart_update_interval']}ms")
    
    # Try to load previous state
    loaded = load_state()
    if loaded:
        logger.info("Successfully loaded previous state")
    else:
        logger.info("No previous state loaded, starting fresh")
    
    # Register shutdown handler to save state on exit
    register_shutdown_handler()
    
    # Start auto-save for periodic persistence
    start_auto_save()
    logger.info("Auto-save started (handled by batch processing)")
    
    # Start the background scheduler if enabled
    if config["enable_background_scheduler"]:
        start_background_scheduler()
        logger.info("Optimized background scheduler started")
    else:
        logger.info("Background scheduler disabled in config")
    
    # Start the FastAPI server with optimized settings
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=config["server_port"],
        log_level="warning",  # Reduce logging overhead
        access_log=False,     # Disable access logs for better performance
        loop="asyncio"        # Use asyncio for better performance
    )
