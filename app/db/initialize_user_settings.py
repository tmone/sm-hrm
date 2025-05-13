from sqlalchemy.orm import Session
import logging
from . import models, database

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_user_settings():
    """Create default user settings for any users that don't have them"""
    # Create session
    db = database.SessionLocal()
    
    try:
        # Get all users
        users = db.query(models.User).all()
        
        created_count = 0
        for user in users:
            # Check if user already has settings
            existing_settings = db.query(models.UserSettings).filter(
                models.UserSettings.user_id == user.id
            ).first()
            
            if not existing_settings:
                # Create default settings for user
                settings = models.UserSettings(
                    user_id=user.id,
                    email_notifications=True,
                    push_notifications=False,
                    leave_alerts=True
                )
                db.add(settings)
                created_count += 1
                
        if created_count > 0:
            db.commit()
            logger.info(f"Created default settings for {created_count} users")
        else:
            logger.info("All users already have settings")
            
        return True
    except Exception as e:
        logger.error(f"Error initializing user settings: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    initialize_user_settings()