#!/usr/bin/env python3
"""
Debug why face images aren't being copied
"""
import os
import sys
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.identity_groups import identity_group_manager

def debug_face_copy():
    # Get faces directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    faces_dir = os.path.join(base_dir, "static", "faces")
    print(f"Base dir: {base_dir}")
    print(f"Faces dir: {faces_dir}")
    print(f"Faces dir exists: {os.path.exists(faces_dir)}")
    
    if os.path.exists(faces_dir):
        face_files = [f for f in os.listdir(faces_dir) if f.endswith('.jpg')]
        print(f"Number of face files: {len(face_files)}")
        print(f"Sample face files: {face_files[:5]}")
    
    # Check identity groups
    all_groups = identity_group_manager.identities.get('groups', {})
    print(f"\nNumber of identity groups: {len(all_groups)}")
    
    # Check first group with faces
    for group_id, group_data in list(all_groups.items())[:5]:
        print(f"\nGroup {group_id}:")
        face_ids = group_data.get('face_ids', [])
        print(f"  Number of faces: {len(face_ids)}")
        if face_ids:
            print(f"  Sample face IDs: {face_ids[:3]}")
            # Check if face files exist
            for face_id in face_ids[:3]:
                face_path = os.path.join(faces_dir, f"{face_id}.jpg")
                print(f"    {face_id}: {'EXISTS' if os.path.exists(face_path) else 'NOT FOUND'} at {face_path}")

if __name__ == "__main__":
    debug_face_copy()