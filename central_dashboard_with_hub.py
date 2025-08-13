# central_dashboard_with_hub.py

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
import requests
import logging
import os
import json
from datetime import datetime, time as dt_time
import time
from typing import Dict, Any
import threading
import asyncio

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
def setup_logger():
    current_date = datetime.now().strftime("%d%m%Y")
    log_filename = f"logs/central_log_{current_date}.txt"
    
    logger_instance = logging.getLogger("stoxxo_central")
    logger_instance.setLevel(logging.INFO)
    
    # Remove any existing handlers
    if logger_instance.handlers:
        for handler in logger_instance.handlers:
            logger_instance.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger_instance.addHandler(file_handler)
    logger_instance.addHandler(console_handler)
    
    return logger_instance

# Set up the global logger
logger = setup_logger()

# Cache storage for MTM data and stats
mtm_cache = {
    "last_updated": {},  # Track last update time per user instead of globally
    "cache_ttl": 0.5,  # Cache TTL in seconds (reduced to 0.5 seconds)
    "data": {},
    "stats": {},  # Store max/min values for each user
    "last_reset_date": datetime.now().strftime("%Y-%m-%d"),  # Track the last reset date
    "opening_mtm": {},  # Store opening hour MTM values for each user
    "opening_hour_hit": {},   # Track if opening hour fetch has been done for each user
    "history": {}  # Store today's MTM history for each user: {user_id: [(timestamp, mtm_value), ...]}
}

# Initialize stats
def init_user_stats(user_id: str):
    if user_id not in mtm_cache["stats"]:
        mtm_cache["stats"][user_id] = {
            "max_mtm": -float('inf'),
            "min_mtm": float('inf'),
            "current_mtm": 0
        }

# Update stats based on new MTM value
def update_user_stats(user_id: str, mtm_value: float):
    init_user_stats(user_id)
    # Update current value
    mtm_cache["stats"][user_id]["current_mtm"] = mtm_value
    # Update max/min if needed
    if mtm_value > mtm_cache["stats"][user_id]["max_mtm"]:
        mtm_cache["stats"][user_id]["max_mtm"] = mtm_value
    if mtm_value < mtm_cache["stats"][user_id]["min_mtm"]:
        mtm_cache["stats"][user_id]["min_mtm"] = mtm_value
    # Append to history (for today)
    now = datetime.now()
    ts = now.strftime("%H:%M:%S")
    if user_id not in mtm_cache["history"]:
        mtm_cache["history"][user_id] = []
    mtm_cache["history"][user_id].append({"timestamp": ts, "mtm": mtm_value})

# Reset stats for a user
def reset_user_stats(user_id: str):
    mtm_cache["stats"][user_id] = {
        "max_mtm": -float('inf'),
        "min_mtm": float('inf'),
        "current_mtm": mtm_cache["stats"].get(user_id, {}).get("current_mtm", 0)
    }
    # Also reset opening hour data
    if user_id in mtm_cache["opening_mtm"]:
        mtm_cache["opening_mtm"][user_id] = 0
    if user_id in mtm_cache["opening_hour_hit"]:
        mtm_cache["opening_hour_hit"].pop(user_id)
    # Reset history for this user
    if user_id in mtm_cache["history"]:
        mtm_cache["history"][user_id] = []

# Reset all stats
def reset_all_stats():
    for user_id in mtm_cache["stats"]:
        reset_user_stats(user_id)
    # Clear opening hour data completely
    mtm_cache["opening_mtm"] = {}
    mtm_cache["opening_hour_hit"] = {}

app = FastAPI(title="MarvelQuant Central Hub")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (for logo)
# Create a static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Copy the logo to the static directory
if os.path.exists("MQ-Logo-Main.svg"):
    import shutil
    shutil.copy("MQ-Logo-Main.svg", "static/MQ-Logo-Main.svg")
    logger.info("Copied logo to static directory")

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Standard headers for requests
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}

# Function to get user data from users.json
def get_user_data():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load users.json: {str(e)}", exc_info=True)
        # Return empty user data instead of defaults
        return {"users": []}

