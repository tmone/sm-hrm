from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import User, UserSettings
from typing import Dict, Any, Optional

class UserSettingsManager:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get settings for a specific user"""
        # Check if user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Get settings or create default ones
        settings = self.db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        
        if not settings:
            # Create default settings
            settings = UserSettings(
                user_id=user_id,
                email_notifications=True,
                push_notifications=False,
                leave_alerts=True
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        
        return {
            "email_notifications": settings.email_notifications,
            "push_notifications": settings.push_notifications,
            "leave_alerts": settings.leave_alerts
        }
    
    def update_user_settings(self, user_id: int, settings_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update settings for a specific user"""
        # Check if user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Get settings or create if they don't exist
        settings = self.db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        
        if not settings:
            # Create new settings
            settings = UserSettings(
                user_id=user_id,
                email_notifications=settings_data.get("email_notifications", True),
                push_notifications=settings_data.get("push_notifications", False),
                leave_alerts=settings_data.get("leave_alerts", True)
            )
            self.db.add(settings)
        else:
            # Update existing settings
            if "email_notifications" in settings_data:
                settings.email_notifications = settings_data["email_notifications"]
            if "push_notifications" in settings_data:
                settings.push_notifications = settings_data["push_notifications"]
            if "leave_alerts" in settings_data:
                settings.leave_alerts = settings_data["leave_alerts"]
            
            settings.updated_at = func.now()
        
        self.db.commit()
        self.db.refresh(settings)
        
        return {
            "email_notifications": settings.email_notifications,
            "push_notifications": settings.push_notifications,
            "leave_alerts": settings.leave_alerts
        }