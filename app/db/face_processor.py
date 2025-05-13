import os
import cv2
import logging
import numpy as np
import uuid
from typing import Dict, List, Any, Optional, Callable, Tuple

# Try to import face detection and landmark modules
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("YOLO not available for face detection")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceProcessor:
    """
    Handles face detection and processing in the facial recognition pipeline.
    
    This includes:
    1. Face detection in extracted frames
    2. Face storage and metadata
    3. Basic duplicate removal
    """
    
    def __init__(self, faces_dir: str, model_dir: str = None):
        """
        Initialize the face processor
        
        Args:
            faces_dir: Directory where detected faces will be saved
            model_dir: Directory where models are stored (optional)
        """
        self.faces_dir = faces_dir
        
        # Create directories if they don't exist
        os.makedirs(self.faces_dir, exist_ok=True)
        
        # Set up model directory
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
        os.makedirs(model_dir, exist_ok=True)
        
        # Try to load YOLO model
        self.model = None
        self.face_cascade = None
        
        if YOLO_AVAILABLE:
            model_path = os.path.join(model_dir, "yolov8n-face.pt")
            
            # Check if model exists, download if not
            if not os.path.exists(model_path):
                self._download_model(model_path)
            
            # Load the model
            try:
                self.model = YOLO(model_path)
                logger.info("YOLO face detection model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading YOLO model: {str(e)}")
                self.model = None
        
        # Set up OpenCV face cascade as backup
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            logger.info("OpenCV face cascade loaded successfully")
        except Exception as e:
            logger.error(f"Error loading OpenCV face cascade: {str(e)}")
            self.face_cascade = None
        
        logger.info(f"Face processor initialized with faces_dir={faces_dir}")
    
    def _download_model(self, model_path: str):
        """
        Download the YOLO face detection model
        
        Args:
            model_path: Path where model will be saved
        """
        logger.info(f"Downloading YOLOv8 face detection model to {model_path}...")
        model_url = "https://github.com/akanametov/yolov8-face/releases/download/v0.0.0/yolov8n-face.pt"
        
        try:
            import requests
            response = requests.get(model_url, stream=True)
            response.raise_for_status()
            with open(model_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("Model downloaded successfully")
        except Exception as e:
            logger.error(f"Error downloading model: {e}")
            # Fallback to system wget if requests fails
            os.system(f"wget {model_url} -O {model_path}")
    
    def detect_faces(self, data: Dict[str, Any], progress_callback: Callable) -> Dict[str, Any]:
        """
        Detect faces in extracted frames
        
        This is the 'detection' stage processor function
        
        Args:
            data: Job data containing frames to process
            progress_callback: Callback function to report progress
            
        Returns:
            Dict with detection results and next stage info
        """
        frames = data.get('frames', [])
        video_id = data.get('video_id')
        
        if not frames:
            raise ValueError("No frames provided in job data")
        
        progress_callback(10, f"Detecting faces in {len(frames)} frames")
        
        # Prepare results
        detected_faces = []
        total_frames = len(frames)
        
        # Process each frame
        for i, frame_data in enumerate(frames):
            frame_path = frame_data.get('frame_path')
            if not frame_path or not os.path.exists(frame_path):
                logger.warning(f"Frame path not found: {frame_path}")
                continue
            
            # Update progress every 10 frames
            if i % 10 == 0:
                progress_percent = min(90, 10 + (i / total_frames) * 80)
                progress_callback(progress_percent, f"Processed {i}/{total_frames} frames, found {len(detected_faces)} faces")
            
            try:
                # Read the frame
                frame = cv2.imread(frame_path)
                if frame is None:
                    logger.warning(f"Could not read frame: {frame_path}")
                    continue
                
                # Detect faces using available method
                if self.model is not None:
                    # Use YOLO model
                    faces_in_frame = self._detect_faces_yolo(frame, frame_data)
                elif self.face_cascade is not None:
                    # Fallback to OpenCV
                    faces_in_frame = self._detect_faces_opencv(frame, frame_data)
                else:
                    logger.error("No face detection method available")
                    faces_in_frame = []
                
                # Add detected faces to results
                detected_faces.extend(faces_in_frame)
                
            except Exception as e:
                logger.exception(f"Error detecting faces in frame {frame_path}: {str(e)}")
        
        # Remove duplicates
        if detected_faces:
            unique_faces = self._remove_duplicates(detected_faces)
            logger.info(f"Found {len(unique_faces)} unique faces out of {len(detected_faces)} total detections")
        else:
            unique_faces = []
            logger.info("No faces detected in any frames")
        
        # Prepare result
        result = {
            'video_id': video_id,
            'face_count': len(unique_faces),
            'faces': unique_faces,
            'next_stage': 'landmarks',
            'next_data': {
                'video_id': video_id,
                'faces': unique_faces
            }
        }
        
        return result
    
    def _detect_faces_yolo(self, frame: np.ndarray, frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect faces using YOLO model
        
        Args:
            frame: Image frame
            frame_data: Metadata about the frame
            
        Returns:
            List of detected faces with metadata
        """
        faces_in_frame = []
        
        # Apply YOLO detection
        results = self.model(frame)
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                try:
                    # Get bounding box with error checking
                    if not hasattr(box, 'xyxy') or len(box.xyxy) == 0:
                        logger.warning(f"Invalid box detected in frame {frame_data.get('frame_number')}")
                        continue
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Expand the box slightly to include more of the face
                    padding_x = int((x2 - x1) * 0.2)
                    padding_y = int((y2 - y1) * 0.2)
                    
                    # Apply padding with boundary checks
                    x1 = max(0, x1 - padding_x)
                    y1 = max(0, y1 - padding_y)
                    x2 = min(frame.shape[1], x2 + padding_x)
                    y2 = min(frame.shape[0], y2 + padding_y)
                    
                    # Extract face
                    face = frame[y1:y2, x1:x2]
                    
                    # Skip if face is too small
                    if face.shape[0] < 64 or face.shape[1] < 64:
                        continue
                    
                    # Get confidence with error checking
                    if not hasattr(box, 'conf') or len(box.conf) == 0:
                        confidence = 0.5  # Default confidence if not available
                    else:
                        confidence = float(box.conf[0])
                    
                    # Save face and add to results
                    face_record = self._save_face(
                        face, 
                        frame_data.get('timestamp_ms', 0),
                        frame_data.get('frame_number', 0),
                        confidence
                    )
                    
                    if face_record:
                        faces_in_frame.append(face_record)
                        
                except Exception as e:
                    logger.exception(f"Error processing YOLO detection: {str(e)}")
        
        return faces_in_frame
    
    def _detect_faces_opencv(self, frame: np.ndarray, frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect faces using OpenCV
        
        Args:
            frame: Image frame
            frame_data: Metadata about the frame
            
        Returns:
            List of detected faces with metadata
        """
        faces_in_frame = []
        
        try:
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # In OpenCV's detectMultiScale, an empty result can be returned in different ways
            # Make sure we have a valid array with a length
            if faces is None or not hasattr(faces, '__len__') or len(faces) == 0:
                logger.debug(f"No faces detected in frame {frame_data.get('frame_number')}")
                return []
            
            # Process each detected face
            for (x, y, w, h) in faces:
                try:
                    # Skip invalid dimensions
                    if w <= 0 or h <= 0:
                        logger.warning(f"Invalid face dimensions ({w}x{h})")
                        continue
                    
                    # Expand the box slightly
                    padding_x = int(w * 0.1)
                    padding_y = int(h * 0.1)
                    
                    # Apply padding with boundary checks
                    x1 = max(0, x - padding_x)
                    y1 = max(0, y - padding_y)
                    x2 = min(frame.shape[1], x + w + padding_x)
                    y2 = min(frame.shape[0], y + h + padding_y)
                    
                    # Additional check to ensure valid extraction region
                    if x2 <= x1 or y2 <= y1:
                        logger.warning(f"Invalid face region ({x1},{y1},{x2},{y2})")
                        continue
                    
                    # Extract face
                    face = frame[y1:y2, x1:x2]
                    
                    # Skip if face is too small
                    if face.shape[0] < 64 or face.shape[1] < 64:
                        continue
                    
                    # Use fixed confidence for OpenCV detector
                    confidence = 0.9
                    
                    # Save face and add to results
                    face_record = self._save_face(
                        face, 
                        frame_data.get('timestamp_ms', 0),
                        frame_data.get('frame_number', 0),
                        confidence
                    )
                    
                    if face_record:
                        faces_in_frame.append(face_record)
                        
                except Exception as e:
                    logger.exception(f"Error processing OpenCV detection: {str(e)}")
            
        except Exception as e:
            logger.exception(f"Error in OpenCV face detection: {str(e)}")
        
        return faces_in_frame
    
    def _save_face(self, face: np.ndarray, timestamp_ms: int, frame_number: int, confidence: float) -> Optional[Dict[str, Any]]:
        """
        Save a detected face and prepare metadata
        
        Args:
            face: Face image data
            timestamp_ms: Timestamp in milliseconds
            frame_number: Frame number
            confidence: Detection confidence
            
        Returns:
            Face record or None if an error occurred
        """
        try:
            # Validate inputs
            if face is None or face.size == 0:
                logger.warning(f"Invalid face data in frame {frame_number}")
                return None
            
            # Generate a unique ID for this face
            face_id = str(uuid.uuid4())
            
            # Format timestamp for display
            timestamp = self._format_timestamp(timestamp_ms / 1000)
            
            # Resize face to 128x128 pixels
            face_resized = cv2.resize(face, (128, 128), interpolation=cv2.INTER_AREA)
            
            # Save face image
            face_filename = f"{face_id}.jpg"
            face_path = os.path.join(self.faces_dir, face_filename)
            
            # Make sure directory exists
            os.makedirs(os.path.dirname(face_path), exist_ok=True)
            
            # Save the resized face
            cv2.imwrite(face_path, face_resized)
            
            # Convert to relative path for frontend
            relative_path = f"/static/faces/{face_filename}"
            
            # Create basic face record
            face_record = {
                "id": face_id,
                "imageUrl": relative_path,
                "timestamp": timestamp,
                "timestamp_ms": timestamp_ms,
                "frameNumber": frame_number,
                "confidence": float(confidence) if confidence is not None else 0.5,
                "assigned": False,
                "group_id": None,
                "has_landmarks": False,
                "original_face_path": face_path  # Store original face path for landmark processing
            }
            
            logger.debug(f"Saved face {face_id} from frame {frame_number}")
            return face_record
            
        except Exception as e:
            logger.exception(f"Error saving face from frame {frame_number}: {e}")
            return None
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds as HH:MM:SS
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp string
        """
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    def _remove_duplicates(self, faces: List[Dict[str, Any]], time_threshold: float = 0.5, max_faces: int = 1000) -> List[Dict[str, Any]]:
        """
        Remove duplicate faces based on timestamp proximity

        Args:
            faces: List of detected faces
            time_threshold: Time threshold in seconds (default: 0.5)
            max_faces: Maximum number of faces to return (default: 1000)

        Returns:
            List of unique faces
        """
        # Sort by confidence
        sorted_faces = sorted(faces, key=lambda x: x["confidence"], reverse=True)

        # Filter faces that are within time_threshold of each other
        unique_faces = []
        used_timestamps = []

        for face in sorted_faces:
            # Extract timestamp in ms
            timestamp_ms = face.get("timestamp_ms", 0)

            # Check if this face is too close to any already selected face
            is_duplicate = False
            for used_ts in used_timestamps:
                if abs(timestamp_ms - used_ts) < time_threshold * 1000:  # Convert to ms
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_faces.append(face)
                used_timestamps.append(timestamp_ms)

            # Limit to max_faces - set to a much higher number to show more faces
            if len(unique_faces) >= max_faces:
                break

        # Sort by timestamp
        unique_faces = sorted(unique_faces, key=lambda x: x.get("timestamp_ms", 0))

        return unique_faces