# Create default users.json if it doesn't exist
if not os.path.exists("users.json"):
    with open("users.json", "w") as f:
        # Creating an empty users array
        json.dump({"users": []}, f, indent=2)
    logger.info("Created empty users.json file")

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
        "cache_ttl": mtm_cache["cache_ttl"]
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

# Dashboard HTML to be served at the root endpoint
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MarvelQuant | MTM Tracker</title>
    <link rel="icon" type="image/svg+xml" href="/static/MQ-Logo-Main.svg">
    <link rel="stylesheet" href="https://unpkg.com/tippy.js@6/dist/tippy.css" />
    <style>
        body {
            background: #fff;
            font-family: 'Segoe UI', 'Poppins', Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 1100px;
            margin: 40px auto;
            padding: 0 8px;
        }
        .card {
            background: none;
            border-radius: 20px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            padding: 0 0 32px 0;
            margin: 0 auto;
            overflow: hidden;
        }
        .header-bar {
            background: #fff;
            display: flex;
            align-items: center;
            padding: 24px 32px 10px 32px;
        }
        .header-bar img {
            height: 48px;
            margin-right: 18px;
        }
        .header-title {
            font-size: 2rem;
            font-weight: 600;
            color: #222;
            letter-spacing: 0.5px;
        }
        .info-message {
            display:flex;align-items:center;justify-content:space-between;color:#333;font-weight:600;font-size:1.15rem;margin:10px 32px 0 32px;min-height:56px;">
            <img src="/static/MQ-Logo-Main.svg" alt="MarvelQuant Logo" style="height:48px;vertical-align:middle;margin-right:18px;flex-shrink:0;">
            <span style="flex:1;text-align:center;font-size:1.3rem;font-weight:600;">MTM Tracker</span>
            <span class="last-updated" id="lastUpdated" style="margin:0;font-size:1rem;color:#666;font-weight:400;text-align:right;min-width:140px;"></span>
        }
        .last-updated {
            text-align: right;
            font-size: 1rem;
            color: #666;
            margin: 18px 32px 0 0;
        }
        .table-wrapper {
            padding: 0 32px;
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 18px;
            background: #fff;
            min-width: 0;
        }
        thead tr {
            background: #f2f2f2;
        }
        th, td {
            padding: 14px 12px;
            text-align: left;
            font-size: 1.08rem;
            vertical-align: middle;
        }
        td.mtm-col {
            min-width: 130px;
        }
        th {
            color: #222;
            font-weight: 600;
            border: none;
            white-space: nowrap;
        }
        tbody tr {
            background: #fff;
            transition: background 0.2s;
        }
        tbody tr:nth-child(even) {
            background: #f6f8fb;
        }
        tbody tr:hover {
            background: #eaf1fb;
        }
        .positive {
            color: #0f9d58;
            font-weight: 600;
        }
        .negative {
            color: #ea4335;
            font-weight: 600;
        }
        .neutral {
            color: #2a5298;
            font-weight: 600;
        }
        @media (max-width: 900px) {
            .container { max-width: 100%; }
            .header-bar, .info-message, .table-wrapper { padding-left: 8px; padding-right: 8px; }
            th, td { font-size: 0.98rem; padding: 10px 6px; }
        }
        @media (max-width: 600px) {
            .header-title { font-size: 1.2rem; }
            .header-bar img { height: 32px; }
            th, td { font-size: 0.85rem; padding: 7px 2px; }
            .info-message { font-size: 0.95rem; padding: 8px 4px; margin: 16px 4px 0 4px; }
            .last-updated { margin: 12px 8px 0 0; font-size: 0.95rem; position: static !important; display: block; text-align: center; }
            .graph-modal {
                width: 98vw !important;
                min-width: 0 !important;
                height: auto !important;
                min-height: 0 !important;
                padding: 8px 2px 8px 2px !important;
                border-radius: 14px !important;
            }
            .graph-popover {
                width: 98vw !important;
                min-width: 0 !important;
                height: auto !important;
                min-height: 0 !important;
                border-radius: 10px !important;
                padding: 8px 2px 8px 2px !important;
            }
            .graph-modal canvas,
            .graph-popover canvas {
                width: 90% !important;
                height: auto !important;
                max-width: 100vw !important;
            }
        }
        .graph-icon {
            cursor: pointer;
            font-size: 1.3rem;
            color: #2a5298;
            transition: color 0.2s;
            vertical-align: middle;
        }
        .graph-icon:hover {
            color: #0f9d58;
        }
        .graph-popover {
            width: 320px;
            height: 180px;
            background: #fff;
            padding: 8px 0 0 0;
            border-radius: 10px;
            box-shadow: none !important;
            border: 4px solid #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .graph-modal-bg {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.25);
            z-index: 1000;
                display: flex;
            align-items: center;
            justify-content: center;
        }
        .graph-modal {
            background: #fff;
            border-radius: 16px;
            padding: 24px 24px 12px 24px;
            min-width: 400px;
            min-height: 320px;
            box-shadow: 0 4px 32px rgba(0,0,0,0.18);
            position: relative;
        }
        .graph-modal-close {
            position: absolute;
            top: 10px;
            right: 18px;
            font-size: 1.5rem;
            color: #888;
            cursor: pointer;
            background: none;
            border: none;
        }
        #reconnect-indicator { display: none; align-items: center; margin-left: 10px; font-size: 0.98rem; color: #ea4335; font-weight: 500; vertical-align: middle; }
        #reconnect-indicator svg { margin-right: 4px; vertical-align: middle; }
        .tippy-box[data-theme~='light'] {
            border: none !important;
            box-shadow: none !important;
            background: #fff !important;
        }
        .tippy-box[data-theme~='light'],
        .tippy-box[data-theme~='light'] .tippy-content {
            border: none !important;
            outline: none !important;
            background: #fff !important;
        }
        .tippy-box[data-theme~='light'] .tippy-arrow {
            color: #fff !important;
            border: none !important;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/@popperjs/core@2"></script>
    <script src="https://unpkg.com/tippy.js@6"></script>
</head>
<body>
        <div class="container">
        <div class="card">
            <div class="info-message" style="display:flex;align-items:center;justify-content:space-between;color:#333;font-weight:600;font-size:1.15rem;margin:10px 32px 0 32px;min-height:56px;">
                <img src="/static/MQ-Logo-Main.svg" alt="MarvelQuant Logo" style="height:48px;vertical-align:middle;margin-right:18px;flex-shrink:0;">
                <span style="flex:1;text-align:center;font-size:1.3rem;font-weight:600;">MTM Tracker</span>
                <span class="last-updated" id="lastUpdated" style="margin:0;font-size:1rem;color:#666;font-weight:400;text-align:right;min-width:140px;"></span>
            </div>
            <div class="table-wrapper">
            <table class="mtm-table">
                <thead>
                    <tr>
                        <th>S.No.</th>
                        <th>User ID</th>
                        <th>User Alias</th>
                        <th>Intraday MTM</th>
                        <th>Max MTM</th>
                        <th>Min MTM</th>
                        <th>MTM Analyzer</th>
                    </tr>
                </thead>
                <tbody id="mtmTableBody">
                        <tr>
                            <td>-</td><td>-</td><td>-</td><td class="neutral">-</td><td class="positive">-</td><td class="negative">-</td>
                    </tr>
                </tbody>
            </table>
            </div>
        </div>
    </div>
    <div class="last-updated" id="lastUpdated-mobile" style="display:none;margin:12px 0 0 0;font-size:0.95rem;color:#666;font-weight:400;text-align:center;"></div>
    <span id="reconnect-indicator">
        <svg width="18" height="18" viewBox="0 0 40 40" fill="none"><circle cx="20" cy="20" r="16" stroke="#ea4335" stroke-width="4" stroke-linecap="round" stroke-dasharray="80" stroke-dashoffset="60"><animate attributeName="stroke-dashoffset" values="60;0" dur="1s" repeatCount="indefinite"/></circle></svg>
        Reconnecting…
    </span>
    <script>
        // Configuration - Use relative path for API to work from any hostname
        const API_ENDPOINT = '/MTM';
        const REFRESH_INTERVAL = 2000; // 2 seconds
        let users = [];
        let refreshInterval;
        let consecutiveErrors = 0;
        const MAX_CONSECUTIVE_ERRORS = 5;
        let zeroMtmCount = {};
        // History cache for user graphs
        const historyCache = {};
        // Spinner SVG
        const spinnerSVG = `<div style='display:flex;align-items:center;justify-content:center;height:100%;'><svg width='40' height='40' viewBox='0 0 40 40' fill='none'><circle cx='20' cy='20' r='16' stroke='#2a5298' stroke-width='4' stroke-linecap='round' stroke-dasharray='80' stroke-dashoffset='60'><animate attributeName='stroke-dashoffset' values='60;0' dur='1s' repeatCount='indefinite'/></circle></svg></div>`;
        // Helper: Exponential backoff for MTM fetch errors
        let mtmFetchBackoff = 2000;
        function resetMtmBackoff() { mtmFetchBackoff = 2000; }
        function increaseMtmBackoff() { mtmFetchBackoff = Math.min(mtmFetchBackoff * 2, 30000); }
        let lastChartUserId = null;
        let lastPopoverUserId = null;
        document.addEventListener('DOMContentLoaded', async function() {
            zeroMtmCount = {};
            await fetchUsers();
            users.forEach(user => { zeroMtmCount[user.userId] = 0; });
            renderUserTable();
            startAutoRefresh();
                const savedStats = localStorage.getItem('mtmTrackerStats');
                if (savedStats) {
                    try {
                        const stats = JSON.parse(savedStats);
                        users.forEach(user => {
                            if (stats[user.userId]) {
                                user.maxMtm = stats[user.userId].maxMtm || -Infinity;
                                user.minMtm = stats[user.userId].minMtm || Infinity;
                            if (stats[user.userId].openingHourMtm !== undefined) {
                                user.openingHourMtm = stats[user.userId].openingHourMtm;
                            }
                            const maxElement = document.getElementById(`max-${user.userId}`);
                            const minElement = document.getElementById(`min-${user.userId}`);
                            const openingHourElement = document.getElementById(`opening-hour-${user.userId}`);
                            if (maxElement && user.maxMtm !== -Infinity) {
                                maxElement.textContent = formatCurrency(user.maxMtm);
                            }
                            if (minElement && user.minMtm !== Infinity) {
                                minElement.textContent = formatCurrency(user.minMtm);
                            }
                            if (openingHourElement && user.openingHourMtm !== undefined) {
                                openingHourElement.textContent = formatCurrency(user.openingHourMtm);
                                openingHourElement.className = user.openingHourMtm > 0 ? 'positive' : user.openingHourMtm < 0 ? 'negative' : 'neutral';
                            }
                        }
                    });
                } catch (e) { console.error("Error loading saved stats:", e); }
            }
        });
        async function fetchUsers() {
            try {
                const response = await fetch('/users');
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();
                window.globalSettings = {
                    opening_mtm: data.opening_mtm || '09:15',
                    start_time: data.start_time || '09:16',
                    chart_start_time: data.chart_start_time || '09:15'
                };
                if (data && data.users && Array.isArray(data.users)) {
                    users = data.users.map(user => ({
                            userId: user.userId,
                            ip: user.ip || null,
                            alias: user.alias || '',
                            mtm: 0,
                            maxMtm: -Infinity,
                            minMtm: Infinity,
                        openingHourMtm: 0
                    }));
                } else {
                    users = [];
                }
                if (users.length === 0) {
                    document.getElementById('mtmTableBody').innerHTML = '<tr><td colspan="8" style="text-align:center;">No users found.</td></tr>';
                }
            } catch (error) {
                document.getElementById('mtmTableBody').innerHTML = '<tr><td colspan="8" style="text-align:center;">Failed to load user data.</td></tr>';
                users = [];
            }
        }
        function formatCurrency(value) {
            return new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(value);
        }
        function updateUserUI(userId, data) {
            const mtmElement = document.getElementById(`mtm-${userId}`);
            const maxElement = document.getElementById(`max-${userId}`);
            const minElement = document.getElementById(`min-${userId}`);
            const rowElement = document.getElementById(`row-${userId}`);
            const openingHourElement = document.getElementById(`opening-hour-${userId}`);
            if (!mtmElement || !maxElement || !minElement || !rowElement) return;
            const userIndex = users.findIndex(user => user.userId === userId);
            if (userIndex === -1) return;
            const user = users[userIndex];
            if (data.status === 'error') {
                mtmElement.textContent = 'Connection Error';
                mtmElement.className = 'neutral';
                return;
            }
            const mtmValue = data.response;
            const maxMtm = data.max_mtm || 0;
            const minMtm = data.min_mtm || 0;
            user.mtm = mtmValue;
            if (mtmValue === 0 && maxMtm === 0 && minMtm === 0 && user.openingHourMtm === 0) {
                rowElement.style.display = 'none';
                return;
            } else {
                rowElement.style.display = '';
            }
            mtmElement.classList.add('data-updated');
            setTimeout(() => { mtmElement.classList.remove('data-updated'); }, 600);
            mtmElement.textContent = formatCurrency(mtmValue);
            mtmElement.className = mtmValue > 0 ? 'positive' : mtmValue < 0 ? 'negative' : 'neutral';
            if (data.max_mtm !== undefined && data.max_mtm !== null && data.max_mtm !== -Infinity) {
                user.maxMtm = data.max_mtm;
                maxElement.textContent = formatCurrency(data.max_mtm);
                maxElement.className = data.max_mtm > 0 ? 'positive' : data.max_mtm < 0 ? 'negative' : 'neutral';
            }
            if (data.min_mtm !== undefined && data.min_mtm !== null && data.min_mtm !== Infinity) {
                user.minMtm = data.min_mtm;
                minElement.textContent = formatCurrency(data.min_mtm);
                minElement.className = data.min_mtm > 0 ? 'positive' : data.min_mtm < 0 ? 'negative' : 'neutral';
            }
            if (openingHourElement) {
                openingHourElement.className = user.openingHourMtm > 0 ? 'positive' : user.openingHourMtm < 0 ? 'negative' : 'neutral';
                openingHourElement.textContent = formatCurrency(user.openingHourMtm);
            }
        }
        function updateLastUpdated() {
            const now = new Date();
            const text = `Last updated: ${now.toLocaleTimeString()}`;
            const desktop = document.getElementById('lastUpdated');
            const mobile = document.getElementById('lastUpdated-mobile');
            if (window.innerWidth <= 600) {
                if (desktop) desktop.style.display = 'none';
                if (mobile) {
                    mobile.style.display = 'block';
                    mobile.textContent = text;
                }
            } else {
                if (desktop) {
                    desktop.style.display = '';
                    desktop.textContent = text;
                    // Move reconnect indicator next to last updated if not already present
                    const indicator = document.getElementById('reconnect-indicator');
                    if (indicator && desktop && indicator.parentNode !== desktop.parentNode) {
                        desktop.parentNode.insertBefore(indicator, desktop.nextSibling);
                    }
                }
                if (mobile) mobile.style.display = 'none';
            }
            saveUserStats();
        }
        function handleFetchError() {
            consecutiveErrors++;
            if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
                showReconnectIndicator();
            }
        }
        function resetErrorCount() {
            consecutiveErrors = 0;
            hideReconnectIndicator();
        }
        function showReconnectIndicator() {
            const indicator = document.getElementById('reconnect-indicator');
            if (indicator) indicator.style.display = 'inline-flex';
        }
        function hideReconnectIndicator() {
            const indicator = document.getElementById('reconnect-indicator');
            if (indicator) indicator.style.display = 'none';
        }
        async function fetchUserMTM(userId) {
            try {
                const response = await fetch(`/MTM?UserID=${userId}`);
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();
                if (data.opening_mtm !== undefined) {
                    const user = users.find(u => u.userId === userId);
                    if (user) user.openingHourMtm = data.opening_mtm;
                }
                        updateUserUI(userId, data);
                resetErrorCount();
                resetMtmBackoff();
                        return true;
                } catch (error) {
                handleFetchError();
                increaseMtmBackoff();
                setTimeout(() => fetchUserMTM(userId), mtmFetchBackoff);
                return false;
            }
        }
        async function fetchAllMTM() {
            const fetchPromises = users.map(user => fetchUserMTM(user.userId));
            try {
                await Promise.all(fetchPromises);
                await refreshAllChartHistories();
                updateLastUpdated();
            } catch (error) {
                handleFetchError();
            }
        }
        function startAutoRefresh() {
            if (refreshInterval) clearInterval(refreshInterval);
            refreshInterval = setInterval(fetchAllMTM, REFRESH_INTERVAL);
        }
        function saveUserStats() {
            const stats = {};
            users.forEach(user => {
                stats[user.userId] = {
                    maxMtm: user.maxMtm,
                    minMtm: user.minMtm,
                    openingHourMtm: user.openingHourMtm
                };
            });
            localStorage.setItem('mtmTrackerStats', JSON.stringify(stats));
        }
        function renderUserTable() {
            const mtmTableBody = document.getElementById('mtmTableBody');
            mtmTableBody.innerHTML = '';
            const usersByIp = {};
            users.forEach(user => {
                const cleanIp = user.ip ? user.ip.split(':')[0] : 'N/A';
                if (!usersByIp[cleanIp]) usersByIp[cleanIp] = [];
                usersByIp[cleanIp].push(user);
            });
            let rowIndex = 1;
            for (const ip in usersByIp) {
                const usersWithSameIp = usersByIp[ip];
                usersWithSameIp.sort((a, b) => a.userId.localeCompare(b.userId));
                usersWithSameIp.forEach((user, index) => {
                const row = document.createElement('tr');
                row.id = `row-${user.userId}`;
                const mtmValue = user.mtm || 0;
                const maxMtm = user.maxMtm !== -Infinity ? user.maxMtm : 0;
                const minMtm = user.minMtm !== Infinity ? user.minMtm : 0;
                const mtmClass = mtmValue > 0 ? 'positive' : mtmValue < 0 ? 'negative' : 'neutral';
                const maxClass = maxMtm > 0 ? 'positive' : maxMtm < 0 ? 'negative' : 'neutral';
                const minClass = minMtm > 0 ? 'positive' : minMtm < 0 ? 'negative' : 'neutral';
                    const maxMtmDisplay = formatCurrency(maxMtm);
                    const minMtmDisplay = formatCurrency(minMtm);
                    row.innerHTML += `
                    <td>${rowIndex}</td>
                    <td>${user.userId}</td>
                    <td>${user.alias || ''}</td>
                    <td id="mtm-${user.userId}" class="mtm-col ${mtmClass}">${formatCurrency(mtmValue)}</td>
                    <td id="max-${user.userId}" class="mtm-col ${maxClass}">${maxMtmDisplay}</td>
                    <td id="min-${user.userId}" class="mtm-col ${minClass}">${minMtmDisplay}</td>
                    <td><span class="graph-icon" data-userid="${user.userId}" title="View MTM Graph">📈</span></td>
                `;
                mtmTableBody.appendChild(row);
                rowIndex++;
            });
            }
            setTimeout(initGraphPopovers, 0);
        }
        function isBeforeChartStartTime() {
            if (!window.globalSettings || !window.globalSettings.chart_start_time) return false;
            const now = new Date();
            const [h, m] = window.globalSettings.chart_start_time.split(':').map(Number);
            const chartStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, 0, 0);
            return now < chartStart;
        }
        function initGraphPopovers() {
            document.querySelectorAll('.graph-icon').forEach(icon => {
                const userId = icon.getAttribute('data-userid');
                // Only enable hover popover on desktop
                if (window.innerWidth > 600) {
                    tippy(icon, {
                        content: spinnerSVG,
                        allowHTML: true,
                        interactive: true,
                        placement: 'top',
                        theme: 'light',
                        onShow(instance) {
                            lastPopoverUserId = userId;
                            if (isBeforeChartStartTime()) {
                                instance.setContent(`<div style='padding:18px 12px;text-align:center;max-width:260px;'><b>Chart will be available after ${window.globalSettings.chart_start_time}</b></div>`);
                                return;
                            }
                            if (historyCache[userId]) {
                                instance.setContent(createGraphPopoverContent(userId, false));
                                setTimeout(() => renderUserGraph(userId, instance.popper.querySelector('canvas'), false, true), 0);
                            } else {
                                instance.setContent(spinnerSVG);
                                fetch(`/history?UserID=${userId}`)
                                    .then(res => res.json())
                                    .then(data => {
                                        historyCache[userId] = data.history || [];
                                        instance.setContent(createGraphPopoverContent(userId, false));
                                        setTimeout(() => renderUserGraph(userId, instance.popper.querySelector('canvas'), false, true), 0);
                                    });
                            }
                        },
                        onHidden(instance) {
                            const canvas = instance.popper.querySelector('canvas');
                            if (canvas && canvas._chartInstance) {
                                canvas._chartInstance.destroy();
                            }
                            lastPopoverUserId = null;
                        }
                    });
                }
                // Always allow click to open modal
                icon.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (isBeforeChartStartTime()) {
                        // Show modal with message instead of chart
                        showChartNotAvailableModal();
                        return;
                    }
                    showGraphModal(userId);
                });
            });
        }
        function createGraphPopoverContent(userId, isModal) {
            return `<div class="graph-popover"><canvas id="graph-canvas-${userId}-${isModal ? 'modal' : 'popover'}" width="300" height="150"></canvas></div>`;
        }
        function renderUserGraph(userId, canvas, isModal, useCache) {
            let historyPromise;
            if (useCache && historyCache[userId]) {
                historyPromise = Promise.resolve({ history: historyCache[userId] });
            } else {
                historyPromise = fetch(`/history?UserID=${userId}`).then(res => res.json()).then(data => {
                    historyCache[userId] = data.history || [];
                    return data;
                });
            }
            historyPromise.then(data => {
                if (!data.history || !canvas) return;
                // Filter history to only include points at or after chart_start_time
                let filteredHistory = data.history;
                if (window.globalSettings && window.globalSettings.chart_start_time) {
                    const chartStart = window.globalSettings.chart_start_time;
                    filteredHistory = data.history.filter(point => {
                        // point.timestamp is HH:MM:SS, chartStart is HH:MM
                        const pt = point.timestamp.split(":");
                        const ch = chartStart.split(":");
                        const ptVal = parseInt(pt[0],10)*60+parseInt(pt[1],10);
                        const chVal = parseInt(ch[0],10)*60+parseInt(ch[1],10);
                        return ptVal >= chVal;
                    });
                }
                const labels = filteredHistory.map(point => point.timestamp);
                const values = filteredHistory.map(point => point.mtm);
                let borderColor = '#2a5298';
                let backgroundColor = 'rgba(180,180,180,0.04)'; // neutral fill for mixed
                let segment = undefined;
                if (values.length > 0) {
                    const allPositive = values.every(v => v > 0);
                    const allNegative = values.every(v => v < 0);
                    if (allPositive) {
                        borderColor = '#0f9d58';
                        backgroundColor = 'rgba(15,157,88,0.08)';
                    } else if (allNegative) {
                        borderColor = '#ea4335';
                        backgroundColor = 'rgba(234,67,53,0.08)';
                    } else {
                        // Use Chart.js segment coloring for mixed
                        borderColor = undefined;
                        segment = {
                            borderColor: ctx => {
                                const v = ctx.p1.parsed.y;
                                return v >= 0 ? '#0f9d58' : '#ea4335';
                            }
                        };
                    }
                }
                if (canvas._chartInstance) canvas._chartInstance.destroy();
                canvas._chartInstance = new Chart(canvas.getContext('2d'), {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: '',
                            data: values,
                            borderColor: borderColor,
                            backgroundColor: backgroundColor,
                            pointRadius: 0,
                            pointHoverRadius: 5,
                            fill: true,
                            tension: 0.25,
                            segment: segment
                        }]
                    },
                    options: {
                        responsive: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: { enabled: true }
                        },
                        interaction: {
                            mode: 'nearest',
                            intersect: false
                        },
                        scales: {
                            x: { display: true, title: { display: false } },
                            y: { display: true, title: { display: false } }
                        }
                    }
                });
            });
        }
        function showGraphModal(userId) {
            lastChartUserId = userId;
            // Remove any existing modal
            const oldModal = document.getElementById('graph-modal-bg');
            if (oldModal) oldModal.remove();
            // Create modal
            const modalBg = document.createElement('div');
            modalBg.className = 'graph-modal-bg';
            modalBg.id = 'graph-modal-bg';
            modalBg.innerHTML = `
                <div class="graph-modal" style="width:75vw;height:75vh;min-width:320px;min-height:240px;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                    <button class="graph-modal-close" onclick="document.getElementById('graph-modal-bg').remove()">&times;</button>
                    <h3 style="text-align:center;font-weight:600;margin-bottom:12px;">${userId}</h3>
                    <div id="graph-modal-spinner">${spinnerSVG}</div>
                    <canvas id="graph-canvas-${userId}-modal" width="${Math.floor(window.innerWidth*0.7)}" height="${Math.floor(window.innerHeight*0.55)}" style="display:none;"></canvas>
                </div>
            `;
            document.body.appendChild(modalBg);
            // Render chart with cache and spinner
            setTimeout(() => {
                const canvas = document.getElementById(`graph-canvas-${userId}-modal`);
                if (historyCache[userId]) {
                    document.getElementById('graph-modal-spinner').style.display = 'none';
                    canvas.style.display = '';
                    renderUserGraph(userId, canvas, true, true);
                } else {
                    renderUserGraph(userId, canvas, true, false);
                    // Wait for data, then hide spinner
                    fetch(`/history?UserID=${userId}`)
                        .then(res => res.json())
                        .then(data => {
                            historyCache[userId] = data.history || [];
                            document.getElementById('graph-modal-spinner').style.display = 'none';
                            canvas.style.display = '';
                            renderUserGraph(userId, canvas, true, true);
                        });
                }
            }, 0);
            // Close on background click
            modalBg.addEventListener('click', (e) => {
                if (e.target === modalBg) modalBg.remove();
            });
        }
        function showChartNotAvailableModal() {
            // Remove any existing modal
            const oldModal = document.getElementById('graph-modal-bg');
            if (oldModal) oldModal.remove();
            // Create modal
            const modalBg = document.createElement('div');
            modalBg.className = 'graph-modal-bg';
            modalBg.id = 'graph-modal-bg';
            modalBg.innerHTML = `
                <div class="graph-modal" style="width:75vw;height:30vh;min-width:320px;min-height:120px;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                    <button class="graph-modal-close" onclick="document.getElementById('graph-modal-bg').remove()">&times;</button>
                    <h3 style="text-align:center;font-weight:600;margin-bottom:12px;">MTM Chart</h3>
                    <div style='font-size:1.15rem;text-align:center;padding:18px 0;'><b>Chart will be available after ${window.globalSettings.chart_start_time}</b></div>
                </div>
            `;
            document.body.appendChild(modalBg);
            // Close on background click
            modalBg.addEventListener('click', (e) => {
                if (e.target === modalBg) modalBg.remove();
            });
        }
        // Proactively refresh chart history for all users
        async function refreshAllChartHistories() {
            await Promise.all(users.map(user =>
                fetch(`/history?UserID=${user.userId}`)
                    .then(res => res.json())
                    .then(data => { historyCache[user.userId] = data.history || []; })
            ));
        }
        // Refresh chart cache when returning to the tab
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'visible') {
                // Clear chart history cache so next chart open fetches fresh data
                for (const key in historyCache) {
                    delete historyCache[key];
                }
                // Re-initialize popovers
                setTimeout(initGraphPopovers, 0);
                // Proactively refresh all chart histories
                refreshAllChartHistories();
                // If chart modal is open, refresh its data
                const modal = document.getElementById('graph-modal-bg');
                if (modal && lastChartUserId) {
                    const canvas = document.getElementById(`graph-canvas-${lastChartUserId}-modal`);
                    if (canvas) {
                        fetch(`/history?UserID=${lastChartUserId}`)
                            .then(res => res.json())
                            .then(data => {
                                historyCache[lastChartUserId] = data.history || [];
                                renderUserGraph(lastChartUserId, canvas, true, true);
                            });
                    }
                }
                // If a popover is open, refresh its data
                if (lastPopoverUserId) {
                    // Try to find the open tippy popover for this user
                    const popover = document.querySelector('.tippy-box[data-state="visible"]');
                    if (popover) {
                        const canvas = popover.querySelector('canvas');
                        if (canvas) {
                            fetch(`/history?UserID=${lastPopoverUserId}`)
                                .then(res => res.json())
                                .then(data => {
                                    historyCache[lastPopoverUserId] = data.history || [];
                                    renderUserGraph(lastPopoverUserId, canvas, false, true);
                                });
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

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

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting MarvelQuant Central Hub...")
    
    # Start the background scheduler
    start_background_scheduler()
    
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8557)