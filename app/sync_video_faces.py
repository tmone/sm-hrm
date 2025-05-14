#!/usr/bin/env python3
"""
Video Face Synchronization Script

This script synchronizes the face references in the database with the actual
image files available in the file system. It will:

1. Find all the actual face image files on disk
2. Check the videos table for face references 
3. Remove references to faces that don't exist on disk
4. Update face URLs to match the actual file locations

Usage:
    python sync_video_faces.py [--dry-run]

Options:
    --dry-run    Only show what would be done, without making changes
"""

import os
import sys
import sqlite3
import json
import logging
import argparse
from typing import Dict, List, Any, Set, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('face_sync.log')
    ]
)
logger = logging.getLogger(__name__)

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hrm.db")

# Static directories
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
FACES_DIR = os.path.join(STATIC_DIR, "faces")

def connect_db() -> sqlite3.Connection:
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        sys.exit(1)

def get_existing_face_files() -> Set[str]:
    """Get all face image files that exist on disk"""
    face_files = set()
    
    if os.path.exists(FACES_DIR):
        for file in os.listdir(FACES_DIR):
            if file.endswith(('.jpg', '.jpeg', '.png')):
                # Extract the face ID from the filename
                face_id = os.path.splitext(file)[0]
                face_files.add(face_id)
    
    logger.info(f"Found {len(face_files)} face image files on disk")
    return face_files

def get_videos_with_faces(conn: sqlite3.Connection) -> List[Dict]:
    """Get all videos with face references from the database"""
    cursor = conn.cursor()
    
    # Check if videos table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='videos'
    """)
    
    if not cursor.fetchone():
        logger.warning("No 'videos' table found in the database")
        return []
    
    # Get videos with faces
    cursor.execute("""
        SELECT id, faces
        FROM videos
        WHERE faces IS NOT NULL AND faces != '[]'
    """)
    
    videos = []
    for row in cursor.fetchall():
        try:
            faces = json.loads(row['faces'])
            if faces:
                videos.append({
                    'id': row['id'],
                    'faces': faces
                })
        except json.JSONDecodeError:
            logger.warning(f"Error decoding faces JSON for video {row['id']}")
    
    logger.info(f"Found {len(videos)} videos with face references")
    return videos

def sync_video_faces(conn: sqlite3.Connection, existing_face_ids: Set[str], dry_run: bool) -> Tuple[int, int]:
    """
    Synchronize video face references with existing files
    
    Returns:
        Tuple of (videos_updated, faces_removed)
    """
    videos = get_videos_with_faces(conn)
    if not videos:
        return 0, 0
    
    videos_updated = 0
    total_faces_removed = 0
    
    for video in videos:
        video_id = video['id']
        faces = video['faces']
        original_face_count = len(faces)
        
        # Filter out faces that don't exist on disk
        valid_faces = []
        for face in faces:
            face_id = face.get('id')
            if face_id and face_id in existing_face_ids:
                # Ensure the imageUrl is correct
                face['imageUrl'] = f"/static/faces/{face_id}.jpg"
                if 'image_url' in face:
                    face['image_url'] = face['imageUrl']  # Keep both fields in sync
                valid_faces.append(face)
            else:
                logger.info(f"Removing reference to non-existent face {face_id} from video {video_id}")
        
        # Check if any faces were removed
        faces_removed = original_face_count - len(valid_faces)
        if faces_removed > 0:
            total_faces_removed += faces_removed
            logger.info(f"Removed {faces_removed} non-existent faces from video {video_id}")
            
            if not dry_run:
                # Update the database
                cursor = conn.cursor()
                faces_json = json.dumps(valid_faces)
                cursor.execute(
                    "UPDATE videos SET faces = ? WHERE id = ?",
                    (faces_json, video_id)
                )
                conn.commit()
                videos_updated += 1
                logger.info(f"Updated video {video_id} with {len(valid_faces)} valid faces")
    
    return videos_updated, total_faces_removed

def main():
    parser = argparse.ArgumentParser(description="Synchronize video face references with existing files")
    parser.add_argument('--dry-run', action='store_true', help="Show what would be done without making changes")
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("Running in dry-run mode - no changes will be made")
    
    # Connect to the database
    conn = connect_db()
    
    # Get existing face files
    existing_face_ids = get_existing_face_files()
    
    # Sync video faces
    videos_updated, faces_removed = sync_video_faces(conn, existing_face_ids, args.dry_run)
    
    # Close database connection
    conn.close()
    
    # Print summary
    print("\nFace Synchronization Summary:")
    print(f"Found {len(existing_face_ids)} face image files on disk")
    print(f"Removed {faces_removed} references to non-existent faces")
    print(f"Updated {videos_updated} videos in the database")
    
    if args.dry_run:
        print("\nThis was a dry run - no changes were made to the database")
        print("Run without --dry-run to apply these changes")

if __name__ == "__main__":
    main()