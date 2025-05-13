import requests
import time
import os
import sys
import json

def test_full_workflow(video_path):
    """
    Test the full workflow:
    1. Upload a video
    2. Start processing the video
    3. Poll for task status until complete
    4. Print detected faces
    """
    base_url = "http://localhost:7860"
    
    print(f"Starting test with video: {video_path}")
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return
    
    # Step 1: Upload the video
    print("\n1. Uploading video...")
    try:
        with open(video_path, "rb") as video_file:
            files = {"video": (os.path.basename(video_path), video_file)}
            upload_response = requests.post(f"{base_url}/api/videos/upload", files=files)
            
            if not upload_response.ok:
                print(f"Error uploading video: {upload_response.status_code} {upload_response.text}")
                return
            
            upload_data = upload_response.json()
            video_id = upload_data["upload_id"]
            print(f"Upload successful. Video ID: {video_id}")
    except Exception as e:
        print(f"Upload failed: {str(e)}")
        return
    
    # Step 2: Start processing the video
    print("\n2. Starting video processing...")
    try:
        process_response = requests.post(f"{base_url}/api/videos/{video_id}/process")
        
        if not process_response.ok:
            print(f"Error starting processing: {process_response.status_code} {process_response.text}")
            return
        
        process_data = process_response.json()
        task_id = process_data["task_id"]
        print(f"Processing started. Task ID: {task_id}")
    except Exception as e:
        print(f"Processing request failed: {str(e)}")
        return
    
    # Step 3: Poll for task status
    print("\n3. Polling for task status...")
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
            
            if status == "completed":
                print(f"Processing complete! Detected {status_data.get('face_count', 0)} faces.")
                completed = True
            elif status == "failed":
                print(f"Processing failed: {status_data.get('error', 'Unknown error')}")
                return
            else:
                # Wait 2 seconds before polling again
                time.sleep(2)
    except Exception as e:
        print(f"Status polling failed: {str(e)}")
        return
    
    # Step 4: Get the video details with faces
    print("\n4. Getting video details with faces...")
    try:
        video_response = requests.get(f"{base_url}/api/videos/{video_id}")
        
        if not video_response.ok:
            print(f"Error getting video details: {video_response.status_code} {video_response.text}")
            return
        
        video_data = video_response.json()
        faces = video_data.get("faces", [])
        print(f"Found {len(faces)} faces:")
        
        for i, face in enumerate(faces):
            print(f"  Face {i+1}:")
            print(f"    ID: {face['id']}")
            print(f"    Image: {face['imageUrl']}")
            print(f"    Timestamp: {face.get('timestamp', 'unknown')}")
            print(f"    Confidence: {face.get('confidence', 0)}")
            print(f"    Labeled: {face.get('labeled', False)}")
        
        print("\nTest completed successfully!")
        return video_id, faces
    except Exception as e:
        print(f"Getting video details failed: {str(e)}")
        return
        
if __name__ == "__main__":
    # Use the test video created earlier or provide a path
    if len(sys.argv) < 2:
        video_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "sample_video.mp4")
        if not os.path.exists(video_path):
            print(f"Test video not found at {video_path}. Please provide a video path.")
            print("Usage: python test_video_workflow.py <path_to_video>")
            sys.exit(1)
    else:
        video_path = sys.argv[1]
    
    test_full_workflow(video_path)