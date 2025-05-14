#!/usr/bin/env python3
"""
Face Image Database Sync Script

This script checks all face records in the database and ensures that:
1. Each face has a corresponding image file
2. The image URL in the database matches the actual file path
3. The image file is valid and properly formatted
4. Any missing images are regenerated from source frames if possible

Usage:
    python fix_face_images.py [--regenerate] [--verify-only]

Options:
    --regenerate    Attempt to regenerate missing face images from source video frames (if available)
    --verify-only   Only check and report issues without fixing them
"""

import os
import sys
import sqlite3
import json
import cv2
import numpy as np
import logging
import argparse
from pathlib import Path
import uuid
from tqdm import tqdm
from typing import Dict, List, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('face_image_sync.log')
    ]
)
logger = logging.getLogger(__name__)

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hrm.db")

# Static directories
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
FACES_DIR = os.path.join(STATIC_DIR, "faces")
FRAMES_DIR = os.path.join(STATIC_DIR, "frames")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")

def connect_db() -> sqlite3.Connection:
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        sys.exit(1)

def get_all_face_records(conn: sqlite3.Connection) -> List[Dict]:
    """Retrieve all face records from the database"""
    try:
        # Check if videos table exists first
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='videos'
        """)
        videos_table_exists = cursor.fetchone() is not None

        all_faces = []
        
        if videos_table_exists:
            # Try to get faces from videos table
            cursor.execute("""
                SELECT v.id as video_id, v.faces
                FROM videos v
                WHERE v.faces IS NOT NULL AND v.faces != '[]'
            """)
            
            videos = cursor.fetchall()
            
            for video in videos:
                video_id = video['video_id']
                try:
                    faces = json.loads(video['faces'])
                    # Add video_id to each face record for reference
                    for face in faces:
                        face['video_id'] = video_id
                    all_faces.extend(faces)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in faces field for video {video_id}")
        
        # Also check facial_data table
        cursor.execute("""
            SELECT fd.id, fd.employee_id, fd.image_path
            FROM facial_data fd
            WHERE fd.image_path IS NOT NULL
        """)
        
        facial_data = cursor.fetchall()
        
        for face in facial_data:
            face_record = {
                'id': str(face['id']),
                'employee_id': face['employee_id'],
                'imageUrl': face['image_path'],
                'source': 'facial_data'
            }
            all_faces.append(face_record)
        
        # Check any missing faces in the static/faces directory
        faces_dir = FACES_DIR
        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                if filename.endswith('.jpg') or filename.endswith('.png'):
                    face_id = os.path.splitext(filename)[0]
                    
                    # Check if this face is already in our records
                    if not any(face.get('id') == face_id for face in all_faces):
                        # Add it as an orphaned face
                        face_record = {
                            'id': face_id,
                            'imageUrl': f"/static/faces/{filename}",
                            'source': 'orphaned'
                        }
                        all_faces.append(face_record)
        
        logger.info(f"Found {len(all_faces)} face records in the database and filesystem")
        return all_faces
    
    except sqlite3.Error as e:
        logger.error(f"Error retrieving face records: {e}")
        return []

def check_face_image(face: Dict) -> Tuple[bool, str]:
    """
    Check if a face image exists and is valid
    
    Returns:
        Tuple of (is_valid, message)
    """
    # Extract file path from imageUrl
    image_url = face.get('imageUrl') or face.get('image_url')
    if not image_url:
        return False, "No imageUrl field found"
    
    # Remove leading slash and extract path after /static/
    if image_url.startswith('/static/'):
        rel_path = image_url[8:]  # Remove /static/
    else:
        rel_path = image_url
    
    # Construct full path
    full_path = os.path.join(STATIC_DIR, rel_path)
    
    # Check if file exists
    if not os.path.exists(full_path):
        return False, f"File not found: {full_path}"
    
    # Check if it's a valid image
    try:
        img = cv2.imread(full_path)
        if img is None or img.size == 0:
            return False, f"Invalid image file: {full_path}"
        
        # Basic validation: check dimensions and channels
        if len(img.shape) < 2 or img.shape[0] < 10 or img.shape[1] < 10:
            return False, f"Image too small or corrupted: {full_path}"
        
        return True, "Image is valid"
    
    except Exception as e:
        return False, f"Error reading image: {e}"

def fix_face_image_path(face: Dict, conn: sqlite3.Connection) -> Dict:
    """
    Fix the image URL in the face record to match the standard format
    
    Returns:
        Updated face record
    """
    face_id = face.get('id')
    if not face_id:
        return face
    
    # Create the correct image URL
    correct_path = f"/static/faces/{face_id}.jpg"
    
    # Check if the current imageUrl is different
    current_url = face.get('imageUrl') or face.get('image_url') or ""
    
    if current_url != correct_path:
        # Update the face record
        face['imageUrl'] = correct_path
        if 'image_url' in face:
            face['image_url'] = correct_path
        
        logger.info(f"Updated image URL for face {face_id}: {current_url} -> {correct_path}")
    
    return face

def regenerate_face_image(face: Dict, conn: sqlite3.Connection) -> bool:
    """
    Attempt to regenerate a missing face image from source frames
    
    Returns:
        True if successful, False otherwise
    """
    face_id = face.get('id')
    video_id = face.get('video_id')
    frame_number = face.get('frameNumber') or face.get('frame_number')
    
    if not face_id or not video_id:
        return False
    
    try:
        # Try to locate the source frame
        cursor = conn.cursor()
        
        # Check if we have a frame path stored
        if frame_number is not None:
            # Try to find the frame file
            potential_frame_paths = [
                # Pattern: frame_directory/video_id/frame_XXXXXX.jpg
                os.path.join(FRAMES_DIR, video_id, f"frame_{frame_number:06d}.jpg"),
                # Pattern: temp directories
                *list(Path(FRAMES_DIR).glob(f"**/frame_{frame_number:06d}.jpg"))
            ]
            
            frame_path = None
            for path in potential_frame_paths:
                if os.path.exists(path):
                    frame_path = path
                    break
            
            if frame_path:
                # Try to find the face box coordinates
                box = face.get('box')
                if not box and 'metadata' in face and isinstance(face['metadata'], dict):
                    box = face['metadata'].get('box')
                
                if box and len(box) == 4:
                    # Extract and save the face
                    frame = cv2.imread(str(frame_path))
                    if frame is not None:
                        x1, y1, x2, y2 = map(int, box)
                        
                        # Apply boundary checks
                        x1 = max(0, x1)
                        y1 = max(0, y1)
                        x2 = min(frame.shape[1], x2)
                        y2 = min(frame.shape[0], y2)
                        
                        # Check if box is valid
                        if x2 > x1 and y2 > y1:
                            # Extract face
                            face_img = frame[y1:y2, x1:x2]
                            
                            # Resize to 128x128
                            face_img = cv2.resize(face_img, (128, 128), interpolation=cv2.INTER_AREA)
                            
                            # Save the face
                            face_path = os.path.join(FACES_DIR, f"{face_id}.jpg")
                            os.makedirs(os.path.dirname(face_path), exist_ok=True)
                            
                            # Save with high quality
                            quality_params = [cv2.IMWRITE_JPEG_QUALITY, 95]
                            success = cv2.imwrite(face_path, face_img, quality_params)
                            
                            if success:
                                logger.info(f"Successfully regenerated face image for {face_id}")
                                return True
        
        logger.warning(f"Could not regenerate face image for {face_id} (no frame data found)")
        return False
    
    except Exception as e:
        logger.error(f"Error regenerating face image for {face_id}: {e}")
        return False

def update_face_records(conn: sqlite3.Connection, faces: List[Dict]) -> bool:
    """Update face records in the database"""
    try:
        cursor = conn.cursor()
        
        # Group faces by source
        faces_by_video = {}
        facial_data_faces = []
        orphaned_faces = []
        
        for face in faces:
            source = face.get('source')
            
            if source == 'facial_data':
                facial_data_faces.append(face)
            elif source == 'orphaned':
                orphaned_faces.append(face)
            else:
                video_id = face.get('video_id')
                if video_id:
                    if video_id not in faces_by_video:
                        faces_by_video[video_id] = []
                    # Remove video_id and source before adding to list for video
                    face_copy = face.copy()
                    if 'video_id' in face_copy:
                        del face_copy['video_id']
                    if 'source' in face_copy:
                        del face_copy['source']
                    faces_by_video[video_id].append(face_copy)
        
        # Update videos table if it exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='videos'
        """)
        if cursor.fetchone():
            for video_id, video_faces in faces_by_video.items():
                # Convert faces to JSON
                faces_json = json.dumps(video_faces)
                
                # Update the database
                cursor.execute(
                    "UPDATE videos SET faces = ? WHERE id = ?",
                    (faces_json, video_id)
                )
        
        # Update facial_data table
        for face in facial_data_faces:
            cursor.execute(
                "UPDATE facial_data SET image_path = ? WHERE id = ?",
                (face['imageUrl'], face['id'])
            )
        
        conn.commit()
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating face records: {e}")
        conn.rollback()
        return False

