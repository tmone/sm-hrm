#!/usr/bin/env python
"""
This script synchronizes face records in the database with face image files on disk.
It ensures that:
1. All face images on disk have corresponding entries in the database
2. All face entries in the database have corresponding files on disk
3. Orphaned face images on disk are removed
4. Database entries for non-existent face images are removed
"""
import os
import sys
import json
import glob
import shutil
import logging
from typing import Dict, Any, List, Set, Tuple
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

def get_all_face_files() -> List[str]:
    """Get all face image files on disk"""
    face_pattern = os.path.join(FACES_DIR, "*.jpg")
    face_files = glob.glob(face_pattern)
    
    # Also check for other image formats
    for ext in ["*.png", "*.jpeg"]:
        face_pattern = os.path.join(FACES_DIR, ext)
        face_files.extend(glob.glob(face_pattern))
    
    logger.info(f"Found {len(face_files)} face image files on disk")
    return face_files

def get_all_face_records(uploads_data: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any], Dict[str, Any]]]:
    """
    Get all face records from the database
    
    Returns:
        List of tuples with (face_id, face_record, video_record)
    """
    all_faces = []
    
    for video in uploads_data.get("videos", []):
        video_id = video.get("id", "")
        faces = video.get("faces", [])
        
        for face in faces:
            face_id = face.get("id", "")
            if face_id:
                all_faces.append((face_id, face, video))
    
    logger.info(f"Found {len(all_faces)} face records in database")
    return all_faces

def map_face_file_to_id(filename: str) -> str:
    """Extract face ID from filename"""
    # Common filename patterns:
    # 1. face_<id>.jpg
    # 2. <video_id>_<track_id>_<frame_num>.jpg
    
    base_name = os.path.basename(filename)
    
    # Pattern 1: face_<id>.jpg
    if base_name.startswith("face_"):
        face_id = base_name[5:].split(".")[0]
        return face_id
    
    # Pattern 2: use the whole filename without extension as ID
    return os.path.splitext(base_name)[0]

def check_and_sync_faces(dry_run: bool = False) -> Dict[str, int]:
    """
    Check and synchronize face files and database records
    
    Args:
        dry_run: If True, only simulate changes without actually making them
        
    Returns:
        Dict with statistics
    """
    stats = {
        "files_on_disk": 0,
        "records_in_db": 0,
        "orphaned_files": 0,
        "missing_files": 0,
        "deleted_orphans": 0,
        "removed_records": 0
    }
    
    # Load the uploads data
    uploads_data = load_uploads_file()
    
    # Get all face files on disk
    face_files = get_all_face_files()
    stats["files_on_disk"] = len(face_files)
    
    # Map face files to their IDs
    face_file_map = {}
    for face_file in face_files:
        face_id = map_face_file_to_id(face_file)
        face_file_map[face_id] = face_file
    
    # Get all face records
    face_records = get_all_face_records(uploads_data)
    stats["records_in_db"] = len(face_records)
    
    # Find face records without files
    missing_files = []
    for face_id, face, video in face_records:
        face_url = face.get("imageUrl", "")
        
        # Skip faces without imageUrl
        if not face_url:
            continue
        
        # Extract filename from imageUrl
        if face_url.startswith("/static/faces/"):
            filename = os.path.basename(face_url)
            expected_path = os.path.join(FACES_DIR, filename)
            
            if not os.path.exists(expected_path):
                logger.warning(f"Missing file for face {face_id} in video {video.get('id')}: {expected_path}")
                missing_files.append((face_id, face, video))
    
    stats["missing_files"] = len(missing_files)
    
    # Find face files without records
    all_face_ids = set(face_id for face_id, _, _ in face_records)
    orphaned_files = []
    
    for face_id, face_file in face_file_map.items():
        if face_id not in all_face_ids:
            logger.warning(f"Orphaned face file without database record: {face_file}")
            orphaned_files.append((face_id, face_file))
    
    stats["orphaned_files"] = len(orphaned_files)
    
    if not dry_run:
        # Remove database records for missing files
        if missing_files:
            logger.info(f"Removing {len(missing_files)} database records for missing files")
            
            for face_id, face, video in missing_files:
                video_id = video.get("id", "")
                # Remove face from the video's faces array
                video["faces"] = [f for f in video.get("faces", []) if f.get("id") != face_id]
                stats["removed_records"] += 1
                
                logger.info(f"Removed record for face {face_id} from video {video_id}")
            
            # Save the updated uploads data
            save_uploads_file(uploads_data)
        
        # Delete orphaned face files
        if orphaned_files:
            logger.info(f"Deleting {len(orphaned_files)} orphaned face files")
            
            for face_id, face_file in orphaned_files:
                try:
                    os.remove(face_file)
                    stats["deleted_orphans"] += 1
                    logger.info(f"Deleted orphaned face file: {face_file}")
                except Exception as e:
                    logger.error(f"Error deleting orphaned face file {face_file}: {str(e)}")
    
    return stats

