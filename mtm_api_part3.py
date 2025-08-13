# mtm_api_part3.py
# File 6: API Endpoints Part 3 - MTM Endpoint (continued)

from mtm_imports import *
from mtm_cache import *
from mtm_server import *

@app.get("/MTM")
async def get_mtm_continued(request: Request, UserID: str = ""):
    """Continuation of the MTM endpoint"""
    # This code would be part of the same get_mtm function, but is separated here
    # for clarity. In the merged file, do not duplicate the function declaration.
    
    try:
        # Get user info
        users_data = get_user_data()
        user_ip = None
        for user in users_data["users"]:
            if user["userId"] == UserID:
                user_ip = user.get("ip")
                break
                
        # Get current time 
        now = datetime.now()
        current_hour, current_minute = now.hour, now.minute
        current_time_val = current_hour * 100 + current_minute
        
        # Get opening/start times
        opening_hour = users_data.get("opening_mtm", "09:15")
        start_time = users_data.get("start_time", "09:16")
        opening_hour_parts = opening_hour.split(":")
        start_time_parts = start_time.split(":")
        opening_hour_val = int(opening_hour_parts[0]) * 100 + int(opening_hour_parts[1])
        start_time_val = int(start_time_parts[0]) * 100 + int(start_time_parts[1])
        
        # BETWEEN opening hour and start time
        if current_time_val > opening_hour_val and current_time_val < start_time_val:
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
