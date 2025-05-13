import os
import sys
import json
from db.uploads import upload_manager

def register_existing_video(video_path):
    """
    Register an existing video file in the uploads database
    """
    print(f"Registering existing video: {video_path}")
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return None
    
    # Get original filename and path
    filename = os.path.basename(video_path)
    
    # Generate metadata
    metadata = {
        "user_id": None,
        "upload_type": "face_detection",
        "registered_manually": True
    }
    
    print(f"Filename: {filename}")
    print(f"File path: {video_path}")
    
    # Get file size
    file_size = os.path.getsize(video_path)
    print(f"File size: {file_size / (1024*1024):.2f} MB")
    
    # Extract video ID - use the filename without extension
    video_id = os.path.splitext(filename)[0]
    
    # Create upload record directly
    upload_record = {
        "id": video_id,
        "original_filename": filename,
        "filename": filename,  # Keep original filename
        "file_path": video_path,
        "file_url": f"/static/uploads/videos/{filename}",
        "file_size": file_size,
        "mime_type": "video/mp4",  # Assume MP4
        "uploaded_at": "2024-05-12T00:00:00",
        "processing_status": "pending",
        "metadata": metadata
    }
    
    # Add to uploads list
    upload_manager.uploads["videos"].append(upload_record)
    upload_manager.uploads["last_updated"] = "2024-05-12T00:00:00"
    upload_manager._save_uploads()
    
    print(f"Video registered with ID: {video_id}")
    
    # Display the record
    print("\nUpload record:")
    print(json.dumps(upload_record, indent=2))
    
    return video_id

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python register_existing_video.py <path_to_video>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    register_existing_video(video_path)