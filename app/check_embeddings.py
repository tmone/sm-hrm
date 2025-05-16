#!/usr/bin/env python3
"""
Check face embeddings in identity groups
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.models import IdentityGroup, Face
from db.database import SessionManager
import json

def check_embeddings():
    with SessionManager() as session:
        # Get all identity groups
        groups = session.query(IdentityGroup).all()
        print(f"Total identity groups: {len(groups)}")
        
        groups_with_embeddings = 0
        groups_without_embeddings = 0
        total_faces = 0
        faces_with_embeddings = 0
        faces_without_embeddings = 0
        
        for group in groups:
            group_has_embeddings = False
            faces_in_group = session.query(Face).filter_by(identity_group_id=group.id).all()
            total_faces += len(faces_in_group)
            
            for face in faces_in_group:
                if face.embedding_json:
                    try:
                        embedding = json.loads(face.embedding_json)
                        if isinstance(embedding, list) and len(embedding) == 128:
                            faces_with_embeddings += 1
                            group_has_embeddings = True
                        else:
                            faces_without_embeddings += 1
                            print(f"  Face {face.id} has invalid embedding size: {len(embedding) if isinstance(embedding, list) else 'not a list'}")
                    except Exception as e:
                        faces_without_embeddings += 1
                        print(f"  Face {face.id} has invalid embedding JSON: {e}")
                else:
                    faces_without_embeddings += 1
            
            if group_has_embeddings:
                groups_with_embeddings += 1
            else:
                groups_without_embeddings += 1
                print(f"Group {group.identity} ({group.id}) has no valid embeddings - {len(faces_in_group)} faces")
        
        print("\nSummary:")
        print(f"  Groups with embeddings: {groups_with_embeddings}")
        print(f"  Groups without embeddings: {groups_without_embeddings}")
        print(f"  Total faces: {total_faces}")
        print(f"  Faces with embeddings: {faces_with_embeddings}")
        print(f"  Faces without embeddings: {faces_without_embeddings}")

if __name__ == "__main__":
    check_embeddings()