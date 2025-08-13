# mtm_api_part2.py
# File 5: API Endpoints Part 2 - MTM Endpoint

from mtm_imports import *
from mtm_cache import *
from mtm_server import *

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
