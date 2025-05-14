#!/usr/bin/env python
"""
This script fixes the imageUrl consistency issue in the uploads.json file.
It ensures all face records have a consistent format for imageUrl paths.
"""
import os
import sys
import json
import logging
import shutil
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

def fix_imageurl_format(video_id: str = None) -> Dict[str, int]:
    """
    Fix the imageUrl format in all face records
    
    Args:
        video_id: Optional specific video to fix
        
    Returns:
        Dict with counts of fixes
    """
    # Statistics
    stats = {
        "total_videos": 0,
        "total_faces": 0,
        "fixed_urls": 0,
        "missing_files": 0,
        "corrupt_entries": 0
    }
    
    # Load uploads data
    uploads_data = load_uploads_file()
    videos = uploads_data.get("videos", [])
    stats["total_videos"] = len(videos)
    
    # Filter to specific video if provided
    if video_id:
        videos = [v for v in videos if v.get("id") == video_id]
        if not videos:
            logger.error(f"Video {video_id} not found")
            return stats
    
    # Process each video
    for video in videos:
        video_id = video.get("id", "unknown")
        faces = video.get("faces", [])
        stats["total_faces"] += len(faces)
        
        logger.info(f"Processing video {video_id} with {len(faces)} faces")
        
        # Process each face
        updated_faces = []
        for face in faces:
            if not isinstance(face, dict):
                stats["corrupt_entries"] += 1
                continue
                
            face_id = face.get("id")
            if not face_id:
                logger.warning(f"Face without ID in video {video_id}")
                stats["corrupt_entries"] += 1
                continue
            
            # Check imageUrl format
            old_url = face.get("imageUrl", "")
            
            # Different possible formats to fix:
            # 1. /static/faces/face_<uuid>.jpg -> /static/faces/<uuid>.jpg
            # 2. Missing imageUrl
            
            fixed = False
            
            if old_url and 'face_' in old_url:
                # Fix the format from /static/faces/face_<id>.jpg to /static/faces/<id>.jpg
                new_url = f"/static/faces/{face_id}.jpg"
                face["imageUrl"] = new_url
                logger.info(f"Fixed URL format: {old_url} -> {new_url}")
                fixed = True
                stats["fixed_urls"] += 1
            elif not old_url:
                # Missing imageUrl
                new_url = f"/static/faces/{face_id}.jpg"
                face["imageUrl"] = new_url
                logger.info(f"Added missing URL: {new_url}")
                fixed = True
                stats["fixed_urls"] += 1
            
            # Also check if the image file exists
            if fixed:
                file_path = os.path.join(FACES_DIR, f"{face_id}.jpg")
                if not os.path.exists(file_path):
                    # Try to look for alternative face file formats
                    alt_path = os.path.join(FACES_DIR, f"face_{face_id}.jpg")
                    if os.path.exists(alt_path):
                        # Rename the file to match the expected format
                        try:
                            shutil.move(alt_path, file_path)
                            logger.info(f"Renamed face file: {alt_path} -> {file_path}")
                        except Exception as e:
                            logger.error(f"Error renaming file: {e}")
                    else:
                        logger.warning(f"Face image not found: {file_path}")
                        stats["missing_files"] += 1
            
            updated_faces.append(face)
        
        # Update the face list for this video
        video["faces"] = updated_faces
    
    # Save the updated uploads data
    if stats["fixed_urls"] > 0:
        save_uploads_file(uploads_data)
    
    return stats

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fix imageUrl formatting in uploads.json")
    parser.add_argument("--video-id", help="Fix only a specific video")
    args = parser.parse_args()
    
    # Run the fix
    logger.info("Starting imageUrl format fix")
    stats = fix_imageurl_format(args.video_id)
    
    # Print results
    logger.info("=" * 50)
    logger.info("ImageUrl Fix Complete")
    logger.info(f"Total videos processed: {stats['total_videos']}")
    logger.info(f"Total faces processed: {stats['total_faces']}")
    logger.info(f"URLs fixed: {stats['fixed_urls']}")
    logger.info(f"Missing files: {stats['missing_files']}")
    logger.info(f"Corrupt entries: {stats['corrupt_entries']}")
    logger.info("=" * 50)
    
    if stats["fixed_urls"] > 0:
        logger.info("Please restart the server to apply changes")

if __name__ == "__main__":
    main()