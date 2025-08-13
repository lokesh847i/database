# mtm_db_stabilized.py
# Optimized SQLite database operations with connection pooling and performance improvements

import sqlite3
import json
import threading
import queue
from contextlib import contextmanager
from mtm_imports import logger, datetime

DATABASE_FILE = "mtm_dashboard.db"

# Connection pool for better performance
class DatabasePool:
    def __init__(self, max_connections=5):
        self.max_connections = max_connections
        self.connections = queue.Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        
        # Initialize connections
        for _ in range(max_connections):
            conn = self._create_connection()
            if conn:
                self.connections.put(conn)
    
    def _create_connection(self):
        """Create a new database connection with optimized settings."""
        try:
            conn = sqlite3.connect(
                DATABASE_FILE, 
                check_same_thread=False,
                timeout=30.0,  # Increased timeout
                isolation_level=None  # Autocommit mode
            )
            
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")  # Faster than FULL
            conn.execute("PRAGMA cache_size=10000")    # Larger cache
            conn.execute("PRAGMA temp_store=MEMORY")   # Use memory for temp tables
            conn.execute("PRAGMA mmap_size=268435456") # 256MB memory mapping
            
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Error creating database connection: {str(e)}")
            return None
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool with context management."""
        conn = None
        try:
            conn = self.connections.get(timeout=5.0)
            yield conn
        except queue.Empty:
            logger.warning("No database connections available, creating new one")
            conn = self._create_connection()
            if conn:
                yield conn
            else:
                raise Exception("Failed to create database connection")
        except Exception as e:
            logger.error(f"Database operation error: {str(e)}")
            raise
        finally:
            if conn:
                try:
                    self.connections.put(conn, timeout=1.0)
                except queue.Full:
                    # If pool is full, close the connection
                    conn.close()

# Global database pool
db_pool = DatabasePool()

def init_db():
    """Initialize the database and create tables if they don't exist."""
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        
        # Create a table for application state (key-value store)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Create a table for user stats with better indexing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id TEXT PRIMARY KEY,
                max_mtm REAL NOT NULL,
                min_mtm REAL NOT NULL,
                current_mtm REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create a table for MTM history with partitioning
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mtm_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                mtm REAL NOT NULL,
                date TEXT NOT NULL
            )
        """)
        
        # Create optimized indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mtm_history_user_ts ON mtm_history (user_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mtm_history_date ON mtm_history (date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_stats_updated ON user_stats (last_updated)")
        
        # Create a table for opening MTM values
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS opening_mtm (
                user_id TEXT PRIMARY KEY,
                mtm REAL NOT NULL,
                captured INTEGER NOT NULL DEFAULT 0,
                captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.commit()
        logger.info("Database initialized with optimized settings.")

# --- App State Functions ---

def get_app_state(key, default=None):
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT value FROM app_state WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else default

def set_app_state(key, value):
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        cursor.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)", (key, str(value)))
        db.commit()

# --- User Stats Functions ---

def get_user_stats(user_id):
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM user_stats WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def update_user_stats_db(user_id, current_mtm, max_mtm, min_mtm):
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_stats (user_id, max_mtm, min_mtm, current_mtm, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, max_mtm, min_mtm, current_mtm))
        db.commit()

def reset_all_stats_db():
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        cursor.execute("UPDATE user_stats SET max_mtm = -999999999, min_mtm = 999999999, current_mtm = 0, last_updated = CURRENT_TIMESTAMP")
        db.commit()
        logger.info("Reset all user stats in the database.")

# --- MTM History Functions ---

def add_mtm_history(user_id, timestamp, mtm):
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        # Extract date for partitioning
        date = timestamp.split(' ')[0] if ' ' in timestamp else datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO mtm_history (user_id, timestamp, mtm, date) VALUES (?, ?, ?, ?)", 
                      (user_id, timestamp, mtm, date))
        db.commit()

def get_mtm_history(user_id, limit=1000):
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT timestamp, mtm FROM mtm_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        return [{"timestamp": r['timestamp'], "mtm": r['mtm']} for r in rows]

def clear_history_db():
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        cursor.execute("DELETE FROM mtm_history")
        db.commit()
        logger.info("Cleared MTM history from the database.")

def cleanup_old_history(days_to_keep=7):
    """Clean up old history data to prevent database bloat."""
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")
        cursor.execute("DELETE FROM mtm_history WHERE date < ?", (cutoff_date,))
        deleted_count = cursor.rowcount
        db.commit()
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old history records")
        
# --- Opening MTM Functions ---

def get_opening_mtm(user_id):
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT mtm FROM opening_mtm WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row['mtm'] if row else 0

def set_opening_mtm(user_id, mtm):
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO opening_mtm (user_id, mtm, captured, captured_at) 
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
        """, (user_id, mtm))
        db.commit()
        
def is_opening_mtm_captured(user_id):
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT captured FROM opening_mtm WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row['captured'] == 1 if row else False

def reset_opening_mtm_db():
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        cursor.execute("DELETE FROM opening_mtm")
        db.commit()
        logger.info("Reset all opening MTM data in the database.")

# --- Performance Monitoring ---

def get_database_stats():
    """Get database performance statistics."""
    with db_pool.get_connection() as db:
        cursor = db.cursor()
        
        # Get table sizes
        cursor.execute("SELECT COUNT(*) as count FROM user_stats")
        user_stats_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM mtm_history")
        history_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM opening_mtm")
        opening_mtm_count = cursor.fetchone()['count']
        
        # Get database file size
        import os
        db_size = os.path.getsize(DATABASE_FILE) if os.path.exists(DATABASE_FILE) else 0
        
        return {
            "user_stats_count": user_stats_count,
            "history_count": history_count,
            "opening_mtm_count": opening_mtm_count,
            "database_size_mb": round(db_size / (1024 * 1024), 2),
            "connection_pool_size": db_pool.connections.qsize()
        }

# Initialize database on import
init_db() 