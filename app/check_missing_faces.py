#!/usr/bin/env python3
"""
Script to identify missing face images
This script specifically checks for files that are referenced in the database but don't exist on disk
"""

import os
import sqlite3
import json
from pathlib import Path
import sys

# Define paths
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hrm.db")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
FACES_DIR = os.path.join(STATIC_DIR, "faces")

def connect_db():
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        sys.exit(1)

def get_image_references():
    """Get all image references from the database"""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Check facial_data table
    print("Checking facial_data table...")
    cursor.execute("SELECT id, image_path FROM facial_data WHERE image_path IS NOT NULL")
    facial_data_refs = []
    
    for row in cursor.fetchall():
        image_path = row['image_path']
        if image_path and image_path.strip():
            # Remove leading /static/ if present
            if image_path.startswith('/static/'):
                rel_path = image_path[8:]
            else:
                rel_path = image_path
                
            facial_data_refs.append({
                'id': row['id'],
                'db_path': image_path,
                'file_path': os.path.join(STATIC_DIR, rel_path)
            })
    
    print(f"Found {len(facial_data_refs)} image references in facial_data table")
    
    # Check videos table if it exists
    video_refs = []
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='videos'
        """)
        if cursor.fetchone():
            print("Checking videos table...")
            cursor.execute("SELECT id, faces FROM videos WHERE faces IS NOT NULL AND faces != '[]'")
            
            for row in cursor.fetchall():
                try:
                    faces = json.loads(row['faces'])
                    for face in faces:
                        image_url = face.get('imageUrl') or face.get('image_url')
                        if image_url:
                            # Remove leading /static/ if present
                            if image_url.startswith('/static/'):
                                rel_path = image_url[8:]
                            else:
                                rel_path = image_url
                                
                            video_refs.append({
                                'id': face.get('id'),
                                'video_id': row['id'],
                                'db_path': image_url,
                                'file_path': os.path.join(STATIC_DIR, rel_path)
                            })
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error parsing faces JSON for video {row['id']}: {e}")
            
            print(f"Found {len(video_refs)} image references in videos table")
    except sqlite3.Error as e:
        print(f"Error checking videos table: {e}")
    
    conn.close()
    return facial_data_refs, video_refs

def check_files_exist(refs):
    """Check if referenced files exist"""
    missing = []
    existing = []
    
    for ref in refs:
        if not os.path.exists(ref['file_path']):
            missing.append(ref)
        else:
            existing.append(ref)
    
    return existing, missing

def main():
    print(f"Checking for missing face images...")
    print(f"Database: {DB_PATH}")
    print(f"Faces directory: {FACES_DIR}")
    
    # Get image references from database
    facial_data_refs, video_refs = get_image_references()
    
    # Check if files exist
    facial_existing, facial_missing = check_files_exist(facial_data_refs)
    video_existing, video_missing = check_files_exist(video_refs)
    
    # Print summary
    print("\n--- Summary ---")
    print(f"Facial data references: {len(facial_data_refs)}")
    print(f"  - Existing files: {len(facial_existing)}")
    print(f"  - Missing files: {len(facial_missing)}")
    
    print(f"Video face references: {len(video_refs)}")
    print(f"  - Existing files: {len(video_existing)}")
    print(f"  - Missing files: {len(video_missing)}")
    
    # Print some sample missing files
    if facial_missing:
        print("\nSample missing facial_data references:")
        for ref in facial_missing[:5]:
            print(f"  - ID: {ref['id']}, Path: {ref['db_path']}")
    
    if video_missing:
        print("\nSample missing video face references:")
        for ref in video_missing[:5]:
            print(f"  - Face ID: {ref['id']}, Video ID: {ref['video_id']}, Path: {ref['db_path']}")
    
    # Check for files on disk that aren't in the database
    if os.path.exists(FACES_DIR):
        print("\nChecking for files not in database...")
        db_paths = set([os.path.normpath(ref['file_path']) for ref in facial_data_refs + video_refs])
        
        # Find all face files
        face_files = []
        for ext in ['jpg', 'jpeg', 'png']:
            face_files.extend(list(Path(FACES_DIR).glob(f'*.{ext}')))
        
        orphaned_files = []
        for file_path in face_files:
            if os.path.normpath(str(file_path)) not in db_paths:
                orphaned_files.append(str(file_path))
        
        print(f"Found {len(face_files)} files in faces directory")
        print(f"Orphaned files (on disk but not in DB): {len(orphaned_files)}")
        
        if orphaned_files:
            print("\nSample orphaned files:")
            for path in orphaned_files[:5]:
                print(f"  - {path}")

if __name__ == "__main__":
    main()