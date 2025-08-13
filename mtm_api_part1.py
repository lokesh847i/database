# mtm_api_part1.py
# File 4: API Endpoints Part 1

from mtm_imports import *
from mtm_cache import *
from mtm_server import *
from mtm_html import DASHBOARD_HTML

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
