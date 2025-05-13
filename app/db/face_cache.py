import os
import json
import uuid
import shutil
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

class FaceCache:
    """
    A simple cache system for storing detected faces during processing.
    This allows for recovering from errors and continuing labeling work.
    """
    def __init__(self):
        # Set up cache directory
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "face_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache metadata file
        self.metadata_file = os.path.join(self.cache_dir, "metadata.json")
        
        # Initialize or load metadata
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "sessions": {},
                "last_cleanup": time.time()
            }
            self._save_metadata()
        
        # Auto cleanup old cache entries (older than 7 days)
        self._cleanup_old_sessions(max_age_days=7)
    
    def create_session(self) -> str:
        """Create a new face processing session"""
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create session directory
        session_dir = os.path.join(self.cache_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Add to metadata
        self.metadata["sessions"][session_id] = {
            "created": timestamp,
            "last_updated": timestamp,
            "status": "in_progress",
            "faces": []
        }
        self._save_metadata()
        
        return session_id
    
    def add_face(self, session_id: str, face_img_path: str, metadata: Dict[str, Any]) -> str:
        """
        Add a detected face to the session cache
        
        Args:
            session_id: The session ID to add to
            face_img_path: Path to the face image (will be copied to cache)
            metadata: Additional metadata for the face
            
        Returns:
            ID of the cached face
        """
        if session_id not in self.metadata["sessions"]:
            raise ValueError(f"Session not found: {session_id}")
        
        # Generate face ID
        face_id = str(uuid.uuid4())
        
        # Create the destination path
        face_filename = f"{face_id}{os.path.splitext(face_img_path)[1]}"
        face_cache_path = os.path.join(self.cache_dir, session_id, face_filename)
        
        # Copy the face image to the cache
        try:
            shutil.copy2(face_img_path, face_cache_path)
        except Exception as e:
            print(f"Failed to copy face image to cache: {e}")
            # If copy fails, use the original path
            face_cache_path = face_img_path
        
        # Add to session metadata
        face_entry = {
            "id": face_id,
            "path": face_cache_path,
            "imageUrl": f"/static/face_cache/{session_id}/{face_filename}",
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
            "assigned": False,
            "assignedTo": None
        }
        
        self.metadata["sessions"][session_id]["faces"].append(face_entry)
        self.metadata["sessions"][session_id]["last_updated"] = datetime.now().isoformat()
        self._save_metadata()
        
        return face_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get all faces and metadata for a session"""
        if session_id not in self.metadata["sessions"]:
            return None
        
        return self.metadata["sessions"][session_id]
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions with summary information"""
        sessions = []
        for session_id, session_data in self.metadata["sessions"].items():
            if session_data["status"] != "deleted":
                face_count = len(session_data["faces"])
                assigned_count = sum(1 for face in session_data["faces"] if face.get("assigned", False))
                
                sessions.append({
                    "id": session_id,
                    "created": session_data["created"],
                    "last_updated": session_data["last_updated"],
                    "status": session_data["status"],
                    "face_count": face_count,
                    "assigned_count": assigned_count
                })
        
        # Sort by last updated (newest first)
        return sorted(sessions, key=lambda x: x["last_updated"], reverse=True)
    
    def assign_face(self, session_id: str, face_id: str, employee_id: str, employee_name: str) -> bool:
        """Mark a face as assigned to an employee"""
        if session_id not in self.metadata["sessions"]:
            return False
        
        # Find the face in the session
        for face in self.metadata["sessions"][session_id]["faces"]:
            if face["id"] == face_id:
                face["assigned"] = True
                face["assignedTo"] = {
                    "employeeId": employee_id,
                    "employeeName": employee_name,
                    "assignedAt": datetime.now().isoformat()
                }
                self.metadata["sessions"][session_id]["last_updated"] = datetime.now().isoformat()
                self._save_metadata()
                return True
        
        return False
    
    def complete_session(self, session_id: str) -> bool:
        """Mark a session as completed"""
        if session_id not in self.metadata["sessions"]:
            return False
        
        self.metadata["sessions"][session_id]["status"] = "completed"
        self.metadata["sessions"][session_id]["last_updated"] = datetime.now().isoformat()
        self._save_metadata()
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its files"""
        if session_id not in self.metadata["sessions"]:
            return False
        
        try:
            # Mark as deleted in metadata
            self.metadata["sessions"][session_id]["status"] = "deleted"
            self.metadata["sessions"][session_id]["last_updated"] = datetime.now().isoformat()
            self._save_metadata()
            
            # Try to remove the directory, but don't fail if it can't be deleted
            session_dir = os.path.join(self.cache_dir, session_id)
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir, ignore_errors=True)
            
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def _save_metadata(self):
        """Save the metadata to disk"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _cleanup_old_sessions(self, max_age_days=7):
        """Clean up old sessions that haven't been accessed in 'max_age_days'"""
        # Only run cleanup once a day
        now = time.time()
        if now - self.metadata.get("last_cleanup", 0) < 86400:  # 24 hours
            return
        
        self.metadata["last_cleanup"] = now
        
        # Calculate cutoff date
        cutoff_time = now - (max_age_days * 86400)
        
        for session_id, session_data in list(self.metadata["sessions"].items()):
            # Skip already deleted sessions
            if session_data["status"] == "deleted":
                continue
            
            # Check last updated timestamp
            try:
                last_updated = datetime.fromisoformat(session_data["last_updated"]).timestamp()
                if last_updated < cutoff_time:
                    print(f"Cleaning up old session: {session_id}")
                    self.delete_session(session_id)
            except Exception as e:
                print(f"Error during cleanup for session {session_id}: {e}")
                continue
        
        self._save_metadata()

# Create singleton instance
face_cache = FaceCache()