# central_dashboard_optimized_part2.py
# Part 2: API Endpoints

@app.get("/")
async def root():
    """Serve the dashboard HTML at the root endpoint"""
    logger.info("Dashboard accessed")
    return HTMLResponse(content=DASHBOARD_HTML)

@app.get("/status")
async def status():
    """API endpoint returning server status"""
    logger.info("Status endpoint accessed")
    return {
        "name": "Stoxxo Central Hub", 
        "status": "running", 
        "cached_users": list(mtm_cache["stats"].keys()),
        "description": "Central hub for Stoxxo trading data"
    }

@app.get("/users")
async def get_users():
    """Endpoint that returns the list of available users"""
    logger.info("Users list requested")
    
    try:
        # Read the users.json file
        with open("users.json", "r") as f:
            users_data = json.load(f)
        
        # Log each user and their IP
        for user in users_data["users"]:
            user_id = user.get("userId", "unknown")
            user_ip = user.get("ip", "not configured")
            logger.info(f"Found user in users.json: {user_id} with IP: {user_ip}")
            init_user_stats(user_id)
            
        logger.info(f"Returning users: {json.dumps(users_data)}")
        return users_data
    except Exception as e:
        error_msg = f"Failed to load users: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Return an empty users list on error
        empty_users = {"users": []}
        logger.info("Returning empty users list due to error")
        return empty_users

# Function to check if daily reset is needed
def check_daily_reset():
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date != mtm_cache["last_reset_date"]:
        logger.info(f"Performing daily stats reset. Last reset: {mtm_cache['last_reset_date']}, Current date: {current_date}")
        reset_all_stats()
        mtm_cache["last_reset_date"] = current_date
        # Reset history for all users
        mtm_cache["history"] = {}
        # Reset minute markers
        mtm_cache["minute_markers"] = {}
        return True
    return False

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
            opening_hour_mtm = mtm_cache["opening_mtm"].get(UserID, 0)
            
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
        elif current_time_val == opening_hour_val and UserID not in mtm_cache["opening_hour_hit"]:
            logger.info(f"Exactly at opening hour for {UserID} - {current_time_val} == {opening_hour_val} - fetching for opening hour")
            
            # Mark this user as hit at opening hour 
            mtm_cache["opening_hour_hit"][UserID] = True
            
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
            
            # Store the opening hour MTM value
            mtm_cache["opening_mtm"][UserID] = mtm_value
            logger.info(f"Stored opening hour MTM for {UserID}: {mtm_value}")
            
            # Get opening hour value for this user
            opening_hour_mtm = mtm_cache["opening_mtm"].get(UserID, 0)
            
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
        elif current_time_val == opening_hour_val and UserID in mtm_cache["opening_hour_hit"]:
            logger.info(f"Still at opening hour for {UserID} but already hit - returning zeros with stored opening hour")
            
            # Get opening hour value
            opening_hour_mtm = mtm_cache["opening_mtm"].get(UserID, 0)
            
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
            opening_hour_mtm = mtm_cache["opening_mtm"].get(UserID, 0)
            
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
            opening_hour_mtm = mtm_cache["opening_mtm"].get(UserID, 0)
            
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
            opening_hour_mtm = mtm_cache["opening_mtm"].get(UserID, 0)
            
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

@app.post("/reset/{user_id}")
async def reset_stats(user_id: str):
    """Reset stats for a specific user"""
    logger.info(f"Resetting stats for user: {user_id}")
    
    if user_id in mtm_cache["stats"]:
        reset_user_stats(user_id)
        return {"status": "success", "message": f"Stats reset for user {user_id}"}
    else:
        return {"status": "error", "message": f"User {user_id} not found"}

@app.post("/reset-all")
async def reset_all():
    """Reset stats for all users"""
    logger.info("Resetting all user stats")
    reset_all_stats()
    return {"status": "success", "message": "All stats reset"}

@app.get("/cache-debug")
async def get_cache_debug():
    """Endpoint that returns the current state of the cache for debugging"""
    logger.info("Cache debug endpoint accessed")
    
    # Create a safe version of the cache to return (with sensitive data removed)
    safe_cache = {
        "opening_mtm": mtm_cache["opening_mtm"],
        "stats": mtm_cache["stats"],
        "last_updated": {k: datetime.fromtimestamp(v).strftime('%H:%M:%S') 
                         for k, v in mtm_cache["last_updated"].items()},
        "last_reset_date": mtm_cache["last_reset_date"],
        "opening_hour_hit": {k: "Yes" for k in mtm_cache["opening_hour_hit"]},
        "cache_ttl": mtm_cache["cache_ttl"],
        "history_points": {k: len(v) for k, v in mtm_cache["history"].items()},
        "minute_markers": {k: len(v) for k, v in mtm_cache["minute_markers"].items()}
    }
    
    return JSONResponse(content=safe_cache)

@app.post("/trigger-background-fetch")
async def trigger_background_fetch(background_tasks: BackgroundTasks):
    """Manually trigger background fetching for all users - useful for testing"""
    logger.info("Manual background fetch triggered")
    
    users_data = get_user_data()
    fetch_count = 0
    
    for user in users_data.get("users", []):
        user_id = user.get("userId")
        user_ip = user.get("ip")
        
        if user_id and user_ip:
            background_tasks.add_task(fetch_user_mtm_background, user_id, user_ip)
            fetch_count += 1
    
    return {"status": "success", "message": f"Triggered background fetch for {fetch_count} users"}

# Endpoint to get today's MTM history for a user
@app.get("/history")
async def get_history(UserID: str = ""):
    """Return today's MTM history for a user"""
    if not UserID:
        return JSONResponse(status_code=400, content={"status": "error", "error": "UserID parameter is required"})
    history = mtm_cache["history"].get(UserID, [])
    return JSONResponse(content={"status": "success", "history": history})

# Endpoint to check the minute markers for a user (for debugging)
@app.get("/minute-markers")
async def get_minute_markers(UserID: str = ""):
    """Return the minute markers for a user"""
    if not UserID:
        return JSONResponse(status_code=400, content={"status": "error", "error": "UserID parameter is required"})
    markers = mtm_cache["minute_markers"].get(UserID, {})
    return JSONResponse(content={"status": "success", "markers": list(markers.keys())})
