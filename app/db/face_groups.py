import os
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

class FaceGroupManager:
    """
    Manages face groups for batch labeling
    
    This class provides:
    1. Group creation and management
    2. Group membership tracking
    3. Group labeling
    """
    
    def __init__(self):
        """Initialize the face group manager"""
        # Set up storage directories
        self.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
        self.groups_dir = os.path.join(self.base_dir, "face_groups")
        os.makedirs(self.groups_dir, exist_ok=True)
        
        # File for tracking groups
        self.groups_file = os.path.join(self.groups_dir, "groups.json")
        
        # Initialize or load groups data
        if os.path.exists(self.groups_file):
            with open(self.groups_file, 'r') as f:
                self.groups = json.load(f)
        else:
            self.groups = {
                "groups": {},
                "face_memberships": {},
                "last_updated": datetime.now().isoformat()
            }
            self._save_groups()
            
    def _save_groups(self):
        """Save groups data to disk"""
        with open(self.groups_file, 'w') as f:
            json.dump(self.groups, f, indent=2)
            
    def create_group(self, face_ids: List[str], similarity_score: float = 0.0) -> str:
        """
        Create a new face group
        
        Args:
            face_ids: List of face IDs to include in the group
            similarity_score: Average similarity score within the group
            
        Returns:
            ID of the created group
        """
        # Generate group ID
        group_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create group entry
        group_entry = {
            "id": group_id,
            "face_ids": face_ids,
            "similarity_score": similarity_score,
            "created": timestamp,
            "last_updated": timestamp,
            "labeled": False,
            "label": None,
            "employee_id": None
        }
        
        # Add to groups
        self.groups["groups"][group_id] = group_entry
        
        # Update face memberships
        for face_id in face_ids:
            self.groups["face_memberships"][face_id] = group_id
            
        # Update timestamp
        self.groups["last_updated"] = timestamp
        
        # Save changes
        self._save_groups()
        
        return group_id
        
    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific group"""
        return self.groups["groups"].get(group_id)
        
    def get_all_groups(self) -> List[Dict[str, Any]]:
        """Get all groups"""
        return list(self.groups["groups"].values())
        
    def get_group_for_face(self, face_id: str) -> Optional[Dict[str, Any]]:
        """Get the group that a face belongs to"""
        group_id = self.groups["face_memberships"].get(face_id)
        
        if group_id:
            return self.get_group(group_id)
            
        return None
        
    def add_faces_to_group(self, group_id: str, face_ids: List[str]) -> bool:
        """Add faces to an existing group"""
        group = self.get_group(group_id)
        
        if not group:
            return False
            
        # Add each face to the group
        for face_id in face_ids:
            if face_id not in group["face_ids"]:
                group["face_ids"].append(face_id)
                
            # Update membership
            self.groups["face_memberships"][face_id] = group_id
            
        # Update timestamp
        timestamp = datetime.now().isoformat()
        group["last_updated"] = timestamp
        self.groups["last_updated"] = timestamp
        
        # Save changes
        self._save_groups()
        
        return True
        
    def remove_face_from_group(self, group_id: str, face_id: str) -> bool:
        """Remove a face from a group"""
        group = self.get_group(group_id)
        
        if not group or face_id not in group["face_ids"]:
            return False
            
        # Remove face from group
        group["face_ids"].remove(face_id)
        
        # Remove from memberships
        if face_id in self.groups["face_memberships"]:
            del self.groups["face_memberships"][face_id]
            
        # Update timestamp
        timestamp = datetime.now().isoformat()
        group["last_updated"] = timestamp
        self.groups["last_updated"] = timestamp
        
        # Save changes
        self._save_groups()
        
        return True
        
    def label_group(self, group_id: str, employee_id: str, label: str) -> bool:
        """Label all faces in a group with an employee ID"""
        group = self.get_group(group_id)
        
        if not group:
            return False
            
        # Update group label
        group["labeled"] = True
        group["label"] = label
        group["employee_id"] = employee_id
        
        # Update timestamp
        timestamp = datetime.now().isoformat()
        group["last_updated"] = timestamp
        self.groups["last_updated"] = timestamp
        
        # Save changes
        self._save_groups()
        
        return True
        
    def create_groups_from_similarity(self, 
                                    face_data: Dict[str, Dict[str, Any]], 
                                    embeddings: Dict[str, Any],
                                    similarity_threshold: float = 0.5) -> Dict[str, List[str]]:
        """
        Create face groups based on embedding similarity
        
        Args:
            face_data: Dictionary mapping face IDs to face data
            embeddings: Dictionary mapping face IDs to face embeddings
            similarity_threshold: Threshold for grouping (0.0 to 1.0)
            
        Returns:
            Dictionary mapping group IDs to lists of face IDs
        """
        from db.face_landmarks import face_landmark_detector
        
        # Use the detector to group faces
        groups = face_landmark_detector.group_faces(embeddings, similarity_threshold)
        
        # Create database groups for each detected group
        db_groups = {}
        
        for group_id, face_ids in groups.items():
            # Create a group entry in the database
            db_group_id = self.create_group(face_ids, similarity_threshold)
            db_groups[db_group_id] = face_ids
            
        return db_groups

# Create singleton instance
face_group_manager = FaceGroupManager()