import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import json
import urllib.request
import tempfile
import base64

# Try to import dlib - if not available, use a stub implementation
DLIB_AVAILABLE = False
try:
    import dlib
    DLIB_AVAILABLE = True
    print("dlib successfully imported - face landmark detection available")
except ImportError:
    print("dlib not available - face landmark detection disabled")
    print("Run the install_dependencies.sh script to install dlib")

class FaceLandmarkDetector:
    """
    Detects facial landmarks and provides methods for comparing faces based on landmarks.
    
    This class provides:
    1. Facial landmark detection (68 points)
    2. Face similarity calculation
    3. Face embedding generation
    4. Face grouping
    """
    
    def __init__(self):
        """Initialize the face landmark detector and recognition models"""
        # Set up model paths and directories
        self.models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
        os.makedirs(self.models_dir, exist_ok=True)

        # Initialize with defaults (non-functional placeholders)
        self.detector = None
        self.landmark_predictor = None
        self.face_recognizer = None

        # If dlib is not available, we can't do landmark detection
        if not DLIB_AVAILABLE:
            print("Landmark detection disabled - dlib not available")
            return

        # Paths for landmark and face recognition models
        self.landmark_model_path = os.path.join(self.models_dir, "shape_predictor_68_face_landmarks.dat")
        self.recognition_model_path = os.path.join(self.models_dir, "dlib_face_recognition_resnet_model_v1.dat")

        # Download models if not present
        self._download_models()

        # Initialize the face detector, landmark predictor, and recognition model
        try:
            self.detector = dlib.get_frontal_face_detector()

            # Only load the landmark model if it exists
            if os.path.exists(self.landmark_model_path):
                self.landmark_predictor = dlib.shape_predictor(self.landmark_model_path)
            else:
                print("Landmark model not found, landmark detection disabled")

            # Only load the recognition model if it exists
            if os.path.exists(self.recognition_model_path):
                self.face_recognizer = dlib.face_recognition_model_v1(self.recognition_model_path)
            else:
                print("Recognition model not found, face recognition disabled")

            if self.detector and self.landmark_predictor and self.face_recognizer:
                print("Face landmark detector initialized successfully")
            else:
                print("Face landmark detector partially initialized")
        except Exception as e:
            print(f"Error initializing face landmark detector: {e}")
            self.detector = None
            self.landmark_predictor = None
            self.face_recognizer = None
            
    def _download_models(self):
        """Download the required models if they don't exist"""
        # Landmark model
        if not os.path.exists(self.landmark_model_path):
            print(f"Downloading facial landmark model to {self.landmark_model_path}...")
            try:
                url = "https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2"
                
                # Download to a temporary file
                tmp_file, _ = urllib.request.urlretrieve(url)
                
                # Decompress (it's a bz2 file)
                import bz2
                with bz2.BZ2File(tmp_file, 'rb') as bz_file:
                    with open(self.landmark_model_path, 'wb') as out_file:
                        out_file.write(bz_file.read())
                        
                print("Landmark model downloaded successfully")
            except Exception as e:
                print(f"Error downloading landmark model: {e}")
                
        # Face recognition model
        if not os.path.exists(self.recognition_model_path):
            print(f"Downloading face recognition model to {self.recognition_model_path}...")
            try:
                url = "https://github.com/davisking/dlib-models/raw/master/dlib_face_recognition_resnet_model_v1.dat.bz2"
                
                # Download to a temporary file
                tmp_file, _ = urllib.request.urlretrieve(url)
                
                # Decompress (it's a bz2 file)
                import bz2
                with bz2.BZ2File(tmp_file, 'rb') as bz_file:
                    with open(self.recognition_model_path, 'wb') as out_file:
                        out_file.write(bz_file.read())
                        
                print("Recognition model downloaded successfully")
            except Exception as e:
                print(f"Error downloading recognition model: {e}")
    
    def detect_landmarks(self, face_img: np.ndarray) -> Optional[List[Tuple[int, int]]]:
        """
        Detect facial landmarks in a face image
        
        Args:
            face_img: BGR face image as numpy array
            
        Returns:
            List of (x, y) landmark coordinates or None if no face/landmarks detected
        """
        if self.landmark_predictor is None:
            print("Landmark predictor not available")
            return None
            
        try:
            # Convert to grayscale for detection
            if len(face_img.shape) == 3:  # Color image
                gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            else:  # Already grayscale
                gray = face_img
                
            # Detect faces
            dlib_faces = self.detector(gray)
            
            if not dlib_faces:
                return None
                
            # Use the first (largest) face
            face_rect = dlib_faces[0]
            
            # Get facial landmarks
            landmarks = self.landmark_predictor(gray, face_rect)
            
            # Convert landmarks to (x, y) tuples
            landmark_points = []
            for i in range(68):  # 68 landmarks
                x = landmarks.part(i).x
                y = landmarks.part(i).y
                landmark_points.append((x, y))
                
            return landmark_points
            
        except Exception as e:
            print(f"Error detecting landmarks: {e}")
            return None
            
    def get_face_embedding(self, face_img: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate a 128D face embedding for recognition/comparison
        
        Args:
            face_img: BGR face image with detected landmarks
            
        Returns:
            128D face embedding vector or None if error
        """
        if self.face_recognizer is None:
            print("Face recognizer not available")
            return None
            
        try:
            # Convert to RGB (dlib needs RGB instead of BGR)
            rgb_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            dlib_faces = self.detector(rgb_img)
            
            if not dlib_faces:
                return None
                
            # Use the first (largest) face
            face_rect = dlib_faces[0]
            
            # Get landmarks
            landmarks = self.landmark_predictor(rgb_img, face_rect)
            
            # Compute face embedding
            face_embedding = self.face_recognizer.compute_face_descriptor(rgb_img, landmarks)
            
            # Convert to numpy array
            embedding_array = np.array(face_embedding)
            
            return embedding_array
            
        except Exception as e:
            print(f"Error generating face embedding: {e}")
            return None
            
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate similarity between two face embeddings
        
        Args:
            embedding1: First face embedding
            embedding2: Second face embedding
            
        Returns:
            Similarity score (0 to 1, higher is more similar)
        """
        try:
            # Calculate Euclidean distance
            distance = np.linalg.norm(embedding1 - embedding2)
            
            # Convert distance to similarity (0 to 1)
            # Typically, distance < 0.6 means same person
            # We'll use an exponential transformation
            similarity = np.exp(-distance)
            
            return similarity
            
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
            
    def group_faces(self, face_embeddings: Dict[str, np.ndarray], threshold: float = 0.5) -> Dict[int, List[str]]:
        """
        Group faces based on similarity
        
        Args:
            face_embeddings: Dictionary mapping face IDs to embeddings
            threshold: Similarity threshold for grouping (0.0 to 1.0)
            
        Returns:
            Dictionary mapping group IDs to lists of face IDs
        """
        # Initialize groups
        groups = {}
        group_id = 0
        processed_faces = set()
        
        # Process each face
        face_ids = list(face_embeddings.keys())
        
        for i, face_id in enumerate(face_ids):
            # Skip already processed faces
            if face_id in processed_faces:
                continue
                
            # Create a new group
            current_group = [face_id]
            processed_faces.add(face_id)
            
            # Find similar faces
            for j in range(i + 1, len(face_ids)):
                other_face_id = face_ids[j]
                
                # Skip already processed faces
                if other_face_id in processed_faces:
                    continue
                    
                # Calculate similarity
                similarity = self.calculate_similarity(
                    face_embeddings[face_id],
                    face_embeddings[other_face_id]
                )
                
                # Add to group if similar enough
                if similarity >= threshold:
                    current_group.append(other_face_id)
                    processed_faces.add(other_face_id)
                    
            # Add group if it has at least one face
            if current_group:
                groups[group_id] = current_group
                group_id += 1
                
        return groups
        
    def serialize_landmarks(self, landmarks: List[Tuple[int, int]]) -> str:
        """Convert landmarks to a serialized string"""
        try:
            # Convert to list of lists for JSON serialization
            landmarks_list = [[x, y] for x, y in landmarks]
            return json.dumps(landmarks_list)
        except Exception as e:
            print(f"Error serializing landmarks: {e}")
            return "[]"
            
    def deserialize_landmarks(self, landmarks_str: str) -> List[Tuple[int, int]]:
        """Convert serialized string back to landmarks"""
        try:
            landmarks_list = json.loads(landmarks_str)
            return [(x, y) for x, y in landmarks_list]
        except Exception as e:
            print(f"Error deserializing landmarks: {e}")
            return []
            
    def serialize_embedding(self, embedding: np.ndarray) -> str:
        """Convert embedding to a serialized string"""
        try:
            # Convert embedding to base64 for storage
            embedding_bytes = embedding.tobytes()
            embedding_b64 = base64.b64encode(embedding_bytes).decode('utf-8')
            return embedding_b64
        except Exception as e:
            print(f"Error serializing embedding: {e}")
            return ""
            
    def deserialize_embedding(self, embedding_str: str) -> Optional[np.ndarray]:
        """Convert serialized string back to embedding"""
        try:
            # Convert base64 back to numpy array
            embedding_bytes = base64.b64decode(embedding_str)
            embedding = np.frombuffer(embedding_bytes, dtype=np.float64)
            return embedding
        except Exception as e:
            print(f"Error deserializing embedding: {e}")
            return None
            
    def visualize_landmarks(self, face_img: np.ndarray, landmarks: List[Tuple[int, int]]) -> np.ndarray:
        """Draw landmarks on face image for visualization"""
        try:
            # Create a copy of the image
            vis_img = face_img.copy()
            
            # Draw each landmark
            for x, y in landmarks:
                cv2.circle(vis_img, (x, y), 2, (0, 255, 0), -1)
                
            return vis_img
        except Exception as e:
            print(f"Error visualizing landmarks: {e}")
            return face_img
            
    def process_face(self, face_img: np.ndarray) -> Dict[str, Any]:
        """
        Process a face image to extract landmarks and embedding

        Args:
            face_img: BGR face image

        Returns:
            Dictionary with landmarks, embedding, and visualization
        """
        # Check if dlib is available
        if not DLIB_AVAILABLE or not self.detector or not self.landmark_predictor or not self.face_recognizer:
            return {
                "success": False,
                "error": "Face landmark detection not available - missing dlib or models"
            }

        try:
            # Get landmarks
            landmarks = self.detect_landmarks(face_img)

            if landmarks is None:
                return {
                    "success": False,
                    "error": "No face or landmarks detected"
                }

            # Get embedding
            embedding = self.get_face_embedding(face_img)

            if embedding is None:
                return {
                    "success": False,
                    "error": "Failed to generate face embedding"
                }

            # Create visualization
            vis_img = self.visualize_landmarks(face_img, landmarks)

            # Serialize for storage
            landmarks_str = self.serialize_landmarks(landmarks)
            embedding_str = self.serialize_embedding(embedding)

            return {
                "success": True,
                "landmarks": landmarks,
                "landmarks_str": landmarks_str,
                "embedding": embedding,
                "embedding_str": embedding_str,
                "visualization": vis_img
            }

        except Exception as e:
            print(f"Error processing face: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Create singleton instance
face_landmark_detector = FaceLandmarkDetector()