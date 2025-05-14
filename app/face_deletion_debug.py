#!/usr/bin/env python
"""
Debug script to identify and fix issues with face deletion in the recovered video.
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")
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

def find_face_with_issues(video_id: str, face_id: str = None) -> List[Dict[str, Any]]:
    """Find faces with potential issues in the video"""
    uploads_data = load_uploads_file()
    
    # Find the video
    video = None
    for v in uploads_data.get("videos", []):
        if v.get("id") == video_id:
            video = v
            break
    
    if not video:
        logger.error(f"Video {video_id} not found")
        return []
    
    # Check faces
    faces = video.get("faces", [])
    logger.info(f"Video {video_id} has {len(faces)} faces")
    
    # If a specific face ID is provided, only check that one
    if face_id:
        face = next((f for f in faces if f.get("id") == face_id), None)
        if face:
            return [face]
        else:
            logger.error(f"Face {face_id} not found in video {video_id}")
            return []
    
    # Otherwise, find all faces with potential issues
    problematic_faces = []
    
    for face in faces:
        face_id = face.get("id")
        if not face_id:
            logger.warning(f"Found face without ID in video {video_id}")
            problematic_faces.append(face)
            continue
        
        # Check if face has valid imageUrl
        image_url = face.get("imageUrl", "")
        if not image_url:
            logger.warning(f"Face {face_id} has no imageUrl")
            problematic_faces.append(face)
            continue
        
        # Check if the face image file exists
        if image_url.startswith("/static/faces/"):
            face_filename = os.path.basename(image_url)
            face_path = os.path.join(FACES_DIR, face_filename)
            
            if not os.path.exists(face_path):
                logger.warning(f"Face {face_id} references non-existent image: {face_path}")
                problematic_faces.append(face)
    
    return problematic_faces

def fix_face_issues(video_id: str, fix_type: str = "placeholder") -> int:
    """
    Fix issues with faces in the video
    
    Args:
        video_id: The ID of the video to fix
        fix_type: The type of fix to apply ("placeholder", "remove", "fix_urls")
        
    Returns:
        Number of faces fixed
    """
    uploads_data = load_uploads_file()
    
    # Find the video
    video = None
    for v in uploads_data.get("videos", []):
        if v.get("id") == video_id:
            video = v
            break
    
    if not video:
        logger.error(f"Video {video_id} not found")
        return 0
    
    # Get faces
    faces = video.get("faces", [])
    
    if fix_type == "remove":
        # Remove problematic faces
        problematic_faces = find_face_with_issues(video_id)
        problematic_ids = [f.get("id") for f in problematic_faces if f.get("id")]
        
        original_count = len(faces)
        video["faces"] = [f for f in faces if f.get("id") not in problematic_ids]
        
        fixed_count = original_count - len(video["faces"])
        logger.info(f"Removed {fixed_count} problematic faces from video {video_id}")
        
        # Save changes
        save_uploads_file(uploads_data)
        return fixed_count
        
    elif fix_type == "fix_urls":
        # Fix image URLs for placeholder faces
        fixed_count = 0
        
        for face in faces:
            face_id = face.get("id", "")
            if not face_id:
                continue
                
            # Update image URL
            original_url = face.get("imageUrl", "")
            if not original_url or not os.path.exists(os.path.join(STATIC_DIR, original_url.lstrip('/'))):
                # Create new URL for the face
                face_filename = f"face_{face_id}.jpg"
                face["imageUrl"] = f"/static/faces/{face_filename}"
                face["placeholder"] = True
                fixed_count += 1
                
                if fixed_count % 100 == 0:
                    logger.info(f"Fixed {fixed_count} face URLs so far")
        
        logger.info(f"Fixed URLs for {fixed_count} faces in video {video_id}")
        
        # Save changes
        save_uploads_file(uploads_data)
        return fixed_count
    
    elif fix_type == "placeholder":
        # Ensure all faces are marked as placeholders
        fixed_count = 0
        
        for face in faces:
            if not face.get("placeholder", False):
                face["placeholder"] = True
                fixed_count += 1
                
                if fixed_count % 100 == 0:
                    logger.info(f"Marked {fixed_count} faces as placeholders so far")
        
        logger.info(f"Marked {fixed_count} faces as placeholders in video {video_id}")
        
        # Save changes
        save_uploads_file(uploads_data)
        return fixed_count
    
    return 0

def test_face_deletion(video_id: str, face_id: str) -> Dict[str, Any]:
    """
    Test face deletion logic without actually deleting the face
    
    Args:
        video_id: The ID of the video
        face_id: The ID of the face to delete
        
    Returns:
        Dict with test results
    """
    uploads_data = load_uploads_file()
    
    # Find the video
    video = None
    for v in uploads_data.get("videos", []):
        if v.get("id") == video_id:
            video = v
            break
    
    if not video:
        return {"success": False, "error": f"Video {video_id} not found"}
    
    # Find the face
    face = None
    face_index = -1
    
    for i, f in enumerate(video.get("faces", [])):
        if f.get("id") == face_id:
            face = f
            face_index = i
            break
    
    if not face:
        return {"success": False, "error": f"Face {face_id} not found in video {video_id}"}
    
    # Log face details
    logger.info(f"Found face {face_id} at index {face_index}")
    logger.info(f"Face details: {face}")
    
    # Check if face image exists
    face_url = face.get("imageUrl", "")
    if face_url.startswith("/static/faces/"):
        face_filename = os.path.basename(face_url)
        face_path = os.path.join(FACES_DIR, face_filename)
        
        if os.path.exists(face_path):
            logger.info(f"Face image exists: {face_path}")
        else:
            logger.warning(f"Face image does not exist: {face_path}")
    
    # Return the test results
    return {
        "success": True,
        "video_id": video_id,
        "face_id": face_id,
        "face_index": face_index,
        "face": face,
        "image_url": face.get("imageUrl", ""),
        "is_placeholder": face.get("placeholder", False)
    }

def manual_delete_face(video_id: str, face_id: str) -> Dict[str, Any]:
    """
    Manually delete a face from a video
    
    Args:
        video_id: The ID of the video
        face_id: The ID of the face to delete
        
    Returns:
        Dict with deletion results
    """
    uploads_data = load_uploads_file()
    
    # Find the video
    video = None
    for i, v in enumerate(uploads_data.get("videos", [])):
        if v.get("id") == video_id:
            video = v
            video_index = i
            break
    
    if not video:
        return {"success": False, "error": f"Video {video_id} not found"}
    
    # Find the face
    face = None
    face_index = -1
    
    for i, f in enumerate(video.get("faces", [])):
        if f.get("id") == face_id:
            face = f
            face_index = i
            break
    
    if not face:
        return {"success": False, "error": f"Face {face_id} not found in video {video_id}"}
    
    # Delete the face from the array
    del video["faces"][face_index]
    logger.info(f"Deleted face {face_id} from video record at index {face_index}")
    
    # Try to delete the face image file
    face_url = face.get("imageUrl", "")
    if face_url.startswith("/static/faces/"):
        try:
            face_filename = os.path.basename(face_url)
            face_path = os.path.join(FACES_DIR, face_filename)
            
            if os.path.exists(face_path):
                os.remove(face_path)
                logger.info(f"Deleted face image: {face_path}")
        except Exception as e:
            logger.error(f"Error deleting face image: {str(e)}")
    
    # Save the updated uploads file
    save_uploads_file(uploads_data)
    
    return {
        "success": True,
        "message": f"Face {face_id} deleted from video {video_id}",
        "video_id": video_id,
        "face_id": face_id
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python face_deletion_debug.py <command> [args]")
        print("Commands:")
        print("  find_issues <video_id> [face_id]")
        print("  fix_issues <video_id> <fix_type>")
        print("  test_delete <video_id> <face_id>")
        print("  manual_delete <video_id> <face_id>")
        return
    
    command = sys.argv[1]
    
    if command == "find_issues":
        if len(sys.argv) < 3:
            print("Usage: python face_deletion_debug.py find_issues <video_id> [face_id]")
            return
        
        video_id = sys.argv[2]
        face_id = sys.argv[3] if len(sys.argv) > 3 else None
        
        issues = find_face_with_issues(video_id, face_id)
        print(f"Found {len(issues)} problematic faces")
        
        for face in issues[:5]:  # Show first 5 issues
            print(f"Face ID: {face.get('id')}")
            print(f"Image URL: {face.get('imageUrl')}")
            print("---")
    
    elif command == "fix_issues":
        if len(sys.argv) < 4:
            print("Usage: python face_deletion_debug.py fix_issues <video_id> <fix_type>")
            print("Fix types: placeholder, remove, fix_urls")
            return
        
        video_id = sys.argv[2]
        fix_type = sys.argv[3]
        
        fixed = fix_face_issues(video_id, fix_type)
        print(f"Fixed {fixed} faces with {fix_type} approach")
    
    elif command == "test_delete":
        if len(sys.argv) < 4:
            print("Usage: python face_deletion_debug.py test_delete <video_id> <face_id>")
            return
        
        video_id = sys.argv[2]
        face_id = sys.argv[3]
        
        result = test_face_deletion(video_id, face_id)
        print(json.dumps(result, indent=2))
    
    elif command == "manual_delete":
        if len(sys.argv) < 4:
            print("Usage: python face_deletion_debug.py manual_delete <video_id> <face_id>")
            return
        
        video_id = sys.argv[2]
        face_id = sys.argv[3]
        
        result = manual_delete_face(video_id, face_id)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()