#!/usr/bin/env python
"""
Advanced recovery script for failed video processing.
This script directly accesses database files to recover face data.
"""
import os
import sys
import json
import glob
import sqlite3
import logging
import shutil
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hrm.db")

# Static directories
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
FRAMES_DIR = os.path.join(STATIC_DIR, "frames")
FACES_DIR = os.path.join(STATIC_DIR, "faces")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")
UPLOADS_FILE = os.path.join(UPLOADS_DIR, "uploads.json")

def load_uploads_file() -> Dict[str, Any]:
    """Load the uploads.json file"""
    try:
        with open(UPLOADS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading uploads file: {str(e)}")
        return {"videos": [], "last_updated": datetime.now().isoformat()}

def save_uploads_file(uploads_data: Dict[str, Any]) -> bool:
    """Save the uploads.json file"""
    try:
        # Create backup first
        backup_path = f"{UPLOADS_FILE}.bak"
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

def get_video_by_id(uploads_data: Dict[str, Any], video_id: str) -> Optional[Dict[str, Any]]:
    """Get a video by ID from the uploads data"""
    for video in uploads_data.get("videos", []):
        if video.get("id") == video_id:
            return video
    return None

def find_tracks_for_video(video_id: str) -> List[str]:
    """Find all track files for a given video ID"""
    track_pattern = os.path.join(FRAMES_DIR, f"{video_id}_track_*.json")
    return glob.glob(track_pattern)

def extract_face_info_from_track(track_file: str) -> List[Dict[str, Any]]:
    """Extract face information from a track file"""
    try:
        with open(track_file, 'r') as f:
            track_data = json.load(f)
        
        faces = []
        track_id = os.path.basename(track_file).split('_')[2].split('.')[0]
        
        for frame_idx, frame_data in enumerate(track_data.get("frames", [])):
            frame_number = frame_data.get("frame_number")
            face_data = frame_data.get("face", {})
            
            if not face_data:
                continue
                
            # Check if face image exists
            face_path = os.path.join(FACES_DIR, f"{track_data.get('video_id')}_{track_id}_{frame_number}.jpg")
            if os.path.exists(face_path):
                # Create face entry
                face_id = f"{track_data.get('video_id')}_{track_id}_{frame_number}"
                face_url = f"/static/faces/{os.path.basename(face_path)}"
                
                face_entry = {
                    "id": face_id,
                    "track_id": track_id,
                    "frame_number": frame_number,
                    "face_path": face_path,
                    "imageUrl": face_url,
                    "bbox": face_data.get("bbox", [0, 0, 0, 0]),
                    "confidence": face_data.get("confidence", 0.0),
                    "recovered": True
                }
                faces.append(face_entry)
        
        return faces
    except Exception as e:
        logger.error(f"Error processing track file {track_file}: {str(e)}")
        return []

def get_faces_from_database(video_id: str) -> List[Dict[str, Any]]:
    """Attempt to get faces from the database for this video"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query faces table if it exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='faces'")
        if cursor.fetchone():
            cursor.execute("SELECT * FROM faces WHERE video_id = ?", (video_id,))
            faces = []
            for row in cursor.fetchall():
                face = dict(row)
                # Add imageUrl if missing
                if "face_path" in face and "imageUrl" not in face:
                    face_filename = os.path.basename(face["face_path"])
                    face["imageUrl"] = f"/static/faces/{face_filename}"
                faces.append(face)
            
            conn.close()
            logger.info(f"Found {len(faces)} faces in database for video {video_id}")
            return faces
        else:
            logger.warning("No 'faces' table found in database")
            conn.close()
            return []
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return []

def force_recover_video(video_id: str) -> Dict[str, Any]:
    """
    Force recovery of a video by directly accessing track files and database
    
    Args:
        video_id: The ID of the video to recover
        
    Returns:
        Dict with recovery results
    """
    logger.info(f"Starting forced recovery for video {video_id}")
    
    # Load uploads file
    uploads_data = load_uploads_file()
    
    # Find video record
    video = get_video_by_id(uploads_data, video_id)
    if not video:
        error_msg = f"Video {video_id} not found in uploads data"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    # Initialize face collection
    all_faces = []
    
    # Method 1: Find track files and extract faces
    track_files = find_tracks_for_video(video_id)
    logger.info(f"Found {len(track_files)} track files for video {video_id}")
    
    for track_file in track_files:
        faces = extract_face_info_from_track(track_file)
        logger.info(f"Extracted {len(faces)} faces from track file {os.path.basename(track_file)}")
        all_faces.extend(faces)
    
    # Method 2: Try to get faces from database
    if not all_faces:
        db_faces = get_faces_from_database(video_id)
        all_faces.extend(db_faces)
    
    # If we found faces, update the video record
    if all_faces:
        logger.info(f"Recovered a total of {len(all_faces)} faces for video {video_id}")
        
        # Update video status
        video["processing_status"] = "recovered"
        video["faces"] = all_faces
        video["recovered"] = True
        video["recovered_at"] = datetime.now().isoformat()
        video["recovered_faces_count"] = len(all_faces)
        
        # Save updated uploads file
        save_uploads_file(uploads_data)
        
        return {
            "success": True,
            "video_id": video_id,
            "faces_count": len(all_faces),
            "message": f"Successfully recovered {len(all_faces)} faces"
        }
    else:
        error_msg = "No faces could be recovered using direct file access"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

if __name__ == "__main__":
    # Get video ID from command line or use the one from error message
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
    else:
        # Default to the video ID from the error message
        video_id = "a9b417e2-1616-4809-8072-2906d9446765"
    
    # Run recovery
    result = force_recover_video(video_id)
    
    # Print summary
    if result.get("success", False):
        faces_count = result.get("faces_count", 0)
        logger.info(f"Successfully recovered {faces_count} faces from video {video_id}")
        print(f"\nRECOVERY SUCCESSFUL: Saved {faces_count} faces from video {video_id}")
    else:
        logger.error(f"Recovery failed for video {video_id}: {result.get('error', 'Unknown error')}")
        print(f"\nRECOVERY FAILED: {result.get('error', 'Unknown error')}")