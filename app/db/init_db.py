from sqlalchemy.orm import Session
from . import models, database, auth
import logging
import os
from dotenv import load_dotenv
from .migrate_db import migrate_db
from .initialize_user_settings import initialize_user_settings

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default admin user settings (from environment variables or defaults)
DEFAULT_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@stepmedia.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Should be changed after first login
DEFAULT_ADMIN_FULLNAME = os.getenv("ADMIN_FULLNAME", "System Administrator")

def init_db():
    """Initialize database, create tables and default admin user"""
    from . import models

    # Create tables
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Database tables created")
    
    # Run database migrations
    migrate_success = migrate_db()
    if not migrate_success:
        logger.error("Database migration failed")
        raise Exception("Database migration failed")

    # Create session
    db = database.SessionLocal()

    try:
        # Check if admin user already exists
        admin_user = db.query(models.User).filter(models.User.username == DEFAULT_ADMIN_USERNAME).first()

        if admin_user:
            logger.info(f"Admin user already exists: {DEFAULT_ADMIN_USERNAME}")

            # Update admin password if env variable changed and differs from current
            if os.getenv("ADMIN_PASSWORD"):
                # Only update if explicitly specified in env var
                hashed_password = auth.get_password_hash(DEFAULT_ADMIN_PASSWORD)
                # Can't directly compare hashed passwords, so just update
                admin_user.hashed_password = hashed_password
                db.commit()
                logger.info(f"Updated admin password from environment variable")
        else:
            # Create admin user
            hashed_password = auth.get_password_hash(DEFAULT_ADMIN_PASSWORD)
            admin_user = models.User(
                username=DEFAULT_ADMIN_USERNAME,
                email=DEFAULT_ADMIN_EMAIL,
                full_name=DEFAULT_ADMIN_FULLNAME,
                hashed_password=hashed_password,
                is_active=True,
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            logger.info(f"Created admin user: {DEFAULT_ADMIN_USERNAME} with password from environment")

            # Create admin role if it doesn't exist
            admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
            if not admin_role:
                admin_role = models.Role(
                    name="admin",
                    description="Administrator with full access"
                )
                db.add(admin_role)
                db.commit()
                db.refresh(admin_role)
                logger.info("Created admin role")

            # Assign admin role to admin user
            admin_user.roles.append(admin_role)
            db.commit()
            logger.info("Assigned admin role to admin user")
        
        # Create default roles if they don't exist
        default_roles = [
            {"name": "hr", "description": "HR staff with employee management access"},
            {"name": "manager", "description": "Manager with team management access"},
            {"name": "employee", "description": "Regular employee with limited access"}
        ]
        
        for role_data in default_roles:
            role = db.query(models.Role).filter(models.Role.name == role_data["name"]).first()
            if not role:
                role = models.Role(**role_data)
                db.add(role)
                logger.info(f"Created role: {role_data['name']}")
        
        db.commit()
        
        # Initialize user settings for all users
        initialize_user_settings()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db()