def main():
    parser = argparse.ArgumentParser(description="Face Image Database Sync Script")
    parser.add_argument('--regenerate', action='store_true', help='Attempt to regenerate missing face images')
    parser.add_argument('--verify-only', action='store_true', help='Only verify images without making changes')
    args = parser.parse_args()
    
    # Make sure face directory exists
    os.makedirs(FACES_DIR, exist_ok=True)
    
    # Connect to the database
    conn = connect_db()
    
    # Get all face records
    all_faces = get_all_face_records(conn)
    
    # Group faces by video
    faces_by_video = {}
    for face in all_faces:
        video_id = face.get('video_id')
        if video_id:
            if video_id not in faces_by_video:
                faces_by_video[video_id] = []
            faces_by_video[video_id].append(face)
    
    # Track statistics
    total_faces = len(all_faces)
    invalid_faces = 0
    fixed_paths = 0
    regenerated = 0
    
    # Process all faces
    updated_faces = []
    
    for face in tqdm(all_faces, desc="Processing faces"):
        # Check if face image is valid
        is_valid, message = check_face_image(face)
        
        if not is_valid:
            invalid_faces += 1
            logger.warning(f"Invalid face image: {face.get('id')} - {message}")
            
            if not args.verify_only:
                # Fix the path first
                face_copy = fix_face_image_path(face.copy(), conn)
                
                # Try to regenerate if requested
                if args.regenerate:
                    if regenerate_face_image(face, conn):
                        regenerated += 1
                        updated_faces.append(face_copy)
                    else:
                        updated_faces.append(face_copy)
                else:
                    updated_faces.append(face_copy)
        else:
            # Face is valid, but check if path needs fixing
            if not args.verify_only:
                original_image_url = face.get('imageUrl', '')
                fixed_face = fix_face_image_path(face.copy(), conn)
                
                if fixed_face.get('imageUrl') != original_image_url:
                    fixed_paths += 1
                    updated_faces.append(fixed_face)
                else:
                    updated_faces.append(face)
            else:
                # Just for counting valid faces
                updated_faces.append(face)
    
    # Update database if needed
    if updated_faces and not args.verify_only:
        if update_face_records(conn, updated_faces):
            logger.info(f"Updated {len(updated_faces)} face records in the database")
    
    # Print summary
    print("\nFace Image Sync Summary:")
    print(f"Total faces checked: {total_faces}")
    print(f"Invalid images found: {invalid_faces}")
    
    if not args.verify_only:
        print(f"URLs fixed: {fixed_paths}")
        if args.regenerate:
            print(f"Images regenerated: {regenerated}")
    
    # Close database connection
    conn.close()
    
    print("\nCheck face_image_sync.log for detailed information.")

if __name__ == "__main__":
    main()