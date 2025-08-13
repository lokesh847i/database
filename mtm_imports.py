# mtm_imports.py
# File 1: Imports and setup

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
