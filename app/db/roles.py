from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import Role, User, user_roles
from typing import List, Optional

class RoleManager:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_roles(self):
        """Get all roles"""
        return self.db.query(Role).all()
    
    def get_role_by_id(self, role_id: int):
        """Get a specific role by ID"""
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    def get_role_by_name(self, name: str):
        """Get a role by name"""
        return self.db.query(Role).filter(Role.name == name).first()
    
    def search_roles(self, search_term: str):
        """Search roles by name or description"""
        search = f"%{search_term}%"
        return self.db.query(Role).filter(
            (Role.name.ilike(search)) | 
            (Role.description.ilike(search))
        ).all()
    
    def create_role(self, name: str, description: str = None):
        """Create a new role"""
        new_role = Role(
            name=name,
            description=description
        )
        
        self.db.add(new_role)
        self.db.commit()
        self.db.refresh(new_role)
        return new_role
    
    def update_role(self, role_id: int, name: str = None, description: str = None):
        """Update a role's details"""
        role = self.get_role_by_id(role_id)
        if not role:
            return None
            
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
            
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def delete_role(self, role_id: int):
        """Delete a role"""
        role = self.get_role_by_id(role_id)
        if not role:
            return False
            
        self.db.delete(role)
        self.db.commit()
        return True
    
    def get_users_with_role(self, role_id: int):
        """Get all users with a specific role"""
        role = self.get_role_by_id(role_id)
        if not role:
            return []
            
        return role.users
    
    def get_user_count_for_role(self, role_id: int):
        """Get the count of users with a specific role"""
        role = self.get_role_by_id(role_id)
        if not role:
            return 0
            
        return len(role.users)
    
    def get_roles_with_user_counts(self):
        """Get all roles with their user counts"""
        roles = self.get_all_roles()
        result = []
        
        for role in roles:
            user_count = len(role.users)
            role_data = {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "user_count": user_count
            }
            result.append(role_data)
            
        return result