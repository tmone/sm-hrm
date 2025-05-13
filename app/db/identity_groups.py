import os
import json
import uuid
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

class IdentityGroupManager:
    """
    Manages identity groups for manual face grouping
    
    This class provides:
    1. Identity code generation (PERSON-XXXX)
    2. Manual grouping of faces across videos
    3. Tracking of best quality faces per identity
    """
    
    def __init__(self):
        """Initialize the identity group manager"""
        # Set up storage directories
        self.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
        self.identity_dir = os.path.join(self.base_dir, "identity_groups")
        os.makedirs(self.identity_dir, exist_ok=True)
        
        # File for tracking identity groups
        self.identities_file = os.path.join(self.identity_dir, "identities.json")
        print(f"Identity groups file path: {self.identities_file}")
        
        # Initialize or load identity data
        try:
            if os.path.exists(self.identities_file):
                with open(self.identities_file, 'r') as f:
                    self.identities = json.load(f)
                print(f"Loaded existing identity data with {len(self.identities.get('groups', {}))} groups")
            else:
                self.identities = {
                    "groups": {},
                    "face_memberships": {},
                    "last_updated": datetime.now().isoformat(),
                    "next_identity_number": 1  # Used for auto-incrementing identity codes
                }
                self._save_identities()
                print("Created new identity data file")
        except Exception as e:
            print(f"Error initializing identity group manager: {str(e)}")
            # Ensure we at least have a valid structure
            self.identities = {
                "groups": {},
                "face_memberships": {},
                "last_updated": datetime.now().isoformat(),
                "next_identity_number": 1
            }
            
    def _save_identities(self):
        """Save identity data to disk"""
        try:
            os.makedirs(os.path.dirname(self.identities_file), exist_ok=True)
            with open(self.identities_file, 'w') as f:
                json.dump(self.identities, f, indent=2)
            print(f"Successfully saved identity data to {self.identities_file}")
        except Exception as e:
            print(f"Error saving identity data: {str(e)}")
            
    def generate_identity_code(self) -> str:
        """
        Generate a new unique identity code (PERSON-XXXX format)
        
        Returns:
            New identity code string
        """
        # Get next number and increment
        next_num = self.identities.get("next_identity_number", 1)
        
        # Format the code
        code = f"PERSON-{next_num:04d}"
        
        # Increment for next time
        self.identities["next_identity_number"] = next_num + 1
        self._save_identities()
        
        return code
            
    def create_identity(self, face_ids: List[str], name: Optional[str] = None, primary_face_id: Optional[str] = None, video_ids: Optional[List[str]] = None) -> str:
        """
        Create a new identity group
        
        Args:
            face_ids: List of face IDs to include in the identity
            name: Optional human-readable name for the identity
            primary_face_id: Optional ID of the primary (best quality) face
            video_ids: Optional list of videos these faces appear in
            
        Returns:
            ID of the created identity (PERSON-XXXX)
        """
        # Debug logging
        print(f"Creating identity with face_ids={face_ids}, name={name}, primary_face_id={primary_face_id}, video_ids={video_ids}")
        
        # Generate identity code
        identity_id = self.generate_identity_code()
        timestamp = datetime.now().isoformat()
        print(f"Generated identity_id: {identity_id}")
        
        # Create identity entry
        identity_entry = {
            "id": identity_id,
            "face_ids": face_ids,
            "created": timestamp,
            "last_updated": timestamp,
            "name": name,
            "primary_face_id": primary_face_id,
            "video_ids": video_ids or [],
            "employee_id": None
        }
        
        # Add to identities
        self.identities["groups"][identity_id] = identity_entry
        
        # Update face memberships
        for face_id in face_ids:
            self.identities["face_memberships"][face_id] = identity_id
            
        # Update timestamp
        self.identities["last_updated"] = timestamp
        
        # Save changes
        self._save_identities()
        
        print(f"Successfully created identity {identity_id}")
        return identity_id
        
    def get_identity(self, identity_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific identity"""
        return self.identities["groups"].get(identity_id)
        
    def get_all_identities(self) -> List[Dict[str, Any]]:
        """Get all identity groups"""
        return list(self.identities["groups"].values())
        
    def get_identity_for_face(self, face_id: str) -> Optional[Dict[str, Any]]:
        """Get the identity that a face belongs to"""
        identity_id = self.identities["face_memberships"].get(face_id)
        
        if identity_id:
            return self.get_identity(identity_id)
            
        return None
        
    def add_faces_to_identity(self, identity_id: str, face_ids: List[str], video_ids: Optional[List[str]] = None) -> bool:
        """Add faces to an existing identity"""
        identity = self.get_identity(identity_id)
        
        if not identity:
            return False
            
        # Add each face to the identity
        for face_id in face_ids:
            if face_id not in identity["face_ids"]:
                identity["face_ids"].append(face_id)
                
            # Update membership
            self.identities["face_memberships"][face_id] = identity_id
            
        # Add video IDs if provided
        if video_ids:
            for video_id in video_ids:
                if video_id not in identity["video_ids"]:
                    identity["video_ids"].append(video_id)
            
        # Update timestamp
        timestamp = datetime.now().isoformat()
        identity["last_updated"] = timestamp
        self.identities["last_updated"] = timestamp
        
        # Save changes
        self._save_identities()
        
        return True
        
    def remove_face_from_identity(self, identity_id: str, face_id: str) -> bool:
        """Remove a face from an identity"""
        identity = self.get_identity(identity_id)
        
        if not identity or face_id not in identity["face_ids"]:
            return False
            
        # Remove face from identity
        identity["face_ids"].remove(face_id)
        
        # Remove from memberships
        if face_id in self.identities["face_memberships"]:
            del self.identities["face_memberships"][face_id]
            
        # Update timestamp
        timestamp = datetime.now().isoformat()
        identity["last_updated"] = timestamp
        self.identities["last_updated"] = timestamp
        
        # Save changes
        self._save_identities()
        
        return True

    def set_primary_face(self, identity_id: str, face_id: str) -> bool:
        """Set the primary (best quality) face for an identity"""
        identity = self.get_identity(identity_id)
        
        if not identity or face_id not in identity["face_ids"]:
            return False
            
        # Set primary face
        identity["primary_face_id"] = face_id
        
        # Update timestamp
        timestamp = datetime.now().isoformat()
        identity["last_updated"] = timestamp
        self.identities["last_updated"] = timestamp
        
        # Save changes
        self._save_identities()
        
        return True
        
    def assign_employee(self, identity_id: str, employee_id: str) -> bool:
        """Assign an employee ID to an identity group"""
        identity = self.get_identity(identity_id)
        
        if not identity:
            return False
            
        # Update identity with employee ID
        identity["employee_id"] = employee_id
        
        # Update timestamp
        timestamp = datetime.now().isoformat()
        identity["last_updated"] = timestamp
        self.identities["last_updated"] = timestamp
        
        # Save changes
        self._save_identities()
        
        return True
        
    def rename_identity(self, identity_id: str, name: str) -> bool:
        """Set a human-readable name for an identity"""
        identity = self.get_identity(identity_id)
        
        if not identity:
            return False
            
        # Update identity name
        identity["name"] = name
        
        # Update timestamp
        timestamp = datetime.now().isoformat()
        identity["last_updated"] = timestamp
        self.identities["last_updated"] = timestamp
        
        # Save changes
        self._save_identities()
        
        return True

    def merge_identities(self, source_ids: List[str], target_id: str) -> bool:
        """
        Merge multiple identity groups into a target identity
        
        Args:
            source_ids: List of identity IDs to merge from
            target_id: Identity ID to merge into
            
        Returns:
            Success status
        """
        target = self.get_identity(target_id)
        if not target:
            return False
            
        # Track all faces to merge
        all_faces = []
        all_videos = []
        
        # Process each source identity
        for source_id in source_ids:
            source = self.get_identity(source_id)
            if not source or source_id == target_id:
                continue
                
            # Add faces from source to all_faces
            all_faces.extend(source["face_ids"])
            
            # Add videos from source
            if "video_ids" in source and source["video_ids"]:
                all_videos.extend(source["video_ids"])
                
            # Delete the source identity
            self.delete_identity(source_id)
            
        # Now add all collected faces to the target
        return self.add_faces_to_identity(target_id, all_faces, list(set(all_videos)))
    
    def delete_identity(self, identity_id: str) -> bool:
        """Delete an identity group"""
        identity = self.get_identity(identity_id)
        
        if not identity:
            return False
            
        # Remove face memberships
        for face_id in identity["face_ids"]:
            if face_id in self.identities["face_memberships"]:
                del self.identities["face_memberships"][face_id]
                
        # Remove the identity entry
        del self.identities["groups"][identity_id]
        
        # Update timestamp
        timestamp = datetime.now().isoformat()
        self.identities["last_updated"] = timestamp
        
        # Save changes
        self._save_identities()
        
        return True

# Create singleton instance
identity_group_manager = IdentityGroupManager()