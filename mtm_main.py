# mtm_main.py
# Main application file that imports all components

from mtm_imports import *
from mtm_config import config
from mtm_cache import *
from mtm_server import *
from mtm_html import DASHBOARD_HTML
from mtm_background import *
from mtm_persistence import load_state, save_state, start_auto_save, register_shutdown_handler
from mtm_db import get_opening_mtm as get_opening_mtm_db, set_opening_mtm as set_opening_mtm_db, is_opening_mtm_captured as is_opening_mtm_captured_db

# Apply configuration
mtm_cache["cache_ttl"] = config["cache_ttl"]

# Import API endpoints after DASHBOARD_HTML is defined
from mtm_api_part1 import *
from mtm_api_part4 import *

# Define the MTM endpoint (combination of part2 and part3)
@app.get("/MTM")
async def get_mtm(request: Request, UserID: str = ""):
    """Endpoint that fetches MTM data from the client machine"""
    logger.info(f"MTM endpoint accessed with UserID: {UserID}")
    
    # Check if daily reset is needed
    check_daily_reset()
    
    # Validate that a user ID was provided
    if not UserID:
        logger.error("No UserID provided")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "response": 0, "error": "UserID parameter is required"}
        )
    
    try:
        current_time = time.time()
        
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
        
        logger.info(f"Time check for {UserID}: Current={current_time_str} ({current_time_val}), Opening={opening_hour} ({opening_hour_val}), Start={start_time} ({start_time_val})")
        
        # BEFORE opening hour - don't fetch at all, just return zeros
        if current_time_val < opening_hour_val:
            logger.info(f"Before opening hour for {UserID} - {current_time_val} < {opening_hour_val} - not fetching, returning zeros")
            
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
                timeout=5
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
            logger.info(f"Still at opening hour for {UserID} but already hit - returning zeros with stored opening hour")
            
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
            logger.info(f"Between opening and start for {UserID} - {opening_hour_val} < {current_time_val} < {start_time_val} - returning zeros with stored opening hour")
            
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
        
        # After start time or if at opening hour but already hit, use normal cache logic
        # Use cache if available and not expired
        if UserID in mtm_cache["data"] and UserID in mtm_cache["last_updated"] and time.time() - mtm_cache["last_updated"][UserID] < mtm_cache["cache_ttl"]:
            logger.info(f"Using cached data for {UserID}")
            
            # Get opening hour value for this user
            opening_hour_mtm = get_opening_mtm_db(UserID)
            
            # Return the cached response with the updated stats
            response_data = {
                "status": "success",
                "response": mtm_cache["stats"][UserID]["current_mtm"],  # Already stored as relative
                "max_mtm": mtm_cache["stats"][UserID]["max_mtm"],
                "min_mtm": mtm_cache["stats"][UserID]["min_mtm"],
                "opening_mtm": opening_hour_mtm,
                "cached": True
            }
            
            return JSONResponse(content=response_data)
        
        # If we get here, we need to fetch fresh MTM data
        full_url = f"http://{user_ip}/MTM"
        logger.info(f"Fetching regular MTM from {full_url} for user {UserID}")
        
        # Forward the request to the client machine
        response = requests.get(
            full_url,
            headers=headers,
            params={"UserID": UserID},
            timeout=5  # Add timeout
        )
        
        response.raise_for_status()  # Raise exception for bad status codes
        
        logger.info(f"Response received: Status {response.status_code}")
        logger.info(f"Response content: {response.text}")
        
        # Try to parse the response as JSON
        try:
            data = response.json()
            if isinstance(data, str):
                # If the response is a JSON string, parse it again
                data = json.loads(data)
            logger.info(f"Parsed JSON data: {data}")
            
            # Extract MTM value
            mtm_value = float(data["response"])
            
            # Update cache
            mtm_cache["data"][UserID] = response.text
            mtm_cache["last_updated"][UserID] = time.time()
            
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
    logger.info("Auto-save started (saves state every minute)")
    
    # Start the background scheduler if enabled
    if config["enable_background_scheduler"]:
        start_background_scheduler()
        logger.info("Background scheduler started")
    else:
        logger.info("Background scheduler disabled in config")
    
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=config["server_port"])
