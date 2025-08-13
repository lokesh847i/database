# central_dashboard_optimized_part1.py
# Part 1: Imports and Server Setup

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
    "history": {},  # Store today's MTM history for each user: {user_id: [(timestamp, mtm_value), ...]}
    "minute_markers": {}  # Track which minutes we've already recorded data for
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
    
    # Append to history (for today) - but only once per minute to prevent overloading
    now = datetime.now()
    current_minute = now.strftime("%H:%M")
    ts = now.strftime("%H:%M:%S")
    
    if user_id not in mtm_cache["history"]:
        mtm_cache["history"][user_id] = []
        
    if user_id not in mtm_cache["minute_markers"]:
        mtm_cache["minute_markers"][user_id] = {}
    
    # Only record in history once per minute
    if current_minute not in mtm_cache["minute_markers"][user_id]:
        mtm_cache["history"][user_id].append({"timestamp": ts, "mtm": mtm_value})
        mtm_cache["minute_markers"][user_id][current_minute] = True
        logger.info(f"Added history point for {user_id} at {ts}: {mtm_value}")

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
    # Clear minute markers
    if user_id in mtm_cache["minute_markers"]:
        mtm_cache["minute_markers"][user_id] = {}

# Reset all stats
def reset_all_stats():
    for user_id in mtm_cache["stats"]:
        reset_user_stats(user_id)
    # Clear opening hour data completely
    mtm_cache["opening_mtm"] = {}
    mtm_cache["opening_hour_hit"] = {}
    # Clear minute markers
    mtm_cache["minute_markers"] = {}

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
