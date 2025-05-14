#!/usr/bin/env python
"""
This script forcibly creates placeholder face images for all faces in a video,
regardless of whether they are marked as synthetic or not.
"""
import os
import sys
import json
import logging
import shutil
from typing import Dict, Any, Optional
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

# Create faces directory if it doesn't exist
os.makedirs(FACES_DIR, exist_ok=True)

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

def generate_placeholder_face(face_id: str, index: int, output_path: str) -> bool:
    """Generate a simple placeholder face image"""
    try:
        # Create a 128x128 image with varying colors based on index
        color_value = (index % 40) + 180  # Vary between 180-220
        img = Image.new('RGB', (128, 128), color=(
            color_value, 
            color_value,
            color_value
        ))
        draw = ImageDraw.Draw(img)
        
        # Determine face features based on index for variety
        face_type = index % 5  # 5 different face types
        
        # Head (vary the color slightly)
        skin_r = 220 + (index % 20)
        skin_g = 180 + (index % 30)
        skin_b = 160 + (index % 40)
        draw.ellipse((20, 20, 108, 108), fill=(skin_r, skin_g, skin_b))
        
        # Eyes (vary position and color)
        eye_color = (
            10 + (index % 70),
            10 + (index % 70),
            120 + (index % 60)
        )
        
        # Different eye positions based on face type
        if face_type == 0:
            # Regular eyes
            draw.ellipse((40, 45, 55, 60), fill=eye_color)
            draw.ellipse((75, 45, 90, 60), fill=eye_color)
        elif face_type == 1:
            # Wide eyes
            draw.ellipse((35, 45, 50, 60), fill=eye_color)
            draw.ellipse((80, 45, 95, 60), fill=eye_color)
        elif face_type == 2:
            # Close eyes
            draw.ellipse((45, 45, 60, 60), fill=eye_color)
            draw.ellipse((70, 45, 85, 60), fill=eye_color)
        elif face_type == 3:
            # Small eyes
            draw.ellipse((42, 48, 52, 58), fill=eye_color)
            draw.ellipse((77, 48, 87, 58), fill=eye_color)
        else:
            # Large eyes
            draw.ellipse((38, 42, 58, 62), fill=eye_color)
            draw.ellipse((72, 42, 92, 62), fill=eye_color)
        
        # Mouth (vary type and color)
        mouth_type = index % 3
        mouth_color = (150 + (index % 50), 50 + (index % 50), 50 + (index % 30))
        
        if mouth_type == 0:
            # Smiling
            draw.arc((45, 70, 85, 95), 0, 180, fill=mouth_color, width=3)
        elif mouth_type == 1:
            # Neutral
            draw.line((45, 80, 85, 80), fill=mouth_color, width=3)
        else:
            # Random curve
            draw.arc((45, 70, 85, 90), 20, 160, fill=mouth_color, width=3)
        
        # Add face ID label
        shortened_id = face_id.split('_')[-1][:6]  # Use last part of ID, shortened
        draw.text((10, 110), shortened_id, fill=(50, 50, 50))
        
        # Save the image
        img.save(output_path)
        logger.debug(f"Created placeholder image at {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error generating placeholder face: {str(e)}")
        return False

def force_create_faces_for_video(video_id: str) -> Dict[str, int]:
    """
    Force create placeholder images for all faces in a video
    
    Args:
        video_id: The video ID to process
        
    Returns:
        Dict with statistics
    """
    stats = {
        "total_faces": 0,
        "created_placeholders": 0,
        "errors": 0
    }
    
    # Load uploads data
    uploads_data = load_uploads_file()
    
    # Find the video
    video = None
    for v in uploads_data.get("videos", []):
        if v.get("id") == video_id:
            video = v
            break
    
    if not video:
        logger.error(f"Video {video_id} not found in uploads data")
        return stats
    
    # Get all faces
    faces = video.get("faces", [])
    stats["total_faces"] = len(faces)
    logger.info(f"Found {len(faces)} faces in video {video_id}")
    
    # Create placeholder images for all faces
    updated_faces = []
    
    for i, face in enumerate(faces):
        face_id = face.get("id", f"face_{i}")
        
        # Create a filename for the face
        face_filename = f"face_{face_id}.jpg"
        face_path = os.path.join(FACES_DIR, face_filename)
        
        # Generate placeholder image
        if generate_placeholder_face(face_id, i, face_path):
            stats["created_placeholders"] += 1
            
            # Update face record
            face["imageUrl"] = f"/static/faces/{face_filename}"
            face["face_path"] = face_path
            face["placeholder"] = True
        else:
            stats["errors"] += 1
        
        updated_faces.append(face)
        
        # Log progress periodically
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{len(faces)} faces")
    
    # Update video record
    video["faces"] = updated_faces
    
    # Save updated uploads data
    save_uploads_file(uploads_data)
    
    return stats

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Please provide a video ID")
        sys.exit(1)
    
    video_id = sys.argv[1]
    logger.info(f"Force creating placeholder faces for video {video_id}")
    
    stats = force_create_faces_for_video(video_id)
    
    logger.info("=" * 40)
    logger.info("Force Placeholder Generation Complete")
    logger.info(f"Total faces: {stats['total_faces']}")
    logger.info(f"Created placeholders: {stats['created_placeholders']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info("=" * 40)