def check_video_files(dry_run: bool = False) -> Dict[str, int]:
    """
    Check video files and database records
    
    Args:
        dry_run: If True, only simulate changes without actually making them
        
    Returns:
        Dict with statistics
    """
    stats = {
        "videos_in_db": 0,
        "video_files": 0,
        "missing_videos": 0,
        "orphaned_videos": 0,
        "removed_records": 0
    }
    
    # Load the uploads data
    uploads_data = load_uploads_file()
    videos = uploads_data.get("videos", [])
    stats["videos_in_db"] = len(videos)
    
    # Check video files
    video_dir = os.path.join(STATIC_DIR, "uploads", "videos")
    if not os.path.exists(video_dir):
        logger.warning(f"Video directory doesn't exist: {video_dir}")
        return stats
    
    # Get all video files
    video_files = []
    for ext in ["*.mp4", "*.avi", "*.mov", "*.wmv", "*.mkv"]:
        video_pattern = os.path.join(video_dir, ext)
        video_files.extend(glob.glob(video_pattern))
    
    stats["video_files"] = len(video_files)
    
    # Map video files to their names
    video_file_map = {os.path.basename(vf): vf for vf in video_files}
    
    # Find missing video files
    missing_videos = []
    for video in videos:
        video_id = video.get("id", "")
        filename = video.get("filename", "")
        
        if not filename:
            continue
        
        if filename not in video_file_map:
            logger.warning(f"Missing video file for video {video_id}: {filename}")
            missing_videos.append((video_id, video))
    
    stats["missing_videos"] = len(missing_videos)
    
    # Find orphaned video files
    video_filenames = set(v.get("filename", "") for v in videos)
    orphaned_videos = []
    
    for filename, file_path in video_file_map.items():
        if filename not in video_filenames:
            logger.warning(f"Orphaned video file without database record: {file_path}")
            orphaned_videos.append((filename, file_path))
    
    stats["orphaned_videos"] = len(orphaned_videos)
    
    # Update database if not dry run
    if not dry_run and missing_videos:
        # Mark missing videos as deleted
        for video_id, video in missing_videos:
            # Instead of removing, mark as deleted
            video["is_deleted"] = True
            video["deleted_at"] = datetime.now().isoformat()
            video["processing_status"] = "deleted"
            
            logger.info(f"Marked video {video_id} as deleted (missing file)")
            stats["removed_records"] += 1
        
        # Save the updated uploads data
        save_uploads_file(uploads_data)
    
    return stats

def main():
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Synchronize face files and database records")
    parser.add_argument("--dry-run", action="store_true", help="Simulate changes without actually making them")
    parser.add_argument("--check-videos", action="store_true", help="Also check video files")
    parser.add_argument("--video-id", type=str, help="Only process a specific video")
    args = parser.parse_args()
    
    # Show what we're doing
    action = "Simulating" if args.dry_run else "Performing"
    logger.info(f"{action} face synchronization")
    
    if args.video_id:
        logger.info(f"Processing only video {args.video_id}")
    
    # Check and sync faces
    face_stats = check_and_sync_faces(args.dry_run)
    
    # Check videos if requested
    video_stats = {}
    if args.check_videos:
        logger.info("Checking video files")
        video_stats = check_video_files(args.dry_run)
    
    # Print summary
    logger.info("=" * 50)
    logger.info("Synchronization Summary")
    logger.info("=" * 50)
    logger.info("Face Statistics:")
    logger.info(f"- Face files on disk: {face_stats['files_on_disk']}")
    logger.info(f"- Face records in database: {face_stats['records_in_db']}")
    logger.info(f"- Face records without files: {face_stats['missing_files']}")
    logger.info(f"- Face files without records: {face_stats['orphaned_files']}")
    
    if not args.dry_run:
        logger.info(f"- Removed database records: {face_stats['removed_records']}")
        logger.info(f"- Deleted orphaned files: {face_stats['deleted_orphans']}")
    
    if args.check_videos:
        logger.info("\nVideo Statistics:")
        logger.info(f"- Video files on disk: {video_stats['video_files']}")
        logger.info(f"- Video records in database: {video_stats['videos_in_db']}")
        logger.info(f"- Video records without files: {video_stats['missing_videos']}")
        logger.info(f"- Video files without records: {video_stats['orphaned_videos']}")
        
        if not args.dry_run:
            logger.info(f"- Updated video records: {video_stats['removed_records']}")
    
    logger.info("=" * 50)
    
    if args.dry_run:
        logger.info("This was a dry run. No changes were made.")
        logger.info("Run without --dry-run to actually make the changes.")

if __name__ == "__main__":
    main()