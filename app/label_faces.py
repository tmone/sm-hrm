import requests
import sys
import json

def label_faces(video_id, employee_id):
    """
    Label all faces in a video with a specific employee ID
    
    Args:
        video_id: The ID of the video containing faces
        employee_id: The employee ID to label the faces with
    """
    base_url = "http://localhost:7860"
    
    print(f"Labeling faces in video {video_id} with employee ID {employee_id}")
    
    # Get video details
    try:
        video_response = requests.get(f"{base_url}/api/videos/{video_id}")
        
        if not video_response.ok:
            print(f"Error getting video details: {video_response.status_code} {video_response.text}")
            return
        
        video_data = video_response.json()
        faces = video_data.get("faces", [])
        
        if not faces:
            print("No faces found in the video")
            return
            
        print(f"Found {len(faces)} faces to label")
        
        # Label each face
        labeled_count = 0
        for face in faces:
            # Skip already labeled faces
            if face.get("labeled", False):
                print(f"Skipping already labeled face {face['id']}")
                continue
                
            # Label the face
            try:
                form_data = {
                    "employee_id": employee_id,
                    "video_id": video_id
                }
                
                label_response = requests.post(f"{base_url}/api/faces/{face['id']}/label", data=form_data)
                
                if not label_response.ok:
                    print(f"Error labeling face {face['id']}: {label_response.status_code} {label_response.text}")
                    continue
                    
                print(f"Face {face['id']} labeled as employee {employee_id}")
                labeled_count += 1
                
            except Exception as e:
                print(f"Error labeling face {face['id']}: {str(e)}")
        
        print(f"\nLabeling complete! {labeled_count} faces labeled as employee {employee_id}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python label_faces.py <video_id> <employee_id>")
        sys.exit(1)
    
    video_id = sys.argv[1]
    employee_id = sys.argv[2]
    
    label_faces(video_id, employee_id)