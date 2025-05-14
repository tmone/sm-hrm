#!/usr/bin/env python
"""
This script creates placeholder face images for synthetic face entries.
It reads the uploads.json file, finds all face entries, and creates placeholder
images for any that don't have actual image files.
"""
import os
import sys
import json
import glob
import logging
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import random

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base directories
APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")
FACES_DIR = os.path.join(STATIC_DIR, "faces")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")
UPLOADS_FILE = os.path.join(UPLOADS_DIR, "uploads.json")
PLACEHOLDER_DIR = os.path.join(STATIC_DIR, "placeholders")

# Create directories if they don't exist
os.makedirs(FACES_DIR, exist_ok=True)
os.makedirs(PLACEHOLDER_DIR, exist_ok=True)

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

def generate_placeholder_face(face_id: str, output_path: str) -> bool:
    """Generate a simple placeholder face image"""
    try:
        # Create a 128x128 image
        img = Image.new('RGB', (128, 128), color=(
            random.randint(180, 220),
            random.randint(180, 220),
            random.randint(180, 220)
        ))
        draw = ImageDraw.Draw(img)
        
        # Draw a simple face outline
        # Head
        draw.ellipse((20, 20, 108, 108), fill=(
            random.randint(220, 240),
            random.randint(180, 220),
            random.randint(160, 200)
        ))
        
        # Eyes
        eye_color = (
            random.randint(10, 80),
            random.randint(10, 80),
            random.randint(120, 180)
        )
        draw.ellipse((40, 45, 55, 60), fill=eye_color)
        draw.ellipse((75, 45, 90, 60), fill=eye_color)
        
        # Mouth
        mouth_start = random.randint(45, 55)
        mouth_width = random.randint(30, 40)
        draw.arc((mouth_start, 70, mouth_start + mouth_width, 90), 0, 180, fill=(150, 50, 50), width=3)
        
        # Add face ID label
        shortened_id = face_id.split('_')[-1][:8]  # Use last part of ID, shortened
        draw.text((10, 110), shortened_id, fill=(50, 50, 50))
        
        # Save the image
        img.save(output_path)
        logger.debug(f"Created placeholder image at {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error generating placeholder face: {str(e)}")
        return False

def create_all_placeholder_faces(videos: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Create placeholder images for all synthetic faces
    
    Args:
        videos: List of video records
        
    Returns:
        Dict with counts of processed faces
    """
    stats = {
        "processed_videos": 0,
        "total_faces": 0,
        "missing_images": 0,
        "created_placeholders": 0,
        "errors": 0
    }
    
    for video in videos:
        video_id = video.get("id", "unknown")
        faces = video.get("faces", [])
        
        if not faces:
            continue
            
        logger.info(f"Processing video {video_id} with {len(faces)} faces")
        stats["processed_videos"] += 1
        stats["total_faces"] += len(faces)
        
        # Keep track of faces that need updating in the JSON
        faces_to_update = []
        
        for face in faces:
            face_id = face.get("id", "")
            if not face_id:
                continue
                
            # Check if this is a synthetic face or if the image doesn't exist
            is_synthetic = face.get("synthetic", False)
            image_url = face.get("imageUrl", "")
            
            if is_synthetic or image_url == "/static/placeholder-face.jpg":
                stats["missing_images"] += 1
                
                # Create a placeholder face image
                face_filename = f"face_{face_id}.jpg"
                face_path = os.path.join(FACES_DIR, face_filename)
                
                if generate_placeholder_face(face_id, face_path):
                    stats["created_placeholders"] += 1
                    
                    # Update the face record to point to the new image
                    face["imageUrl"] = f"/static/faces/{face_filename}"
                    face["face_path"] = face_path
                    face["placeholder"] = True
                    faces_to_update.append(face)
                else:
                    stats["errors"] += 1
        
        # Update faces in the video record if needed
        if faces_to_update:
            logger.info(f"Updating {len(faces_to_update)} face records in uploads.json")
    
    return stats

def main(video_id: Optional[str] = None):
    """
    Main function to create placeholder faces
    
    Args:
        video_id: Optional specific video ID to process
    """
    logger.info("Loading uploads data")
    uploads_data = load_uploads_file()
    
    # Filter to specified video if provided
    if video_id:
        videos = [v for v in uploads_data.get("videos", []) if v.get("id") == video_id]
        if not videos:
            logger.error(f"Video {video_id} not found")
            return
        logger.info(f"Processing single video: {video_id}")
    else:
        videos = uploads_data.get("videos", [])
        logger.info(f"Processing all {len(videos)} videos")
    
    # Create placeholder faces
    stats = create_all_placeholder_faces(videos)
    
    # Save updated uploads data
    save_uploads_file(uploads_data)
    
    # Print statistics
    logger.info("=" * 40)
    logger.info("Placeholder Generation Complete")
    logger.info(f"Processed videos: {stats['processed_videos']}")
    logger.info(f"Total faces: {stats['total_faces']}")
    logger.info(f"Missing images: {stats['missing_images']}")
    logger.info(f"Created placeholders: {stats['created_placeholders']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info("=" * 40)

if __name__ == "__main__":
    # Get video ID from command line if provided
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
        main(video_id)
    else:
        # Process all videos
        main()