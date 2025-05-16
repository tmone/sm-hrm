import json

# Read the uploads file directly
with open("/home/tmone/pinokio/api/StepmediaHRM/app/static/uploads/uploads.json", "r") as f:
    uploads = json.load(f)

print("[DEBUG] Total video uploads:", len(uploads.get("videos", [])))
print("\n[DEBUG] Recent uploads:")
for video in uploads.get("videos", [])[-5:]:  # Show last 5 uploads
    print(f"- ID: {video['id']}")
    print(f"  Original: {video['original_filename']}")
    print(f"  Path: {video.get('file_path')}")
    print(f"  Status: {video.get('processing_status')}")
    print(f"  Uploaded: {video.get('uploaded_at')}")
    print()