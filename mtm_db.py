# mtm_db.py
# Handles all SQLite database operations

import sqlite3
import json
from mtm_imports import logger, datetime, threading

DATABASE_FILE = "mtm_dashboard.db"

# Thread-local storage for database connections
local = threading.local()

def get_db():
    """Get a database connection for the current thread."""
    if not hasattr(local, "db"):
        local.db = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        local.db.row_factory = sqlite3.Row
    return local.db

def close_db(e=None):
    """Close the database connection for the current thread."""
    db = getattr(local, "db", None)
    if db is not None:
        db.close()
        local.db = None

def init_db():
    """Initialize the database and create tables if they don't exist."""
    db = get_db()
    cursor = db.cursor()
    
    # Create a table for application state (key-value store)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Create a table for user stats
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id TEXT PRIMARY KEY,
            max_mtm REAL NOT NULL,
            min_mtm REAL NOT NULL,
            current_mtm REAL NOT NULL
        )
    """)
    
    # Create a table for MTM history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mtm_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            mtm REAL NOT NULL
        )
    """)
    
    # Create an index on user_id and timestamp for faster history lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mtm_history_user_ts ON mtm_history (user_id, timestamp)")
    
    # Create a table for opening MTM values
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS opening_mtm (
            user_id TEXT PRIMARY KEY,
            mtm REAL NOT NULL,
            captured INTEGER NOT NULL DEFAULT 0
        )
    """)
    
    db.commit()
    logger.info("Database initialized.")

# --- App State Functions ---

def get_app_state(key, default=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT value FROM app_state WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row['value'] if row else default

def set_app_state(key, value):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)", (key, str(value)))
    db.commit()

# --- User Stats Functions ---

def get_user_stats(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user_stats WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None

def update_user_stats_db(user_id, current_mtm, max_mtm, min_mtm):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO user_stats (user_id, max_mtm, min_mtm, current_mtm)
        VALUES (?, ?, ?, ?)
    """, (user_id, max_mtm, min_mtm, current_mtm))
    db.commit()

def reset_all_stats_db():
    db = get_db()
    cursor = db.cursor()
    # Reset stats but keep users
    cursor.execute("UPDATE user_stats SET max_mtm = -999999999, min_mtm = 999999999, current_mtm = 0")
    db.commit()
    logger.info("Reset all user stats in the database.")

# --- MTM History Functions ---

def add_mtm_history(user_id, timestamp, mtm):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO mtm_history (user_id, timestamp, mtm) VALUES (?, ?, ?)", (user_id, timestamp, mtm))
    db.commit()

def get_mtm_history(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT timestamp, mtm FROM mtm_history WHERE user_id = ? ORDER BY timestamp ASC", (user_id,))
    rows = cursor.fetchall()
    return [{"timestamp": r['timestamp'], "mtm": r['mtm']} for r in rows]

def clear_history_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM mtm_history")
    db.commit()
    logger.info("Cleared MTM history from the database.")
    
# --- Opening MTM Functions ---

def get_opening_mtm(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT mtm FROM opening_mtm WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row['mtm'] if row else 0

def set_opening_mtm(user_id, mtm):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT OR REPLACE INTO opening_mtm (user_id, mtm, captured) VALUES (?, ?, 1)", (user_id, mtm))
    db.commit()
    
def is_opening_mtm_captured(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT captured FROM opening_mtm WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row['captured'] == 1 if row else False

def reset_opening_mtm_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM opening_mtm")
    db.commit()
    logger.info("Reset all opening MTM data in the database.") 