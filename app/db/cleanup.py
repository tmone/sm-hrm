import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules
from db.uploads import upload_manager
from db.background_processor import background_processor

class CleanupManager:
    """
    Manages cleanup of error uploaded videos and associated data
    """
    
    def __init__(self):
        self.uploads_dir = upload_manager.uploads_dir
        self.videos_dir = upload_manager.videos_dir
        self.frames_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "frames")
        self.faces_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "faces")
        
        # Ensure directories exist
        for directory in [self.frames_dir, self.faces_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def find_error_videos(self, error_age_hours: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find all videos with error status or failed processing
        
        Args:
            error_age_hours: If specified, only include videos older than this many hours
            
        Returns:
            List of video objects with errors
        """
        # Get all videos
        all_videos = upload_manager.get_all_videos()
        error_videos = []
        
        for video in all_videos:
            # Check if video is in error state
            is_error = False
            
            # Check processing status
            if video.get("processing_status") == "failed":
                is_error = True
            
            # Check for error field in video object
            if "error" in video and video["error"]:
                is_error = True
                
            # Check upload timestamp against age threshold
            if is_error and error_age_hours is not None:
                # Get timestamp from video metadata
                uploaded_at = video.get("uploaded_at", None)
                
                if uploaded_at:
                    try:
                        # Parse ISO timestamp
                        upload_time = datetime.fromisoformat(uploaded_at)
                        age_threshold = datetime.now() - timedelta(hours=error_age_hours)
                        
                        # Only include if older than threshold
                        if upload_time > age_threshold:
                            is_error = False
                    except Exception as e:
                        logger.error(f"Error parsing timestamp for video {video.get('id')}: {str(e)}")
            
            # Add to list if in error state
            if is_error:
                error_videos.append(video)
        
        return error_videos
    
    def cleanup_error_videos(self, error_age_hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Remove videos with errors and associated data
        
        Args:
            error_age_hours: If specified, only remove videos older than this many hours
            
        Returns:
            Dict with results of cleanup operation
        """
        # Find videos with errors
        error_videos = self.find_error_videos(error_age_hours)
        
        if not error_videos:
            return {
                "status": "success",
                "message": "No error videos found to clean up",
                "removed_count": 0
            }
        
        removed_count = 0
        errors = []
        
        # Process each error video
        for video in error_videos:
            video_id = video.get("id")
            filename = video.get("filename")
            file_path = video.get("file_path")
            
            try:
                logger.info(f"Cleaning up error video: {video_id} ({filename})")
                
                # 1. Remove video file if it exists
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Removed video file: {file_path}")
                
                # 2. Remove frame directory if it exists
                # Calculate the video_id that would have been used for frames
                video_md5 = video.get("md5_hash", "")
                if not video_md5 and "metadata" in video:
                    video_md5 = video["metadata"].get("md5_hash", "")
                
                frame_dir_id = video_md5[:10] if video_md5 else video_id
                frame_dir = os.path.join(self.frames_dir, frame_dir_id)
                
                if os.path.exists(frame_dir) and os.path.isdir(frame_dir):
                    # Remove all files in the directory
                    for frame_file in os.listdir(frame_dir):
                        os.remove(os.path.join(frame_dir, frame_file))
                    # Remove the directory
                    os.rmdir(frame_dir)
                    logger.info(f"Removed frame directory: {frame_dir}")
                
                # 3. Check for any job records in the background processor
                for job_id, job in list(background_processor.jobs.items()):
                    # Look for references to this video
                    if "data" in job and isinstance(job["data"], dict):
                        if job["data"].get("video_id") == video_id:
                            # Mark job as cancelled/removed
                            background_processor.jobs[job_id]["status"] = "cancelled"
                            background_processor.jobs[job_id]["cancelled_reason"] = "Video removed during cleanup"
                            logger.info(f"Marked job {job_id} as cancelled for removed video {video_id}")
                
                # 4. Remove from uploads manager
                # Create a new list excluding the current video
                upload_manager.uploads["videos"] = [
                    v for v in upload_manager.uploads["videos"] 
                    if v.get("id") != video_id
                ]
                
                # Save the updated uploads file
                upload_manager._save_uploads()
                
                removed_count += 1
                logger.info(f"Successfully removed error video {video_id}")
                
            except Exception as e:
                error_msg = f"Error removing video {video_id}: {str(e)}"
                logger.error(error_msg)
                errors.append({
                    "video_id": video_id,
                    "error": error_msg
                })
        
        # Return results
        result = {
            "status": "success" if not errors else "partial",
            "message": f"Removed {removed_count} error videos",
            "removed_count": removed_count,
            "total_error_videos": len(error_videos)
        }
        
        if errors:
            result["errors"] = errors
            
        return result

# Create singleton instance
cleanup_manager = CleanupManager()