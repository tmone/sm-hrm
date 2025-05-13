"""
Dashboard data manager for StepmediaHRM
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from sqlalchemy import func, and_, or_
from db.database import get_db
from db import models, uploads, face_cache, identity_groups

logger = logging.getLogger(__name__)

class DashboardManager:
    """Manages dashboard data in the StepmediaHRM system"""
    
    def __init__(self):
        """Initialize the dashboard manager"""
        self.session = next(get_db())
        
    def get_summary_metrics(self) -> Dict[str, Any]:
        """
        Get dashboard summary metrics
        
        Returns:
            Dict containing summary metrics for the dashboard
        """
        try:
            # Get total active employees
            total_employees = self.session.query(models.Employee)\
                .filter(models.Employee.status != 'Terminated')\
                .count()
            
            # Get employees hired this month
            now = datetime.now()
            start_of_month = datetime(now.year, now.month, 1)
            new_employees_this_month = self.session.query(models.Employee)\
                .filter(models.Employee.hire_date >= start_of_month)\
                .count()
            
            # Get today's date for filtering
            today = datetime.now().date()
            today_datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get employees on leave today (from LeaveRequest table)
            on_leave_today = self.session.query(models.LeaveRequest)\
                .filter(models.LeaveRequest.status == 'Approved')\
                .filter(models.LeaveRequest.start_date <= today_datetime)\
                .filter(models.LeaveRequest.end_date >= today_datetime)\
                .count()
            
            # Get employees present today (from Attendance table)
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
            
            present_today = self.session.query(models.Attendance)\
                .filter(models.Attendance.date.between(today_start, today_end))\
                .filter(models.Attendance.status.in_(['Present', 'Late']))\
                .count()
            
            # Get pending leave requests
            pending_leave_requests = self.session.query(models.LeaveRequest)\
                .filter(models.LeaveRequest.status == 'Pending')\
                .count()
            
            # Get face registration statistics
            total_faces = self.session.query(models.FacialData).count()
            approved_faces = self.session.query(models.FacialData)\
                .filter(models.FacialData.is_approved == True)\
                .count()
            
            return {
                "totalEmployees": total_employees,
                "newEmployeesThisMonth": new_employees_this_month,
                "onLeaveToday": on_leave_today,
                "presentToday": present_today,
                "pendingLeaveRequests": pending_leave_requests,
                "registeredFaces": {
                    "total": total_faces,
                    "approved": approved_faces
                }
            }
        except Exception as e:
            logger.exception(f"Error getting dashboard summary metrics: {str(e)}")
            # Return empty metrics on error
            return {
                "totalEmployees": 0,
                "newEmployeesThisMonth": 0,
                "onLeaveToday": 0,
                "presentToday": 0,
                "pendingLeaveRequests": 0,
                "registeredFaces": {
                    "total": 0,
                    "approved": 0
                }
            }
    
    def get_today_attendance(self) -> List[Dict[str, Any]]:
        """
        Get today's attendance records
        
        Returns:
            List of attendance records for today
        """
        try:
            # Get today's date for filtering
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Get attendance records
            attendance_records = self.session.query(models.Attendance, models.Employee)\
                .join(models.Employee, models.Attendance.employee_id == models.Employee.id)\
                .filter(models.Attendance.date.between(today_start, today_end))\
                .all()
            
            # Convert to serializable format
            result = []
            for attendance, employee in attendance_records:
                result.append({
                    "id": str(attendance.id),
                    "employeeId": str(employee.id),
                    "employeeName": employee.name,
                    "date": attendance.date,
                    "checkInTime": attendance.check_in.isoformat() if attendance.check_in else None,
                    "checkOutTime": attendance.check_out.isoformat() if attendance.check_out else None,
                    "status": attendance.status,
                    "notes": attendance.notes
                })
            
            return result
        except Exception as e:
            logger.exception(f"Error getting today's attendance: {str(e)}")
            return []
    
    def get_upcoming_leaves(self) -> List[Dict[str, Any]]:
        """
        Get upcoming approved leave requests
        
        Returns:
            List of upcoming approved leave requests
        """
        try:
            # Get today's date for filtering
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get upcoming leave requests
            leave_requests = self.session.query(models.LeaveRequest, models.Employee)\
                .join(models.Employee, models.LeaveRequest.employee_id == models.Employee.id)\
                .filter(models.LeaveRequest.status == 'Approved')\
                .filter(models.LeaveRequest.start_date >= today)\
                .order_by(models.LeaveRequest.start_date)\
                .all()
            
            # Convert to serializable format
            result = []
            for leave, employee in leave_requests:
                result.append({
                    "id": str(leave.id),
                    "employeeId": str(employee.id),
                    "employeeName": employee.name,
                    "leaveType": leave.leave_type,
                    "startDate": leave.start_date,
                    "endDate": leave.end_date,
                    "reason": leave.reason,
                    "status": leave.status,
                    "requestedDate": leave.requested_at.isoformat() if leave.requested_at else None,
                    "approvedBy": leave.approved_by,
                    "approvedDate": leave.approved_at.isoformat() if leave.approved_at else None
                })
            
            return result
        except Exception as e:
            logger.exception(f"Error getting upcoming leaves: {str(e)}")
            return []
    
    def get_upcoming_absences_data(self) -> List[Dict[str, Any]]:
        """
        Get data for upcoming absences for the next 7 days
        
        Returns:
            List of data points for upcoming absences
        """
        try:
            # Get today's date for filtering
            today = datetime.now().date()
            
            # Prepare result data
            result = []
            
            # For each of the next 7 days
            for i in range(7):
                target_date = today + timedelta(days=i)
                target_date_start = datetime.combine(target_date, datetime.min.time())
                target_date_end = datetime.combine(target_date, datetime.max.time())
                target_date_str = target_date.isoformat()
                
                # Get count of approved leave requests for this day
                absent_count = self.session.query(models.LeaveRequest)\
                    .filter(models.LeaveRequest.status == 'Approved')\
                    .filter(models.LeaveRequest.start_date <= target_date_end)\
                    .filter(models.LeaveRequest.end_date >= target_date_start)\
                    .count()
                
                # Add to result
                result.append({
                    "date": target_date.strftime('%b %d'),
                    "fullDate": target_date_str,
                    "absentCount": absent_count
                })
            
            return result
        except Exception as e:
            logger.exception(f"Error getting upcoming absences data: {str(e)}")
            return []

# Create singleton instance
dashboard_manager = DashboardManager()