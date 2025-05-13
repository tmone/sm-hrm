import os
import cv2
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Tuple

# Import face landmarks module
try:
    from db.face_landmarks import face_landmark_detector, DLIB_AVAILABLE
    LANDMARKS_AVAILABLE = DLIB_AVAILABLE
except ImportError:
    LANDMARKS_AVAILABLE = False
    print("Face landmark module not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LandmarkProcessor:
    """
    Handles facial landmark detection and processing in the facial recognition pipeline.
    
    This includes:
    1. Facial landmark detection on detected faces
    2. Face embedding generation for similarity comparison
    3. Face visualization with landmarks
    """
    
    def __init__(self, faces_dir: str):
        """
        Initialize the landmark processor
        
        Args:
            faces_dir: Directory where faces and landmark visualizations will be saved
        """
        self.faces_dir = faces_dir
        
        # Create directory if it doesn't exist
        os.makedirs(self.faces_dir, exist_ok=True)
        
        # Check if landmark detection is available
        self.landmarks_available = LANDMARKS_AVAILABLE
        
        logger.info(f"Landmark processor initialized with faces_dir={faces_dir}")
        logger.info(f"Landmark detection available: {self.landmarks_available}")
    
    def process_landmarks(self, data: Dict[str, Any], progress_callback: Callable) -> Dict[str, Any]:
        """
        Process facial landmarks for detected faces
        
        This is the 'landmarks' stage processor function
        
        Args:
            data: Job data containing faces to process
            progress_callback: Callback function to report progress
            
        Returns:
            Dict with landmark processing results and next stage info
        """
        faces = data.get('faces', [])
        video_id = data.get('video_id')
        
        if not faces:
            logger.warning("No faces provided in job data")
            return {
                'video_id': video_id,
                'landmark_count': 0,
                'faces': faces,
                'next_stage': 'grouping',
                'next_data': {
                    'video_id': video_id,
                    'faces': faces
                }
            }
        
        # Check if landmark detection is available
        if not self.landmarks_available:
            logger.warning("Landmark detection not available - skipping landmark processing")
            progress_callback(100, "Landmark detection not available - skipping")
            return {
                'video_id': video_id,
                'landmark_count': 0,
                'faces': faces,
                'next_stage': 'grouping',
                'next_data': {
                    'video_id': video_id,
                    'faces': faces
                }
            }
        
        progress_callback(10, f"Processing landmarks for {len(faces)} faces")
        
        # Process each face
        processed_count = 0
        total_faces = len(faces)
        
        for i, face in enumerate(faces):
            face_id = face.get('id')
            if not face_id:
                logger.warning(f"Face missing ID, skipping: {face}")
                continue
            
            # Get the original face path
            original_face_path = face.get('original_face_path')
            if not original_face_path or not os.path.exists(original_face_path):
                logger.warning(f"Face path not found: {original_face_path}")
                continue
            
            # Update progress every 5 faces
            if i % 5 == 0:
                progress_percent = min(90, 10 + (i / total_faces) * 80)
                progress_callback(progress_percent, 
                                 f"Processed landmarks for {i}/{total_faces} faces")
            
            try:
                # Load the original face image
                face_img = cv2.imread(original_face_path)
                if face_img is None:
                    logger.warning(f"Could not read face image: {original_face_path}")
                    continue
                
                # Process face to get landmarks and embedding
                landmark_data = face_landmark_detector.process_face(face_img)
                
                # Update face with landmark data if successful
                if landmark_data.get("success", False):
                    # Save the visualization image with landmarks
                    vis_filename = f"{face_id}_landmarks.jpg"
                    vis_path = os.path.join(self.faces_dir, vis_filename)
                    cv2.imwrite(vis_path, landmark_data["visualization"])
                    
                    # Add to face record
                    face.update({
                        "has_landmarks": True,
                        "landmarks_str": landmark_data["landmarks_str"],
                        "embedding_str": landmark_data["embedding_str"],
                        "landmark_image": f"/static/faces/{vis_filename}"
                    })
                    
                    processed_count += 1
                    logger.info(f"Added landmarks to face {face_id}")
                else:
                    if "error" in landmark_data:
                        logger.warning(f"Failed to get landmarks for face {face_id}: {landmark_data['error']}")
            
            except Exception as e:
                logger.exception(f"Error processing landmarks for face {face_id}: {str(e)}")
        
        logger.info(f"Landmark processing completed: {processed_count}/{total_faces} faces processed")
        progress_callback(95, f"Completed landmark processing for {processed_count}/{total_faces} faces")
        
        # Prepare result
        result = {
            'video_id': video_id,
            'landmark_count': processed_count,
            'faces': faces,
            'next_stage': 'grouping',
            'next_data': {
                'video_id': video_id,
                'faces': faces
            }
        }
        
        return result