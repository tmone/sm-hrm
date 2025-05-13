import requests
import time
import os
import sys

def test_video_upload(video_path):
    # Ensure the file exists
    if not os.path.exists(video_path):
        print(f"Error: The video file {video_path} does not exist.")
        return
    
    print(f"Testing face detection with video: {video_path}")
    
    try:
        # Create a session first
        session_response = requests.post(
            "http://localhost:7860/api/face-sessions",
            timeout=10
        )
        
        if not session_response.ok:
            print(f"Failed to create session: {session_response.status_code} {session_response.text}")
            return
        
        session_data = session_response.json()
        session_id = session_data.get("session_id")
        
        if not session_id:
            print("No session ID returned from server")
            return
            
        print(f"Created session: {session_id}")
        
        # Now upload the video to process
        with open(video_path, "rb") as video_file:
            files = {"video": (os.path.basename(video_path), video_file)}
            data = {"sample_rate": "10", "session_id": session_id}
            
            print("Uploading video for processing...")
            start_time = time.time()
            
            response = requests.post(
                "http://localhost:7860/api/process-video",
                files=files,
                data=data,
                timeout=30
            )
            
            elapsed = time.time() - start_time
            print(f"Request completed in {elapsed:.2f} seconds")
            
            if not response.ok:
                print(f"Error: {response.status_code} {response.text}")
                return
                
            # Process the response
            result = response.json()
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            
            if result.get('error'):
                print(f"Error: {result.get('error')}")
            
            faces = result.get('faces', [])
            print(f"Detected {len(faces)} faces")
            
            # Print first few faces details
            for i, face in enumerate(faces[:3]):
                print(f"Face {i+1}: ID={face.get('id')}, Timestamp={face.get('timestamp')}")
                
            return True
            
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_face_detection.py <path_to_video_file>")
        sys.exit(1)
        
    video_path = sys.argv[1]
    test_video_upload(video_path)