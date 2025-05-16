import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'db'))

from db.uploads import upload_manager

# Check if any uploads exist
print("[DEBUG] Total video uploads:", len(upload_manager.uploads.get("videos", [])))
print("[DEBUG] All upload IDs:")
for video in upload_manager.uploads.get("videos", []):
    print(f"  - ID: {video['id']}, Path: {video.get('file_path')}, Filename: {video.get('filename')}")

# Test getting a specific upload
test_id = "a18f5b12-5d48-4a5f-a6f8-2a10b067e251"  # Replace with actual ID from your test
video = upload_manager.get_video(test_id)
if video:
    print(f"\n[DEBUG] Found video with ID {test_id}:")
    print(f"  - Path: {video.get('file_path')}")
    print(f"  - Filename: {video.get('filename')}")
    print(f"  - Status: {video.get('processing_status')}")
else:
    print(f"\n[DEBUG] No video found with ID {test_id}")