#!/usr/bin/env python
"""
This script fixes the delete_face API endpoint to properly handle placeholder faces.
It modifies the app.py file to add better error handling and specific handling for
placeholder faces created during recovery.
"""
import os
import sys
import re
import shutil
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PY = os.path.join(APP_DIR, "app.py")
BACKUP_DIR = os.path.join(APP_DIR, "backups")

# Create backup directory if it doesn't exist
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_app_py():
    """Create a backup of app.py"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"app.py.{timestamp}.bak")
    
    shutil.copy2(APP_PY, backup_file)
    logger.info(f"Created backup of app.py at {backup_file}")
    
    return backup_file

def update_delete_face_endpoint():
    """Update the delete_face endpoint in app.py"""
    # Read the app.py file
    with open(APP_PY, 'r') as f:
        content = f.read()
    
    # Find the delete_face function definition
    delete_face_pattern = r'@app\.delete\("/api/videos/{video_id}/faces/{face_id}"\)\nasync def delete_face\([^)]*\):[^}]*?return [^}]*?}(?=\n)'
    
    # Use re.DOTALL to match across multiple lines
    match = re.search(delete_face_pattern, content, re.DOTALL)
    
    if not match:
        logger.error("Could not find delete_face function in app.py")
        return False
    
    old_function = match.group(0)
    logger.info(f"Found delete_face function ({len(old_function)} chars)")
    
    # Create the new function
    new_function = '''@app.delete("/api/videos/{video_id}/faces/{face_id}")
async def delete_face(
    video_id: str,
    face_id: str,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """
    Delete a face from a video
    
    This endpoint:
    1. Removes the face from the video record
    2. Removes the face from any face groups
    3. Removes the face from any identity groups
    4. Optionally deletes the face image file
    
    Special handling for placeholder faces created during recovery.
    """
    logger.info(f"Deleting face {face_id} from video {video_id}")
    
    # Get the video
    video = upload_manager.get_video(video_id)
    if not video:
        logger.error(f"Video not found: {video_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Video not found: {video_id}"
        )
    
    # Check if the video has a faces array
    if "faces" not in video or not video["faces"]:
        logger.error(f"Video {video_id} has no faces")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No faces found in video {video_id}"
        )
    
    # Find the face in the video
    face = None
    face_index = -1
    for i, f in enumerate(video["faces"]):
        if f.get("id") == face_id:
            face = f
            face_index = i
            break
    
    if face is None:
        logger.error(f"Face {face_id} not found in video {video_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Face {face_id} not found in video {video_id}"
        )
    
    # Check if this is a placeholder/recovered face
    is_placeholder = face.get("placeholder", False) or face.get("synthetic", False)
    logger.info(f"Face {face_id} is {'a placeholder/synthetic face' if is_placeholder else 'a regular face'}")
    
    # For placeholder/synthetic faces, skip group removal
    if not is_placeholder:
        # 1. Remove the face from any face groups
        try:
            # Get the group ID for this face
            group_id = face_group_manager.groups["face_memberships"].get(face_id)
            if group_id:
                logger.info(f"Removing face {face_id} from face group {group_id}")
                face_group_manager.remove_face_from_group(group_id, face_id)
        except Exception as e:
            logger.error(f"Error removing face from face group: {str(e)}")
            # Continue with deletion even if this fails
        
        # 2. Remove the face from any identity groups
        try:
            # Get the identity ID for this face
            identity_id = identity_group_manager.identities["face_memberships"].get(face_id)
            if identity_id:
                logger.info(f"Removing face {face_id} from identity group {identity_id}")
                identity_group_manager.remove_face_from_identity(identity_id, face_id)
        except Exception as e:
            logger.error(f"Error removing face from identity group: {str(e)}")
            # Continue with deletion even if this fails
    
    # 3. Remove the face from the video record
    logger.info(f"Removing face {face_id} from video record at index {face_index}")
    video["faces"].pop(face_index)
    upload_manager.update_video_status(video_id, video["processing_status"], {"faces": video["faces"]})
    
    # 4. Optionally delete the face image file
    if "imageUrl" in face and face["imageUrl"] and face["imageUrl"].startswith("/static/faces/"):
        try:
            face_filename = os.path.basename(face["imageUrl"])
            face_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "faces", face_filename)
            
            if os.path.exists(face_path):
                logger.info(f"Deleting face image file: {face_path}")
                os.remove(face_path)
        except Exception as e:
            logger.error(f"Error deleting face image file: {str(e)}")
            # Don't fail the request if file deletion fails
    
    logger.info(f"Successfully deleted face {face_id} from video {video_id}")
    return {"status": "success", "message": f"Face {face_id} deleted from video {video_id}"}'''
    
    # Replace the old function with the new one
    new_content = content.replace(old_function, new_function)
    
    # Save the modified file
    with open(APP_PY, 'w') as f:
        f.write(new_content)
    
    logger.info("Updated delete_face function in app.py")
    
    return True

def main():
    # Create a backup first
    backup_file = backup_app_py()
    
    # Update the delete_face endpoint
    if update_delete_face_endpoint():
        logger.info("Successfully updated delete_face endpoint")
        logger.info("Please restart the server to apply changes")
    else:
        logger.error("Failed to update delete_face endpoint")
        logger.info(f"Original app.py backed up at {backup_file}")

if __name__ == "__main__":
    main()