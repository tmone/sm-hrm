import sys
import os
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_path():
    """Get the database path based on current working directory"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hrm.db")

def check_column_exists(cursor, table, column):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    for col in columns:
        if col[1] == column:
            return True
    return False

def migrate_db():
    """Run database migrations to add missing columns"""
    try:
        db_path = get_db_path()
        logger.info(f"Running database migrations on {db_path}")
        
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Migration 1: Add last_login column to users table if it doesn't exist
        if not check_column_exists(cursor, "users", "last_login"):
            logger.info("Adding last_login column to users table")
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
            conn.commit()
            logger.info("Successfully added last_login column to users table")
        else:
            logger.info("last_login column already exists in users table")
            
        # Migration 2: Add user_settings table if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        if not cursor.fetchone():
            logger.info("Creating user_settings table")
            cursor.execute("""
            CREATE TABLE user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                email_notifications BOOLEAN DEFAULT 1,
                push_notifications BOOLEAN DEFAULT 0,
                leave_alerts BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """)
            conn.commit()
            logger.info("Successfully created user_settings table")
        else:
            logger.info("user_settings table already exists")
        
        conn.close()
        logger.info("Database migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during database migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_db()
    sys.exit(0 if success else 1)