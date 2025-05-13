#!/usr/bin/env python
"""
Database fix script for StepmediaHRM
This script will:
1. Run migrations to add missing columns
2. Initialize user settings for existing users
"""

import sys
import logging
from db.migrate_db import migrate_db
from db.initialize_user_settings import initialize_user_settings

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[
                       logging.StreamHandler(),
                       logging.FileHandler("database_fix.log")
                   ])
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting database fix operations...")
    
    # Step 1: Run database migrations
    logger.info("Step 1: Running database migrations...")
    migrate_success = migrate_db()
    if not migrate_success:
        logger.error("Database migration failed. Exiting.")
        return False
        
    # Step 2: Initialize user settings for all users
    logger.info("Step 2: Initializing user settings...")
    settings_success = initialize_user_settings()
    if not settings_success:
        logger.error("User settings initialization failed.")
        return False
    
    logger.info("Database fix operations completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)