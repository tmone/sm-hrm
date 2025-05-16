#!/usr/bin/env python3
"""
Check face embeddings in JSON-based identity groups
"""
import os
import json
from db.identity_groups import identity_group_manager

def check_embeddings():
    # Get all identity groups from JSON
    groups = identity_group_manager.identities.get('groups', {})
    print(f"Total identity groups: {len(groups)}")
    
    groups_with_embeddings = 0
    groups_without_embeddings = 0
    total_faces = 0
    faces_with_embeddings = 0
    faces_without_embeddings = 0
    
    # Path to face embeddings
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    faces_dir = os.path.join(base_dir, "faces")
    face_cache_dir = os.path.join(base_dir, "face_cache")
    
    # Load face cache metadata if it exists
    metadata_file = os.path.join(face_cache_dir, "metadata.json")
    face_metadata = {}
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            face_metadata = json.load(f)
    
    for group_id, group_data in groups.items():
        group_has_embeddings = False
        face_ids = group_data.get('face_ids', [])
        total_faces += len(face_ids)
        
        for face_id in face_ids:
            # Check if face has embedding
            face_info = face_metadata.get(face_id, {})
            
            # Check for dlib embedding in face metadata
            if face_info.get('embedding'):
                embedding = face_info.get('embedding')
                if isinstance(embedding, list) and len(embedding) == 128:
                    faces_with_embeddings += 1
                    group_has_embeddings = True
                else:
                    faces_without_embeddings += 1
                    print(f"  Face {face_id} has invalid embedding size: {len(embedding) if isinstance(embedding, list) else 'not a list'}")
            else:
                faces_without_embeddings += 1
        
        if group_has_embeddings:
            groups_with_embeddings += 1
        else:
            groups_without_embeddings += 1
            print(f"Group {group_id} ({group_data.get('name', 'unnamed')}) has no valid embeddings - {len(face_ids)} faces")
    
    print("\nSummary:")
    print(f"  Groups with embeddings: {groups_with_embeddings}")
    print(f"  Groups without embeddings: {groups_without_embeddings}")
    print(f"  Total faces: {total_faces}")
    print(f"  Faces with embeddings: {faces_with_embeddings}")
    print(f"  Faces without embeddings: {faces_without_embeddings}")
    
    # Check for alternate embedding storage
    print("\nChecking for alternate embedding storage...")
    embeddings_count = 0
    for face_id in face_metadata:
        if 'embedding' in face_metadata[face_id]:
            embeddings_count += 1
    print(f"Face cache metadata contains {embeddings_count} embeddings")

if __name__ == "__main__":
    check_embeddings()