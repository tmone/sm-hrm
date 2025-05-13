"""
Employees data manager for StepmediaHRM
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from sqlalchemy import func, and_, or_
from db.database import get_db
from db import models

logger = logging.getLogger(__name__)

class EmployeesManager:
    """Manages employee data in the StepmediaHRM system"""
    
    def __init__(self):
        """Initialize the employees manager"""
        self.session = next(get_db())
        
    def get_all_employees(self) -> List[Dict[str, Any]]:
        """
        Get all employees with basic information
        
        Returns:
            List of employees with their details
        """
        try:
            # Get all employees from the database
            employees = self.session.query(models.Employee).all()
            
            # Convert to serializable format
            result = []
            for emp in employees:
                # Check if employee has facial data
                has_face = self.session.query(models.FacialData)\
                    .filter(models.FacialData.employee_id == emp.id)\
                    .first() is not None
                
                result.append({
                    "id": str(emp.id),
                    "name": emp.name,
                    "firstName": emp.name.split()[0] if emp.name else "",
                    "lastName": " ".join(emp.name.split()[1:]) if emp.name and len(emp.name.split()) > 1 else "",
                    "department": emp.department,
                    "position": emp.position,
                    "email": emp.email,
                    "phone": emp.phone or "",
                    "hireDate": emp.hire_date.isoformat() if emp.hire_date else "",
                    "status": emp.status,
                    "avatarUrl": emp.facial_data.image_path if hasattr(emp, 'facial_data') and emp.facial_data else None,
                    "hasFacialData": has_face
                })
            
            return result
        except Exception as e:
            logger.exception(f"Error getting all employees: {str(e)}")
            return []
    
    def search_employees(self, query: str) -> List[Dict[str, Any]]:
        """
        Search employees by name, department, position, etc.
        
        Args:
            query: The search query string
        
        Returns:
            List of employees matching the search
        """
        try:
            # Prepare the search query
            search = f"%{query}%"
            
            # Search for employees
            employees = self.session.query(models.Employee)\
                .filter(
                    or_(
                        models.Employee.name.ilike(search),
                        models.Employee.employee_id.ilike(search),
                        models.Employee.department.ilike(search),
                        models.Employee.position.ilike(search),
                        models.Employee.email.ilike(search)
                    )
                ).all()
            
            # Convert to serializable format (same as get_all_employees)
            result = []
            for emp in employees:
                # Check if employee has facial data
                has_face = self.session.query(models.FacialData)\
                    .filter(models.FacialData.employee_id == emp.id)\
                    .first() is not None
                
                result.append({
                    "id": str(emp.id),
                    "name": emp.name,
                    "firstName": emp.name.split()[0] if emp.name else "",
                    "lastName": " ".join(emp.name.split()[1:]) if emp.name and len(emp.name.split()) > 1 else "",
                    "department": emp.department,
                    "position": emp.position,
                    "email": emp.email,
                    "phone": emp.phone or "",
                    "hireDate": emp.hire_date.isoformat() if emp.hire_date else "",
                    "status": emp.status,
                    "avatarUrl": emp.facial_data.image_path if hasattr(emp, 'facial_data') and emp.facial_data else None,
                    "hasFacialData": has_face
                })
            
            return result
        except Exception as e:
            logger.exception(f"Error searching employees: {str(e)}")
            return []
    
    def get_employee_by_id(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single employee by ID
        
        Args:
            employee_id: The employee ID
        
        Returns:
            Employee details or None if not found
        """
        try:
            # Get employee by ID
            emp = self.session.query(models.Employee)\
                .filter(models.Employee.id == employee_id)\
                .first()
            
            if not emp:
                return None
            
            # Check if employee has facial data
            facial_data = self.session.query(models.FacialData)\
                .filter(models.FacialData.employee_id == emp.id)\
                .first()
            
            # Convert to serializable format
            return {
                "id": str(emp.id),
                "name": emp.name,
                "firstName": emp.name.split()[0] if emp.name else "",
                "lastName": " ".join(emp.name.split()[1:]) if emp.name and len(emp.name.split()) > 1 else "",
                "department": emp.department,
                "position": emp.position,
                "email": emp.email,
                "phone": emp.phone or "",
                "hireDate": emp.hire_date.isoformat() if emp.hire_date else "",
                "status": emp.status,
                "avatarUrl": facial_data.image_path if facial_data else None,
                "hasFacialData": facial_data is not None
            }
        except Exception as e:
            logger.exception(f"Error getting employee by ID {employee_id}: {str(e)}")
            return None
    
    def create_employee(self, employee_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new employee
        
        Args:
            employee_data: The employee data
        
        Returns:
            The created employee or None on error
        """
        try:
            # Create new employee instance
            emp = models.Employee(
                employee_id=employee_data.get("employee_id", f"EMP{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                name=employee_data.get("name", ""),
                position=employee_data.get("position", ""),
                department=employee_data.get("department", ""),
                email=employee_data.get("email", ""),
                phone=employee_data.get("phone", ""),
                hire_date=datetime.fromisoformat(employee_data.get("hireDate", datetime.now().isoformat())),
                status=employee_data.get("status", "Active"),
                address=employee_data.get("address", "")
            )
            
            # Add to database
            self.session.add(emp)
            self.session.commit()
            self.session.refresh(emp)
            
            # Return the created employee
            return self.get_employee_by_id(emp.id)
        except Exception as e:
            logger.exception(f"Error creating employee: {str(e)}")
            self.session.rollback()
            return None
    
    def update_employee(self, employee_id: int, employee_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing employee
        
        Args:
            employee_id: The employee ID
            employee_data: The updated employee data
        
        Returns:
            The updated employee or None on error
        """
        try:
            # Get employee by ID
            emp = self.session.query(models.Employee)\
                .filter(models.Employee.id == employee_id)\
                .first()
            
            if not emp:
                return None
            
            # Update fields
            if "name" in employee_data:
                emp.name = employee_data["name"]
            if "position" in employee_data:
                emp.position = employee_data["position"]
            if "department" in employee_data:
                emp.department = employee_data["department"]
            if "email" in employee_data:
                emp.email = employee_data["email"]
            if "phone" in employee_data:
                emp.phone = employee_data["phone"]
            if "hireDate" in employee_data:
                emp.hire_date = datetime.fromisoformat(employee_data["hireDate"])
            if "status" in employee_data:
                emp.status = employee_data["status"]
            if "address" in employee_data:
                emp.address = employee_data["address"]
            
            # Commit changes
            self.session.commit()
            self.session.refresh(emp)
            
            # Return the updated employee
            return self.get_employee_by_id(emp.id)
        except Exception as e:
            logger.exception(f"Error updating employee {employee_id}: {str(e)}")
            self.session.rollback()
            return None
    
    def delete_employee(self, employee_id: int) -> bool:
        """
        Delete an employee
        
        Args:
            employee_id: The employee ID
        
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Get employee by ID
            emp = self.session.query(models.Employee)\
                .filter(models.Employee.id == employee_id)\
                .first()
            
            if not emp:
                return False
            
            # Delete the employee
            self.session.delete(emp)
            self.session.commit()
            
            return True
        except Exception as e:
            logger.exception(f"Error deleting employee {employee_id}: {str(e)}")
            self.session.rollback()
            return False

# Create singleton instance
employees_manager = EmployeesManager()