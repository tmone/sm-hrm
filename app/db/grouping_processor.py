import os
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple

# Import face grouping module
try:
    from db.face_groups import face_group_manager
    from db.face_landmarks import face_landmark_detector, DLIB_AVAILABLE
    GROUPING_AVAILABLE = DLIB_AVAILABLE
except ImportError:
    GROUPING_AVAILABLE = False
    print("Face grouping module not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroupingProcessor:
    """
    Handles face grouping based on similarity in the facial recognition pipeline.
    
    This includes:
    1. Grouping similar faces together based on embeddings
    2. Managing face group assignments
    3. Preparing batch labeling information
    """
    
    def __init__(self):
        """Initialize the grouping processor"""
        # Check if grouping is available
        self.grouping_available = GROUPING_AVAILABLE
        
        logger.info(f"Grouping processor initialized")
        logger.info(f"Grouping functionality available: {self.grouping_available}")
    
    def group_faces(self, data: Dict[str, Any], progress_callback: Callable) -> Dict[str, Any]:
        """
        Group faces based on embedding similarity
        
        This is the 'grouping' stage processor function
        
        Args:
            data: Job data containing faces with embeddings
            progress_callback: Callback function to report progress
            
        Returns:
            Dict with grouping results
        """
        faces = data.get('faces', [])
        video_id = data.get('video_id')
        
        if not faces:
            logger.warning("No faces provided in job data")
            return {
                'video_id': video_id,
                'group_count': 0,
                'faces': faces
            }
        
        # Check if grouping is available
        if not self.grouping_available:
            logger.warning("Face grouping not available - skipping grouping")
            progress_callback(100, "Face grouping not available - skipping")
            return {
                'video_id': video_id,
                'group_count': 0,
                'faces': faces
            }
        
        progress_callback(10, f"Grouping {len(faces)} faces by similarity")
        
        # Extract faces with embeddings
        faces_with_embeddings = [face for face in faces if face.get("has_landmarks", False)]
        
        if not faces_with_embeddings:
            logger.warning("No faces with embeddings to group")
            progress_callback(100, "No faces with embeddings to group")
            return {
                'video_id': video_id,
                'group_count': 0,
                'faces': faces
            }
        
        # Extract face IDs and embeddings
        face_data = {}
        embeddings = {}
        
        for face in faces_with_embeddings:
            face_id = face["id"]
            face_data[face_id] = face
            
            # Deserialize the embedding
            embedding_str = face.get("embedding_str")
            if embedding_str:
                embedding = face_landmark_detector.deserialize_embedding(embedding_str)
                if embedding is not None:
                    embeddings[face_id] = embedding
        
        if not embeddings:
            logger.warning("No valid embeddings found")
            progress_callback(100, "No valid embeddings found")
            return {
                'video_id': video_id,
                'group_count': 0,
                'faces': faces
            }
        
        # Group faces using the face group manager
        similarity_threshold = 0.5  # Default similarity threshold
        progress_callback(50, f"Grouping {len(embeddings)} faces with similarity threshold {similarity_threshold}")
        
        try:
            groups = face_group_manager.create_groups_from_similarity(face_data, embeddings, similarity_threshold)
            
            # Update face records with group information
            for group_id, face_ids in groups.items():
                for face_id in face_ids:
                    # Find the face in our list
                    for face in faces:
                        if face["id"] == face_id:
                            face["group_id"] = group_id
                            break
            
            # Print summary
            logger.info(f"Created {len(groups)} groups from {len(embeddings)} faces")
            for group_id, face_ids in groups.items():
                logger.info(f"Group {group_id}: {len(face_ids)} faces")
            
            progress_callback(90, f"Created {len(groups)} groups from {len(embeddings)} faces")
            
            # Prepare result
            result = {
                'video_id': video_id,
                'group_count': len(groups),
                'groups': [
                    {
                        'group_id': group_id,
                        'face_count': len(face_ids),
                        'face_ids': face_ids
                    }
                    for group_id, face_ids in groups.items()
                ],
                'faces': faces
            }
            
            return result
            
        except Exception as e:
            logger.exception(f"Error grouping faces: {str(e)}")
            progress_callback(100, f"Error grouping faces: {str(e)}")
            return {
                'video_id': video_id,
                'group_count': 0,
                'error': str(e),
                'faces': faces
            }