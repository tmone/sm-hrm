import requests
import time
import os
import sys
import re

def extract_video_id(video_path):
    """Extract video ID from the filename"""
    # Extract just the filename from the path
    filename = os.path.basename(video_path)
    # Remove the extension
    filename_without_ext = os.path.splitext(filename)[0]
    # Return the filename as ID
    return filename_without_ext

def process_existing_video(video_path):
    """
    Process an existing video file without re-uploading it
    1. Start processing the video
    2. Poll for task status until complete
    3. Print detected faces
    """
    base_url = "http://localhost:7860"
    
    print(f"Starting process for existing video: {video_path}")
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return
    
    # Get video ID from filename
    video_filename = os.path.basename(video_path)
    # Remove extension
    video_id_base = os.path.splitext(video_filename)[0]
    
    print(f"Using video ID: {video_id_base}")
    
    # Step 1: Start processing the video
    print("\n1. Starting video processing...")
    try:
        process_response = requests.post(f"{base_url}/api/videos/{video_id_base}/process")
        
        if not process_response.ok:
            print(f"Error starting processing: {process_response.status_code} {process_response.text}")
            return
        
        process_data = process_response.json()
        task_id = process_data["task_id"]
        print(f"Processing started. Task ID: {task_id}")
    except Exception as e:
        print(f"Processing request failed: {str(e)}")
        return
    
    # Step 2: Poll for task status
    print("\n2. Polling for task status...")
    try:
        completed = False
        while not completed:
            status_response = requests.get(f"{base_url}/api/tasks/{task_id}")
            
            if not status_response.ok:
                print(f"Error getting task status: {status_response.status_code} {status_response.text}")
                return
            
            status_data = status_response.json()
            status = status_data["status"]
            
            print(f"Task status: {status}")
            progress = status_data.get("progress", 0)
            if progress:
                print(f"Progress: {progress}%")
            
            if status == "completed":
                print(f"Processing complete! Detected {status_data.get('face_count', 0)} faces.")
                completed = True
            elif status == "failed":
                print(f"Processing failed: {status_data.get('error', 'Unknown error')}")
                return
            else:
                # Wait 5 seconds before polling again
                print("Waiting 5 seconds...")
                time.sleep(5)
    except Exception as e:
        print(f"Status polling failed: {str(e)}")
        return
    
    # Step 3: Get the video details with faces
    print("\n3. Getting video details with faces...")
    try:
        video_response = requests.get(f"{base_url}/api/videos/{video_id_base}")
        
        if not video_response.ok:
            print(f"Error getting video details: {video_response.status_code} {video_response.text}")
            return
        
        video_data = video_response.json()
        faces = video_data.get("faces", [])
        print(f"Found {len(faces)} faces:")
        
        for i, face in enumerate(faces[:10]):  # Show first 10 faces
            print(f"  Face {i+1}:")
            print(f"    ID: {face['id']}")
            print(f"    Image: {face['imageUrl']}")
            print(f"    Timestamp: {face.get('timestamp', 'unknown')}")
            print(f"    Confidence: {face.get('confidence', 0)}")
            print(f"    Labeled: {face.get('labeled', False)}")
        
        if len(faces) > 10:
            print(f"  ... and {len(faces) - 10} more faces")
        
        print("\nTest completed successfully!")
        return video_id_base, faces
    except Exception as e:
        print(f"Getting video details failed: {str(e)}")
        return
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_existing_video.py <path_to_video>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    process_existing_video(video_path)