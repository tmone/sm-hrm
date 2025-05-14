#!/usr/bin/env python
"""
This script completely removes all faces from a specific video.
It's useful for cleaning up placeholder/fake faces so the video can be reprocessed.
"""
import os
import sys
import json
import glob
import shutil
import logging
from typing import Dict, Any, List
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")
FACES_DIR = os.path.join(STATIC_DIR, "faces")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")
UPLOADS_FILE = os.path.join(UPLOADS_DIR, "uploads.json")

def load_uploads_file() -> Dict[str, Any]:
    """Load the uploads.json file"""
    try:
        with open(UPLOADS_FILE, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded uploads data with {len(data.get('videos', []))} videos")
        return data
    except Exception as e:
        logger.error(f"Error loading uploads file: {str(e)}")
        return {"videos": [], "last_updated": datetime.now().isoformat()}

def save_uploads_file(uploads_data: Dict[str, Any]) -> bool:
    """Save the uploads.json file"""
    try:
        # Create backup first
        backup_path = f"{UPLOADS_FILE}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
        if os.path.exists(UPLOADS_FILE):
            shutil.copy2(UPLOADS_FILE, backup_path)
            logger.info(f"Created backup at {backup_path}")
        
        # Save the file
        with open(UPLOADS_FILE, 'w') as f:
            json.dump(uploads_data, f, indent=2)
        logger.info(f"Saved uploads file with {len(uploads_data.get('videos', []))} videos")
        return True
    except Exception as e:
        logger.error(f"Error saving uploads file: {str(e)}")
        return False

def remove_all_faces_from_video(video_id: str) -> Dict[str, Any]:
    """
    Remove all faces from a specific video
    
    Args:
        video_id: The ID of the video to clean
        
    Returns:
        Dict with operation results
    """
    logger.info(f"Removing all faces from video {video_id}")
    
    # Load the uploads data
    uploads_data = load_uploads_file()
    
    # Find the video
    video = None
    for v in uploads_data.get("videos", []):
        if v.get("id") == video_id:
            video = v
            break
    
    if not video:
        error_msg = f"Video {video_id} not found in uploads data"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    # Get all faces from the video
    faces = video.get("faces", [])
    face_count = len(faces)
    logger.info(f"Found {face_count} faces in video {video_id}")
    
    # Remove all face image files
    deleted_files = 0
    for face in faces:
        face_id = face.get("id", "")
        if not face_id:
            continue
            
        # Try to delete face image file
        face_url = face.get("imageUrl", "")
        if face_url and face_url.startswith("/static/faces/"):
            filename = os.path.basename(face_url)
            face_path = os.path.join(FACES_DIR, filename)
            
            if os.path.exists(face_path):
                try:
                    os.remove(face_path)
                    deleted_files += 1
                    if deleted_files % 100 == 0:
                        logger.info(f"Deleted {deleted_files}/{face_count} face image files")
                except Exception as e:
                    logger.error(f"Error deleting face image file {face_path}: {str(e)}")
    
    logger.info(f"Deleted {deleted_files} face image files")
    
    # Clear the faces array in the video record
    video["faces"] = []
    
    # Update video status to allow reprocessing
    video["processing_status"] = "uploaded"
    
    # Remove other processing-related fields if they exist
    for field in ["faces_count", "recovered", "recovered_at", "recovered_faces_count"]:
        if field in video:
            del video[field]
    
    # Save the updated uploads data
    save_result = save_uploads_file(uploads_data)
    
    if save_result:
        logger.info(f"Successfully removed all faces from video {video_id}")
        return {
            "success": True,
            "video_id": video_id,
            "faces_removed": face_count,
            "files_deleted": deleted_files
        }
    else:
        error_msg = "Failed to save uploads data after removing faces"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

def main():
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Remove all faces from a video")
    parser.add_argument("video_id", help="ID of the video to clean")
    parser.add_argument("--force", action="store_true", help="Don't prompt for confirmation")
    args = parser.parse_args()
    
    video_id = args.video_id
    
    # Confirm before proceeding
    if not args.force:
        confirm = input(f"This will remove ALL faces from video {video_id}. Continue? (y/N): ")
        if confirm.lower() != 'y':
            logger.info("Operation cancelled by user")
            return
    
    # Remove all faces
    result = remove_all_faces_from_video(video_id)
    
    # Print result
    if result["success"]:
        print("=" * 50)
        print(f"Successfully removed all faces from video {video_id}")
        print(f"- Faces removed: {result['faces_removed']}")
        print(f"- Files deleted: {result['files_deleted']}")
        print("\nThe video's status has been reset to 'uploaded'.")
        print("You can now reprocess the video if needed.")
        print("=" * 50)
    else:
        print("=" * 50)
        print(f"Failed to remove faces: {result['error']}")
        print("=" * 50)

if __name__ == "__main__":
    main()