"""
Attendance data manager for StepmediaHRM
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from sqlalchemy import func, and_, or_, desc
from db.database import get_db
from db import models

logger = logging.getLogger(__name__)

class AttendanceManager:
    """Manages attendance data in the StepmediaHRM system"""
    
    def __init__(self):
        """Initialize the attendance manager"""
        self.session = next(get_db())
        
    def get_all_attendance(self) -> List[Dict[str, Any]]:
        """
        Get all attendance records
        
        Returns:
            List of attendance records
        """
        try:
            # Get all attendance records from the database, ordered by date (newest first)
            records = self.session.query(models.Attendance, models.Employee)\
                .join(models.Employee, models.Attendance.employee_id == models.Employee.id)\
                .order_by(desc(models.Attendance.date))\
                .all()
            
            # Convert to serializable format
            result = []
            for attendance, employee in records:
                result.append({
                    "id": str(attendance.id),
                    "employeeId": str(employee.id),
                    "employeeName": employee.name,
                    "date": attendance.date.isoformat() if attendance.date else None,
                    "checkInTime": attendance.check_in.isoformat() if attendance.check_in else None,
                    "checkOutTime": attendance.check_out.isoformat() if attendance.check_out else None,
                    "status": attendance.status,
                    "notes": attendance.notes
                })
            
            return result
        except Exception as e:
            logger.exception(f"Error getting all attendance records: {str(e)}")
            return []
    
    def get_attendance_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """
        Get attendance records for a specific date
        
        Args:
            date_str: The date in ISO format (YYYY-MM-DD)
        
        Returns:
            List of attendance records for the date
        """
        try:
            # Parse the date string
            date = datetime.fromisoformat(date_str)
            
            # Get attendance records for the date
            records = self.session.query(models.Attendance, models.Employee)\
                .join(models.Employee, models.Attendance.employee_id == models.Employee.id)\
                .filter(func.date(models.Attendance.date) == date.date())\
                .all()
            
            # Convert to serializable format
            result = []
            for attendance, employee in records:
                result.append({
                    "id": str(attendance.id),
                    "employeeId": str(employee.id),
                    "employeeName": employee.name,
                    "date": attendance.date.isoformat() if attendance.date else None,
                    "checkInTime": attendance.check_in.isoformat() if attendance.check_in else None,
                    "checkOutTime": attendance.check_out.isoformat() if attendance.check_out else None,
                    "status": attendance.status,
                    "notes": attendance.notes
                })
            
            return result
        except Exception as e:
            logger.exception(f"Error getting attendance records for date {date_str}: {str(e)}")
            return []
    
    def create_attendance(self, attendance_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new attendance record
        
        Args:
            attendance_data: The attendance data
        
        Returns:
            The created attendance record or None on error
        """
        try:
            # Get the employee
            employee_id = attendance_data.get("employeeId")
            employee = self.session.query(models.Employee)\
                .filter(models.Employee.id == employee_id)\
                .first()
            
            if not employee:
                logger.error(f"Employee {employee_id} not found")
                return None
            
            # Parse date and times
            date = datetime.fromisoformat(attendance_data.get("date", datetime.now().isoformat()))
            check_in = None
            check_out = None
            
            if "checkInTime" in attendance_data and attendance_data["checkInTime"]:
                check_in = datetime.fromisoformat(attendance_data["checkInTime"])
            
            if "checkOutTime" in attendance_data and attendance_data["checkOutTime"]:
                check_out = datetime.fromisoformat(attendance_data["checkOutTime"])
            
            # Determine status based on check-in time
            status = "Present"
            if check_in:
                # Example: if check-in after 9:00 AM, mark as Late
                if check_in.hour >= 9 and check_in.minute > 0:
                    status = "Late"
            elif "status" in attendance_data:
                status = attendance_data["status"]
            else:
                status = "Absent"
            
            # Create new attendance record
            attendance = models.Attendance(
                employee_id=employee_id,
                date=date,
                check_in=check_in,
                check_out=check_out,
                status=status,
                notes=attendance_data.get("notes", "")
            )
            
            # Add to database
            self.session.add(attendance)
            self.session.commit()
            self.session.refresh(attendance)
            
            # Return the created record
            return {
                "id": str(attendance.id),
                "employeeId": str(employee_id),
                "employeeName": employee.name,
                "date": attendance.date.isoformat() if attendance.date else None,
                "checkInTime": attendance.check_in.isoformat() if attendance.check_in else None,
                "checkOutTime": attendance.check_out.isoformat() if attendance.check_out else None,
                "status": attendance.status,
                "notes": attendance.notes
            }
        except Exception as e:
            logger.exception(f"Error creating attendance record: {str(e)}")
            self.session.rollback()
            return None
    
    def update_attendance(self, attendance_id: int, attendance_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing attendance record
        
        Args:
            attendance_id: The attendance record ID
            attendance_data: The updated attendance data
        
        Returns:
            The updated attendance record or None on error
        """
        try:
            # Get the attendance record
            attendance = self.session.query(models.Attendance)\
                .filter(models.Attendance.id == attendance_id)\
                .first()
            
            if not attendance:
                logger.error(f"Attendance record {attendance_id} not found")
                return None
            
            # Update fields
            if "date" in attendance_data:
                attendance.date = datetime.fromisoformat(attendance_data["date"])
            
            if "checkInTime" in attendance_data:
                attendance.check_in = datetime.fromisoformat(attendance_data["checkInTime"]) if attendance_data["checkInTime"] else None
            
            if "checkOutTime" in attendance_data:
                attendance.check_out = datetime.fromisoformat(attendance_data["checkOutTime"]) if attendance_data["checkOutTime"] else None
            
            if "status" in attendance_data:
                attendance.status = attendance_data["status"]
            
            if "notes" in attendance_data:
                attendance.notes = attendance_data["notes"]
            
            # Commit changes
            self.session.commit()
            self.session.refresh(attendance)
            
            # Get employee for the response
            employee = self.session.query(models.Employee)\
                .filter(models.Employee.id == attendance.employee_id)\
                .first()
            
            # Return the updated record
            return {
                "id": str(attendance.id),
                "employeeId": str(attendance.employee_id),
                "employeeName": employee.name if employee else "Unknown",
                "date": attendance.date.isoformat() if attendance.date else None,
                "checkInTime": attendance.check_in.isoformat() if attendance.check_in else None,
                "checkOutTime": attendance.check_out.isoformat() if attendance.check_out else None,
                "status": attendance.status,
                "notes": attendance.notes
            }
        except Exception as e:
            logger.exception(f"Error updating attendance record {attendance_id}: {str(e)}")
            self.session.rollback()
            return None
    
    def delete_attendance(self, attendance_id: int) -> bool:
        """
        Delete an attendance record
        
        Args:
            attendance_id: The attendance record ID
        
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Get the attendance record
            attendance = self.session.query(models.Attendance)\
                .filter(models.Attendance.id == attendance_id)\
                .first()
            
            if not attendance:
                logger.error(f"Attendance record {attendance_id} not found")
                return False
            
            # Delete the record
            self.session.delete(attendance)
            self.session.commit()
            
            return True
        except Exception as e:
            logger.exception(f"Error deleting attendance record {attendance_id}: {str(e)}")
            self.session.rollback()
            return False

# Create singleton instance
attendance_manager = AttendanceManager()