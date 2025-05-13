import os
import uuid
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class UploadManager:
    """
    Manages file uploads and storage for the application
    """
    def __init__(self):
        # Set up upload directories
        self.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")

        # Create directories if they don't exist
        self.uploads_dir = os.path.join(self.base_dir, "uploads")
        self.videos_dir = os.path.join(self.uploads_dir, "videos")
        self.images_dir = os.path.join(self.uploads_dir, "images")

        # Create archive directories
        self.archive_dir = os.path.join(self.base_dir, "archive")
        self.archive_videos_dir = os.path.join(self.archive_dir, "videos")
        self.archive_images_dir = os.path.join(self.archive_dir, "images")

        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs(self.archive_videos_dir, exist_ok=True)
        os.makedirs(self.archive_images_dir, exist_ok=True)

        # File for tracking uploads
        self.uploads_file = os.path.join(self.uploads_dir, "uploads.json")
        
        # Initialize or load uploads tracking
        if os.path.exists(self.uploads_file):
            with open(self.uploads_file, 'r') as f:
                self.uploads = json.load(f)
        else:
            self.uploads = {
                "videos": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_uploads()
    
    def save_video(self, file_obj, filename: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Save a video file to the uploads directory

        Args:
            file_obj: File-like object to save
            filename: Original filename
            metadata: Additional metadata to store

        Returns:
            Dict with upload details
        """
        # Generate unique ID and sanitized filename
        upload_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1].lower()
        safe_filename = f"{upload_id}{ext}"

        # Create full path
        file_path = os.path.join(self.videos_dir, safe_filename)

        # Save the file - use a streaming approach for large files
        try:
            # Use a buffer size of 64KB for efficient copying
            with open(file_path, 'wb') as f:
                buffer_size = 64 * 1024  # 64KB buffer

                # If file_obj has a read method with a size parameter
                if hasattr(file_obj, 'read') and callable(getattr(file_obj, 'read')):
                    # Streaming read/write loop
                    while True:
                        chunk = file_obj.read(buffer_size)
                        if not chunk:
                            break
                        f.write(chunk)
                else:
                    # Fallback for objects that don't support streaming
                    shutil.copyfileobj(file_obj, f)

            print(f"Saved video file: {file_path}")
        except Exception as e:
            print(f"Error saving video file: {str(e)}")
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

        # Create upload record
        file_size = os.path.getsize(file_path)
        upload_record = {
            "id": upload_id,
            "original_filename": filename,
            "filename": safe_filename,
            "file_path": file_path,
            "file_url": f"/static/uploads/videos/{safe_filename}",
            "file_size": file_size,
            "mime_type": self._get_mime_type(ext),
            "uploaded_at": datetime.now().isoformat(),
            "processing_status": "pending",
            "metadata": metadata or {}
        }

        print(f"Saved video with ID {upload_id}, size: {file_size / (1024*1024):.2f} MB")

        # Add to uploads list
        self.uploads["videos"].append(upload_record)
        self.uploads["last_updated"] = datetime.now().isoformat()
        self._save_uploads()

        return upload_record
    
    def get_video(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """Get a video upload by ID"""
        for video in self.uploads["videos"]:
            if video["id"] == upload_id:
                return video
        return None
    
    def update_video_status(self, upload_id: str, status: str, additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """Update the processing status of a video"""
        for video in self.uploads["videos"]:
            if video["id"] == upload_id:
                video["processing_status"] = status
                video["last_updated"] = datetime.now().isoformat()
                
                if additional_data:
                    video.update(additional_data)
                
                self._save_uploads()
                return True
        return False
    
    def get_all_videos(self, status: Optional[str] = None, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        Get all video uploads, optionally filtered by status

        Args:
            status: Filter by processing status
            include_deleted: If True, include videos marked as deleted

        Returns:
            List of video records
        """
        videos = self.uploads["videos"]

        # Filter by deletion status
        if not include_deleted:
            videos = [v for v in videos if not v.get("is_deleted", False)]

        # Filter by processing status if provided
        if status:
            videos = [v for v in videos if v["processing_status"] == status]

        return videos

    def delete_video(self, upload_id: str) -> bool:
        """
        Mark a video as deleted and move it to the archive folder

        Args:
            upload_id: ID of the video to mark as deleted

        Returns:
            bool: True if video was archived, False if not found
        """
        video = self.get_video(upload_id)
        if not video:
            return False

        # Move the file to archive folder if it exists
        file_path = video.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                # Create archive filename
                filename = os.path.basename(file_path)
                archive_path = os.path.join(self.archive_videos_dir, filename)

                # Move the file
                shutil.move(file_path, archive_path)
                print(f"Archived video file: {file_path} -> {archive_path}")

                # Update the file path in the record
                video["file_path"] = archive_path
                video["file_url"] = f"/static/archive/videos/{filename}"

            except Exception as e:
                print(f"Error archiving video file: {str(e)}")

        # Mark as deleted in the database instead of removing it
        video["is_deleted"] = True
        video["deleted_at"] = datetime.now().isoformat()

        self.uploads["last_updated"] = datetime.now().isoformat()
        self._save_uploads()

        return True

    def _save_uploads(self):
        """Save the uploads tracking data to disk"""
        with open(self.uploads_file, 'w') as f:
            json.dump(self.uploads, f, indent=2)
    
    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type from file extension"""
        mime_types = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.wmv': 'video/x-ms-wmv',
            '.flv': 'video/x-flv',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
        }
        return mime_types.get(extension.lower(), 'application/octet-stream')

# Create singleton instance
upload_manager = UploadManager()