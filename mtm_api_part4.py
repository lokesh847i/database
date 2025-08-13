# mtm_api_part4.py
# File 7: API Endpoints Part 4 - Additional Endpoints

from mtm_imports import *
from mtm_cache import *
from mtm_server import *
from mtm_background import fetch_user_mtm_background
from mtm_db import get_mtm_history, reset_all_stats_db, get_user_stats, get_app_state

@app.post("/reset-all")
async def reset_all():
    """Reset stats for all users in the database"""
    logger.info("Resetting all user stats")
    reset_all_stats_db()
    # Also clear in-memory caches
    mtm_cache["stats"] = {}
    mtm_cache["opening_mtm"] = {}
    mtm_cache["opening_hour_hit"] = {}
    mtm_cache["time_markers"] = {}
    return {"status": "success", "message": "All stats reset"}

@app.get("/db-debug")
async def get_db_debug():
    """Endpoint that returns the current state of the database for debugging"""
    logger.info("Database debug endpoint accessed")
    
    users_data = get_user_data()
    users = users_data.get("users", [])
    
    debug_data = {
        "last_reset_date": get_app_state("last_reset_date"),
        "users": []
    }
    
    for user in users:
        user_id = user["userId"]
        stats = get_user_stats(user_id)
        history = get_mtm_history(user_id)
        user_info = {
            "user_id": user_id,
            "stats": stats,
            "history_points": len(history)
        }
        debug_data["users"].append(user_info)
        
    return JSONResponse(content=debug_data)

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
    """Return today's MTM history for a user from the database"""
    if not UserID:
        return JSONResponse(status_code=400, content={"status": "error", "error": "UserID parameter is required"})
    history = get_mtm_history(UserID)
    return JSONResponse(content={"status": "success", "history": history})

# Unused endpoints from the old implementation - can be removed or left as is
@app.post("/reset/{user_id}")
async def reset_stats(user_id: str):
    return {"status": "error", "message": "This endpoint is deprecated. Use /reset-all."}

@app.get("/cache-debug")
async def get_cache_debug():
    return {"status": "error", "message": "This endpoint is deprecated. Use /db-debug."}

@app.get("/time-markers")
async def get_time_markers(UserID: str = ""):
    return {"status": "error", "message": "This endpoint is deprecated."}
