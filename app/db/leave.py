"""
Leave request manager for StepmediaHRM
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

class LeaveManager:
    """Manages leave requests in the StepmediaHRM system"""
    
    def __init__(self):
        """Initialize the leave manager"""
        self.session = next(get_db())
        
    def get_all_leave_requests(self) -> List[Dict[str, Any]]:
        """
        Get all leave requests
        
        Returns:
            List of leave requests
        """
        try:
            # Get all leave requests from the database, ordered by request date (newest first)
            requests = self.session.query(models.LeaveRequest, models.Employee)\
                .join(models.Employee, models.LeaveRequest.employee_id == models.Employee.id)\
                .order_by(desc(models.LeaveRequest.created_at))\
                .all()
            
            # Convert to serializable format
            result = []
            for leave, employee in requests:
                result.append({
                    "id": str(leave.id),
                    "employeeId": str(employee.id),
                    "employeeName": employee.name,
                    "leaveType": leave.leave_type,
                    "startDate": leave.start_date.isoformat() if leave.start_date else None,
                    "endDate": leave.end_date.isoformat() if leave.end_date else None,
                    "reason": leave.reason,
                    "status": leave.status,
                    "requestedDate": leave.created_at.isoformat() if leave.created_at else None,
                    "approvedBy": leave.approved_by,
                    "approvedDate": leave.updated_at.isoformat() if leave.updated_at and leave.status == "Approved" else None
                })
            
            return result
        except Exception as e:
            logger.exception(f"Error getting all leave requests: {str(e)}")
            return []
    
    def get_employee_leave_requests(self, employee_id: int) -> List[Dict[str, Any]]:
        """
        Get leave requests for a specific employee
        
        Args:
            employee_id: The employee ID
        
        Returns:
            List of leave requests for the employee
        """
        try:
            # Get leave requests for the employee
            requests = self.session.query(models.LeaveRequest, models.Employee)\
                .join(models.Employee, models.LeaveRequest.employee_id == models.Employee.id)\
                .filter(models.LeaveRequest.employee_id == employee_id)\
                .order_by(desc(models.LeaveRequest.created_at))\
                .all()
            
            # Convert to serializable format
            result = []
            for leave, employee in requests:
                result.append({
                    "id": str(leave.id),
                    "employeeId": str(employee.id),
                    "employeeName": employee.name,
                    "leaveType": leave.leave_type,
                    "startDate": leave.start_date.isoformat() if leave.start_date else None,
                    "endDate": leave.end_date.isoformat() if leave.end_date else None,
                    "reason": leave.reason,
                    "status": leave.status,
                    "requestedDate": leave.created_at.isoformat() if leave.created_at else None,
                    "approvedBy": leave.approved_by,
                    "approvedDate": leave.updated_at.isoformat() if leave.updated_at and leave.status == "Approved" else None
                })
            
            return result
        except Exception as e:
            logger.exception(f"Error getting leave requests for employee {employee_id}: {str(e)}")
            return []
    
    def create_leave_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new leave request
        
        Args:
            request_data: The leave request data
        
        Returns:
            The created leave request or None on error
        """
        try:
            # Get the employee
            employee_id = request_data.get("employeeId")
            employee = self.session.query(models.Employee)\
                .filter(models.Employee.id == employee_id)\
                .first()
            
            if not employee:
                logger.error(f"Employee {employee_id} not found")
                return None
            
            # Parse dates
            start_date = datetime.fromisoformat(request_data.get("startDate"))
            end_date = datetime.fromisoformat(request_data.get("endDate"))
            
            # Create new leave request
            leave_request = models.LeaveRequest(
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
                leave_type=request_data.get("leaveType"),
                reason=request_data.get("reason", ""),
                status="Pending",  # Default status is Pending
                created_at=datetime.now()
            )
            
            # Add to database
            self.session.add(leave_request)
            self.session.commit()
            self.session.refresh(leave_request)
            
            # Return the created request
            return {
                "id": str(leave_request.id),
                "employeeId": str(employee_id),
                "employeeName": employee.name,
                "leaveType": leave_request.leave_type,
                "startDate": leave_request.start_date.isoformat() if leave_request.start_date else None,
                "endDate": leave_request.end_date.isoformat() if leave_request.end_date else None,
                "reason": leave_request.reason,
                "status": leave_request.status,
                "requestedDate": leave_request.created_at.isoformat() if leave_request.created_at else None,
                "approvedBy": None,
                "approvedDate": None
            }
        except Exception as e:
            logger.exception(f"Error creating leave request: {str(e)}")
            self.session.rollback()
            return None
    
    def update_leave_request(self, request_id: int, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing leave request
        
        Args:
            request_id: The leave request ID
            request_data: The updated leave request data
        
        Returns:
            The updated leave request or None on error
        """
        try:
            # Get the leave request
            leave_request = self.session.query(models.LeaveRequest)\
                .filter(models.LeaveRequest.id == request_id)\
                .first()
            
            if not leave_request:
                logger.error(f"Leave request {request_id} not found")
                return None
            
            # Update fields
            if "startDate" in request_data:
                leave_request.start_date = datetime.fromisoformat(request_data["startDate"])
            
            if "endDate" in request_data:
                leave_request.end_date = datetime.fromisoformat(request_data["endDate"])
            
            if "leaveType" in request_data:
                leave_request.leave_type = request_data["leaveType"]
            
            if "reason" in request_data:
                leave_request.reason = request_data["reason"]
            
            if "status" in request_data:
                leave_request.status = request_data["status"]
            
            if "approvedBy" in request_data:
                leave_request.approved_by = request_data["approvedBy"]
            
            # Update timestamp
            leave_request.updated_at = datetime.now()
            
            # Commit changes
            self.session.commit()
            self.session.refresh(leave_request)
            
            # Get employee for the response
            employee = self.session.query(models.Employee)\
                .filter(models.Employee.id == leave_request.employee_id)\
                .first()
            
            # Return the updated request
            return {
                "id": str(leave_request.id),
                "employeeId": str(leave_request.employee_id),
                "employeeName": employee.name if employee else "Unknown",
                "leaveType": leave_request.leave_type,
                "startDate": leave_request.start_date.isoformat() if leave_request.start_date else None,
                "endDate": leave_request.end_date.isoformat() if leave_request.end_date else None,
                "reason": leave_request.reason,
                "status": leave_request.status,
                "requestedDate": leave_request.created_at.isoformat() if leave_request.created_at else None,
                "approvedBy": leave_request.approved_by,
                "approvedDate": leave_request.updated_at.isoformat() if leave_request.updated_at and leave_request.status == "Approved" else None
            }
        except Exception as e:
            logger.exception(f"Error updating leave request {request_id}: {str(e)}")
            self.session.rollback()
            return None
    
    def approve_leave_request(self, request_id: int, approver_id: str) -> Optional[Dict[str, Any]]:
        """
        Approve a leave request
        
        Args:
            request_id: The leave request ID
            approver_id: The ID of the user approving the request
        
        Returns:
            The updated leave request or None on error
        """
        try:
            # Get the leave request
            leave_request = self.session.query(models.LeaveRequest)\
                .filter(models.LeaveRequest.id == request_id)\
                .first()
            
            if not leave_request:
                logger.error(f"Leave request {request_id} not found")
                return None
            
            # Update fields
            leave_request.status = "Approved"
            leave_request.approved_by = approver_id
            leave_request.updated_at = datetime.now()
            
            # Commit changes
            self.session.commit()
            self.session.refresh(leave_request)
            
            # Get employee for the response
            employee = self.session.query(models.Employee)\
                .filter(models.Employee.id == leave_request.employee_id)\
                .first()
            
            # Return the updated request
            return {
                "id": str(leave_request.id),
                "employeeId": str(leave_request.employee_id),
                "employeeName": employee.name if employee else "Unknown",
                "leaveType": leave_request.leave_type,
                "startDate": leave_request.start_date.isoformat() if leave_request.start_date else None,
                "endDate": leave_request.end_date.isoformat() if leave_request.end_date else None,
                "reason": leave_request.reason,
                "status": leave_request.status,
                "requestedDate": leave_request.created_at.isoformat() if leave_request.created_at else None,
                "approvedBy": leave_request.approved_by,
                "approvedDate": leave_request.updated_at.isoformat()
            }
        except Exception as e:
            logger.exception(f"Error approving leave request {request_id}: {str(e)}")
            self.session.rollback()
            return None
    
    def reject_leave_request(self, request_id: int, reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Reject a leave request
        
        Args:
            request_id: The leave request ID
            reason: The reason for rejection (optional)
        
        Returns:
            The updated leave request or None on error
        """
        try:
            # Get the leave request
            leave_request = self.session.query(models.LeaveRequest)\
                .filter(models.LeaveRequest.id == request_id)\
                .first()
            
            if not leave_request:
                logger.error(f"Leave request {request_id} not found")
                return None
            
            # Update fields
            leave_request.status = "Rejected"
            if reason:
                leave_request.reason = leave_request.reason + f"\nRejection reason: {reason}"
            leave_request.updated_at = datetime.now()
            
            # Commit changes
            self.session.commit()
            self.session.refresh(leave_request)
            
            # Get employee for the response
            employee = self.session.query(models.Employee)\
                .filter(models.Employee.id == leave_request.employee_id)\
                .first()
            
            # Return the updated request
            return {
                "id": str(leave_request.id),
                "employeeId": str(leave_request.employee_id),
                "employeeName": employee.name if employee else "Unknown",
                "leaveType": leave_request.leave_type,
                "startDate": leave_request.start_date.isoformat() if leave_request.start_date else None,
                "endDate": leave_request.end_date.isoformat() if leave_request.end_date else None,
                "reason": leave_request.reason,
                "status": leave_request.status,
                "requestedDate": leave_request.created_at.isoformat() if leave_request.created_at else None,
                "approvedBy": None,
                "approvedDate": None
            }
        except Exception as e:
            logger.exception(f"Error rejecting leave request {request_id}: {str(e)}")
            self.session.rollback()
            return None
    
    def delete_leave_request(self, request_id: int) -> bool:
        """
        Delete a leave request
        
        Args:
            request_id: The leave request ID
        
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Get the leave request
            leave_request = self.session.query(models.LeaveRequest)\
                .filter(models.LeaveRequest.id == request_id)\
                .first()
            
            if not leave_request:
                logger.error(f"Leave request {request_id} not found")
                return False
            
            # Delete the request
            self.session.delete(leave_request)
            self.session.commit()
            
            return True
        except Exception as e:
            logger.exception(f"Error deleting leave request {request_id}: {str(e)}")
            self.session.rollback()
            return False

# Create singleton instance
leave_manager = LeaveManager()