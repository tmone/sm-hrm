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
        
        print(f"Uploads file path: {self.uploads_file}")
        
        # Initialize or load uploads tracking
        if os.path.exists(self.uploads_file):
            try:
                with open(self.uploads_file, 'r') as f:
                    self.uploads = json.load(f)
                print(f"Loaded {len(self.uploads.get('videos', []))} videos from uploads file")
            except Exception as e:
                print(f"Error loading uploads file: {str(e)}")
                # Create default structure if loading fails
                self.uploads = {
                    "videos": [],
                    "last_updated": datetime.now().isoformat()
                }
                print("Created empty uploads dictionary after error")
        else:
            print("No uploads file found, creating new one")
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
        try:
            # Make sure uploads is initialized
            if not hasattr(self, 'uploads') or not self.uploads:
                print("Warning: uploads not initialized, trying to reload")
                # Try to load uploads file
                if os.path.exists(self.uploads_file):
                    try:
                        with open(self.uploads_file, 'r') as f:
                            self.uploads = json.load(f)
                        print(f"Reloaded {len(self.uploads.get('videos', []))} videos from uploads file")
                    except json.JSONDecodeError as je:
                        print(f"JSON decode error in uploads file: {str(je)}")
                        # Try to recover corrupted JSON
                        recovered = self._recover_corrupted_json()
                        if recovered:
                            print(f"Successfully recovered {len(self.uploads.get('videos', []))} videos from corrupted file")
                        else:
                            # Create default structure if recovery fails
                            self.uploads = {
                                "videos": [],
                                "last_updated": datetime.now().isoformat()
                            }
                            print("Created empty uploads dictionary after failed recovery")
                    except Exception as e:
                        print(f"Error reloading uploads file: {str(e)}")
                        # Create default structure if loading fails
                        self.uploads = {
                            "videos": [],
                            "last_updated": datetime.now().isoformat()
                        }
                        print("Created empty uploads dictionary after error")
                else:
                    print("No uploads file found, creating new one")
                    self.uploads = {
                        "videos": [],
                        "last_updated": datetime.now().isoformat()
                    }
                    self._save_uploads()
                
            # Make sure videos key exists
            if "videos" not in self.uploads:
                print("Warning: 'videos' key not found in uploads, initializing it")
                self.uploads["videos"] = []
            
            # Ensure videos is a list (defensive programming)
            if not isinstance(self.uploads["videos"], list):
                print(f"Error: 'videos' is not a list type: {type(self.uploads['videos'])}")
                self.uploads["videos"] = []
                self._save_uploads()  # Save the corrected structure
            
            videos = self.uploads["videos"]
            print(f"Found {len(videos)} videos before filtering")

            # Validate and sanitize each video entry
            sanitized_videos = []
            modified = False
            
            for idx, video in enumerate(videos):
                if not isinstance(video, dict):
                    print(f"Warning: Video at index {idx} is not a dictionary, skipping")
                    modified = True
                    continue
                
                # Ensure required keys exist with default values
                if "id" not in video:
                    video["id"] = str(uuid.uuid4())
                    modified = True
                    
                if "processing_status" not in video:
                    video["processing_status"] = "unknown"
                    modified = True
                    
                if "is_deleted" not in video:
                    video["is_deleted"] = False
                    modified = True
                    
                if "faces" not in video:
                    video["faces"] = []
                    modified = True
                elif not isinstance(video["faces"], list):
                    video["faces"] = []
                    modified = True
                
                # Sanitize faces array to ensure all faces have required properties
                if "faces" in video and isinstance(video["faces"], list):
                    sanitized_faces = []
                    face_modified = False
                    
                    for face in video["faces"]:
                        if isinstance(face, dict):
                            # Ensure required face properties
                            if "id" not in face:
                                face["id"] = str(uuid.uuid4())
                                face_modified = True
                                
                            # Add imageUrl if missing but face_path exists
                            if "face_path" in face and not face.get("imageUrl"):
                                face_filename = os.path.basename(face["face_path"])
                                face["imageUrl"] = f"/static/faces/{face_filename}"
                                face_modified = True
                                
                            sanitized_faces.append(face)
                    
                    if face_modified or len(sanitized_faces) != len(video["faces"]):
                        video["faces"] = sanitized_faces
                        modified = True
                
                sanitized_videos.append(video)
            
            # Save sanitized videos back to uploads if we made any changes
            if modified or len(sanitized_videos) != len(videos):
                self.uploads["videos"] = sanitized_videos
                print(f"Saved sanitized video list with {len(sanitized_videos)} videos")
                self._save_uploads()
                videos = sanitized_videos

            # Filter by deletion status
            if not include_deleted:
                filtered_videos = [v for v in videos if not v.get("is_deleted", False)]
                print(f"After deletion filtering: {len(filtered_videos)} videos")
            else:
                filtered_videos = videos
                
            # Filter by processing status if provided
            if status:
                final_videos = [v for v in filtered_videos if v.get("processing_status") == status]
                print(f"After status filtering: {len(final_videos)} videos")
            else:
                final_videos = filtered_videos

            return final_videos
            
        except Exception as e:
            print(f"Error in get_all_videos: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Return empty list on error
            return []

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
    
    def _recover_corrupted_json(self) -> bool:
        """
        Attempt to recover a corrupted uploads.json file
        
        Returns:
            bool: True if recovery was successful, False otherwise
        """
        try:
            print(f"Attempting to recover corrupted uploads file: {self.uploads_file}")
            
            # Try to create a backup first
            backup_path = f"{self.uploads_file}.bak"
            try:
                shutil.copy2(self.uploads_file, backup_path)
                print(f"Created backup at {backup_path}")
            except Exception as e:
                print(f"Failed to create backup: {str(e)}")
            
            # Read the file as text and try to fix common JSON issues
            with open(self.uploads_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse the content with a more forgiving approach
            import re
            
            # Check if it's completely corrupted beyond repair
            if not content.strip().startswith('{'):
                print("File is too corrupted to recover using simple methods")
                return False
                
            # Initialize with empty structure if recovery fails
            self.uploads = {
                "videos": [],
                "last_updated": datetime.now().isoformat()
            }
            
            # Try to extract the videos array if it exists
            videos_match = re.search(r'"videos"\s*:\s*\[(.*?)\]', content, re.DOTALL)
            if videos_match:
                try:
                    # Try to parse each object in the array individually
                    videos_content = videos_match.group(1)
                    video_objects = []
                    
                    # Very basic parsing to extract individual JSON objects
                    depth = 0
                    start = 0
                    for i, char in enumerate(videos_content):
                        if char == '{': 
                            if depth == 0:
                                start = i
                            depth += 1
                        elif char == '}':
                            depth -= 1
                            if depth == 0:
                                try:
                                    obj_str = videos_content[start:i+1]
                                    video_obj = json.loads(obj_str)
                                    video_objects.append(video_obj)
                                except:
                                    print(f"Failed to parse video object: {obj_str[:100]}...")
                    
                    if video_objects:
                        print(f"Recovered {len(video_objects)} video objects")
                        self.uploads["videos"] = video_objects
                        self._save_uploads()  # Save the recovered data
                        return True
                except Exception as e:
                    print(f"Error during videos extraction: {str(e)}")
            
            return False
        except Exception as e:
            print(f"Error in _recover_corrupted_json: {str(e)}")
            return False

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