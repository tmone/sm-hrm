import os
import shutil
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from db.uploads import upload_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoCleanupManager:
    """
    Manages cleanup of failed video uploads and their associated processing data
    """

    def __init__(self):
        self.base_dir = upload_manager.base_dir
        self.frame_dir = os.path.join(self.base_dir, "frames")

        # Create directories if they don't exist
        os.makedirs(self.frame_dir, exist_ok=True)

    def cleanup_error_videos(self, min_age_hours: int = 24) -> Dict[str, Any]:
        """
        Find and remove videos with "failed" processing status
        
        Args:
            min_age_hours: Minimum age in hours since failure before cleanup (default: 24)
            
        Returns:
            Dict with cleanup results and statistics
        """
        logger.info(f"Starting cleanup of error videos older than {min_age_hours} hours")
        
        # Get all videos with failed status
        failed_videos = upload_manager.get_all_videos(status="failed")
        logger.info(f"Found {len(failed_videos)} videos with failed status")
        
        # Track cleanup statistics
        cleanup_stats = {
            "total_found": len(failed_videos),
            "removed": 0,
            "skipped_age": 0,
            "errors": 0,
            "freed_space_bytes": 0,
            "cleaned_videos": []
        }
        
        # Current time for age comparison
        now = datetime.now()
        
        # Process each failed video
        for video in failed_videos:
            try:
                # Check if video has been in failed state long enough
                if "processing_failed" in video:
                    failed_time = datetime.fromisoformat(video["processing_failed"])
                    age = now - failed_time
                    
                    if age < timedelta(hours=min_age_hours):
                        logger.info(f"Skipping video {video['id']} as it's only {age.total_seconds() / 3600:.2f} hours old")
                        cleanup_stats["skipped_age"] += 1
                        continue
                
                # Log the video we're about to clean up
                logger.info(f"Cleaning up failed video: {video['id']} - {video['original_filename']}")
                
                # Track the space to be freed
                video_size = 0
                if os.path.exists(video["file_path"]):
                    video_size = os.path.getsize(video["file_path"])
                    cleanup_stats["freed_space_bytes"] += video_size
                
                # Remove the actual video file
                if os.path.exists(video["file_path"]):
                    os.remove(video["file_path"])
                    logger.info(f"Removed video file: {video['file_path']}")
                
                # Remove any associated extracted frames
                # Most likely stored in frame dir with video_id prefix or hash-based dirname
                self._cleanup_extracted_frames(video)
                
                # Add to cleaned videos list
                cleanup_stats["cleaned_videos"].append({
                    "id": video["id"],
                    "filename": video["original_filename"],
                    "size_bytes": video_size,
                    "error": video.get("error", "Unknown error")
                })
                
                # Remove from uploads tracking
                self._remove_from_uploads_tracking(video["id"])
                
                cleanup_stats["removed"] += 1
                logger.info(f"Successfully cleaned up video {video['id']}")
                
            except Exception as e:
                logger.error(f"Error cleaning up video {video['id']}: {str(e)}")
                cleanup_stats["errors"] += 1
        
        # Save the updated uploads.json without the removed videos
        upload_manager._save_uploads()
        
        logger.info(f"Cleanup completed: {cleanup_stats['removed']} videos removed, "
                   f"{cleanup_stats['skipped_age']} skipped due to age, "
                   f"{cleanup_stats['errors']} errors")
        
        return cleanup_stats
    
    def _cleanup_extracted_frames(self, video: Dict[str, Any]) -> None:
        """
        Remove extracted frames associated with a video
        
        This checks multiple possible locations where frames might be stored
        based on the various processing methods and stages
        """
        video_id = video["id"]
        
        # Check for frames directory based on video ID
        video_frame_dir = os.path.join(self.frame_dir, video_id)
        if os.path.exists(video_frame_dir) and os.path.isdir(video_frame_dir):
            shutil.rmtree(video_frame_dir)
            logger.info(f"Removed video frame directory: {video_frame_dir}")
        
        # Check for frames based on MD5 hash if available (used by video_processor.py)
        if "md5_hash" in video and video["md5_hash"]:
            hash_prefix = video["md5_hash"][:10]
            hash_frame_dir = os.path.join(self.frame_dir, hash_prefix)
            if os.path.exists(hash_frame_dir) and os.path.isdir(hash_frame_dir):
                shutil.rmtree(hash_frame_dir)
                logger.info(f"Removed hash-based frame directory: {hash_frame_dir}")
        
        # Check if the video has a 'task_id' and clean up associated processing results
        if "task_id" in video:
            task_id = video["task_id"]
            task_result_dir = os.path.join(self.base_dir, "processing", task_id)
            if os.path.exists(task_result_dir) and os.path.isdir(task_result_dir):
                shutil.rmtree(task_result_dir)
                logger.info(f"Removed task result directory: {task_result_dir}")
        
        # Check if there's a parallel job ID and clean up related data
        if "parallel_job_id" in video:
            job_id = video["parallel_job_id"]
            job_dir = os.path.join(self.base_dir, "jobs", job_id)
            if os.path.exists(job_dir) and os.path.isdir(job_dir):
                shutil.rmtree(job_dir)
                logger.info(f"Removed parallel job directory: {job_dir}")
    
    def _remove_from_uploads_tracking(self, video_id: str) -> None:
        """
        Remove a video from the uploads tracking data
        """
        # Filter out the video with the given ID
        upload_manager.uploads["videos"] = [v for v in upload_manager.uploads["videos"] if v["id"] != video_id]
        upload_manager.uploads["last_updated"] = datetime.now().isoformat()

# Create singleton instance
video_cleanup_manager = VideoCleanupManager()