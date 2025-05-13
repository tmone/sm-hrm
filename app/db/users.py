from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import User, Role, user_roles
import datetime
from typing import List, Optional
from passlib.context import CryptContext

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserManager:
    def __init__(self, db: Session):
        self.db = db
        
    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
        
    def get_password_hash(self, password):
        return pwd_context.hash(password)

    def get_all_users(self):
        """Get all users with their roles"""
        return self.db.query(User).all()
    
    def get_user_by_id(self, user_id: int):
        """Get a specific user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str):
        """Get a user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str):
        """Get a user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def search_users(self, search_term: str):
        """Search users by name, email, or username"""
        search = f"%{search_term}%"
        return self.db.query(User).filter(
            (User.full_name.ilike(search)) | 
            (User.email.ilike(search)) | 
            (User.username.ilike(search))
        ).all()
    
    def create_user(self, username: str, email: str, full_name: str, password: str, is_admin: bool = False):
        """Create a new user"""
        hashed_password = self.get_password_hash(password)
        
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            is_admin=is_admin,
            is_active=True,
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user
    
    def update_user(self, user_id: int, username: str = None, email: str = None, 
                    full_name: str = None, is_active: bool = None, is_admin: bool = None):
        """Update a user's details"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
            
        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        if full_name is not None:
            user.full_name = full_name
        if is_active is not None:
            user.is_active = is_active
        if is_admin is not None:
            user.is_admin = is_admin
            
        user.updated_at = func.now()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_password(self, user_id: int, new_password: str):
        """Update a user's password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
            
        hashed_password = self.get_password_hash(new_password)
        user.hashed_password = hashed_password
        user.updated_at = func.now()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete_user(self, user_id: int):
        """Delete a user"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
            
        self.db.delete(user)
        self.db.commit()
        return True
    
    def assign_role_to_user(self, user_id: int, role_id: int):
        """Assign a role to a user"""
        user = self.get_user_by_id(user_id)
        role = self.db.query(Role).filter(Role.id == role_id).first()
        
        if not user or not role:
            return False
        
        # Check if user already has this role
        existing = self.db.query(user_roles).filter_by(
            user_id=user_id, role_id=role_id
        ).first()
        
        if not existing:
            # Add role to user
            user.roles.append(role)
            self.db.commit()
        
        return True
    
    def remove_role_from_user(self, user_id: int, role_id: int):
        """Remove a role from a user"""
        user = self.get_user_by_id(user_id)
        role = self.db.query(Role).filter(Role.id == role_id).first()
        
        if not user or not role:
            return False
        
        # Check if user has this role
        if role in user.roles:
            user.roles.remove(role)
            self.db.commit()
        
        return True
    
    def get_user_roles(self, user_id: int):
        """Get all roles for a user"""
        user = self.get_user_by_id(user_id)
        if not user:
            return []
            
        return user.roles
    
    def authenticate_user(self, username: str, password: str):
        """Authenticate a user by username and password"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user