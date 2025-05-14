#!/usr/bin/env python3
"""
Face Files API Endpoint

This script creates a new API endpoint that returns a list of all available face image files.
It can be used by the frontend to validate which faces actually exist.
"""

import os
import sys
import json
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict

# Define paths
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
FACES_DIR = os.path.join(STATIC_DIR, "faces")

# Create FastAPI app
app = FastAPI(title="Face Files API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/face-files")
async def get_face_files() -> Dict:
    """Return a list of all available face image files"""
    face_files = []
    
    if os.path.exists(FACES_DIR):
        for file in os.listdir(FACES_DIR):
            if file.endswith(('.jpg', '.jpeg', '.png')):
                # Extract the face ID from the filename
                face_id = os.path.splitext(file)[0]
                file_path = os.path.join(FACES_DIR, file)
                
                # Get file size and modification time
                stat = os.stat(file_path)
                
                face_files.append({
                    'id': face_id,
                    'filename': file,
                    'url': f"/static/faces/{file}",
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
    
    # Sort by modification time (newest first)
    face_files.sort(key=lambda x: x['modified'], reverse=True)
    
    return {
        'count': len(face_files),
        'faces': face_files
    }

# Add this endpoint to the main app.py by running:
# python api_faces_list.py --integrate

def integrate_with_app():
    """Add this endpoint to the main app.py file"""
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    
    if not os.path.exists(app_path):
        print(f"Error: Main app file not found at {app_path}")
        return False
    
    # Read the app.py file
    with open(app_path, 'r') as f:
        lines = f.readlines()
    
    # Check if our endpoint is already integrated
    if any('get_face_files' in line for line in lines):
        print("Endpoint already integrated in app.py")
        return True
    
    # Find where to insert our endpoint
    insert_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("@app.get") and "/api/" in line:
            insert_index = i
    
    if insert_index == -1:
        print("Could not find a suitable location to insert the endpoint")
        return False
    
    # Generate the endpoint code
    endpoint_code = """
@app.get("/api/face-files")
async def get_face_files():
    \"\"\"Return a list of all available face image files\"\"\"
    face_files = []
    
    faces_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "faces")
    
    if os.path.exists(faces_dir):
        for file in os.listdir(faces_dir):
            if file.endswith(('.jpg', '.jpeg', '.png')):
                # Extract the face ID from the filename
                face_id = os.path.splitext(file)[0]
                file_path = os.path.join(faces_dir, file)
                
                # Get file size and modification time
                stat = os.stat(file_path)
                
                face_files.append({
                    'id': face_id,
                    'filename': file,
                    'url': f"/static/faces/{file}",
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
    
    # Sort by modification time (newest first)
    face_files.sort(key=lambda x: x['modified'], reverse=True)
    
    return {
        'count': len(face_files),
        'faces': face_files
    }
"""
    
    # Insert the endpoint code
    lines.insert(insert_index, endpoint_code)
    
    # Write the updated file
    with open(app_path, 'w') as f:
        f.writelines(lines)
    
    print(f"Successfully integrated endpoint into {app_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--integrate':
        # Integrate with main app
        integrate_with_app()
    else:
        # Run standalone API for testing
        print(f"Starting Face Files API on http://localhost:8000")
        print(f"To integrate with main app.py, run: python {sys.argv[0]} --integrate")
        uvicorn.run(app, host="0.0.0.0", port=8000)