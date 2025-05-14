import os
import cv2
import numpy as np
import uuid
import tempfile
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional, Callable

# Import face landmark and grouping modules
from db.face_landmarks import face_landmark_detector, DLIB_AVAILABLE
from db.face_groups import face_group_manager

# Flag for whether advanced face processing is available
ADVANCED_FACE_PROCESSING = DLIB_AVAILABLE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Will use YOLOv8 for face detection
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Installing required packages...")
    os.system("pip install ultralytics")
    try:
        from ultralytics import YOLO
        YOLO_AVAILABLE = True
    except ImportError:
        YOLO_AVAILABLE = False
        print("Failed to install YOLO. Will use fallback detection.")

# Try to import OpenCV tracking modules
try:
    # Import OpenCV's Tracking API
    OPENCV_TRACKING = True
    # We'll use the CSRT tracker for better accuracy
    TrackerCSRT = cv2.TrackerCSRT_create
except (ImportError, AttributeError):
    try:
        # For newer OpenCV versions
        TrackerCSRT = cv2.legacy.TrackerCSRT_create
        OPENCV_TRACKING = True
    except (ImportError, AttributeError):
        OPENCV_TRACKING = False
        print("OpenCV tracking not available. Using basic interpolation tracking.")

class FaceTrack:
    """
    Represents a face tracked across multiple frames.
    """
    def __init__(self, face_id: str, initial_box: np.ndarray, initial_frame: int, confidence: float = 0.7, chunk_id: str = None):
        self.id = face_id  # Unique track ID (different from face ID)
        self.face_id = face_id  # Initial face ID, can be changed
        self.boxes = {initial_frame: initial_box}  # Frame number to box mapping
        self.last_frame = initial_frame
        self.tracker = None  # Will be initialized when needed
        self.confidence = confidence
        self.identity_code = None  # Identity group assigned to this track
        self.active = True
        self.missed_frames = 0
        self.embedding = None  # Face embedding for recognition
        self.chunk_id = chunk_id  # Track which processing chunk this track belongs to
        
    def add_detection(self, frame_number: int, box: np.ndarray, confidence: float = None):
        """Add a new detection to this track"""
        self.boxes[frame_number] = box
        self.last_frame = frame_number
        self.missed_frames = 0
        self.active = True
        if confidence is not None:
            # Update confidence with exponential decay
            self.confidence = 0.8 * self.confidence + 0.2 * confidence
    
    def get_latest_box(self):
        """Get the most recent detection box"""
        return self.boxes[self.last_frame]
    
    def mark_missed(self):
        """Mark this track as missed in the current frame"""
        self.missed_frames += 1
        if self.missed_frames > 15:  # Deactivate after 15 missed frames
            self.active = False
    
    def initialize_tracker(self, frame):
        """Initialize an OpenCV tracker for this track"""
        if OPENCV_TRACKING:
            self.tracker = TrackerCSRT()
            bbox = self.get_latest_box()
            x1, y1, x2, y2 = map(int, bbox)
            self.tracker.init(frame, (x1, y1, x2-x1, y2-y1))

class FaceDetector:
    def __init__(self):
        # Set up model path and directory
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, "yolov8n-face.pt")

        # Download model if not present
        if not os.path.exists(model_path):
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

        # Load the model
        self.model = None
        self.face_cascade = None
        
        if YOLO_AVAILABLE:
            try:
                self.model = YOLO(model_path)
                logger.info("Face detection model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                self.model = None
        
        # Set up fallback OpenCV face detector
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            logger.info("OpenCV face cascade loaded successfully")
        except Exception as e:
            logger.error(f"Error loading OpenCV face cascade: {e}")

        # Set up face storage directory
        self.faces_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "faces")
        os.makedirs(self.faces_dir, exist_ok=True)
        
        # Initialize face tracks list
        self.tracks = []
        
        # Set up identity group counter for automatic group creation
        self.next_identity_group = 1

    def process_video(self, data: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """
        Process video frames with continuous tracking
        
        This is the 'detection' stage processor function
        
        Args:
            data: Job data with frames to process
            progress_callback: Function to report progress
            
        Returns:
            Dict with detection results
        """
        frames = data.get('frames', [])
        video_id = data.get('video_id')
        frame_directory = data.get('frame_directory')
        enable_tracking = data.get('enable_tracking', True)
        fps = data.get('fps', 30)
        
        if not frames:
            logger.warning("No frames provided for processing")
            return {
                'video_id': video_id,
                'face_count': 0,
                'faces': [],
                'error': 'No frames provided'
            }
        
        if progress_callback:
            progress_callback(10, f"Processing {len(frames)} frames with tracking={enable_tracking}")
        logger.info(f"Processing {len(frames)} frames with tracking={enable_tracking}")
        
        # Reset tracks
        self.tracks = []
        
        # Process all frames in sequence for tracking
        detected_faces = []
        processing_results = {}
        
        # Store already processed face IDs to avoid duplicates
        processed_face_ids = set()
        
        # Process frames in sequence
        for i, frame_data in enumerate(frames):
            frame_path = frame_data.get('frame_path')
            frame_number = frame_data.get('frame_number')
            
            if not frame_path or not os.path.exists(frame_path):
                logger.warning(f"Frame path not found: {frame_path}")
                continue
            
            try:
                # Read the frame
                frame = cv2.imread(frame_path)
                if frame is None:
                    logger.warning(f"Could not read frame: {frame_path}")
                    continue
                
                # First detect faces with detector
                faces_in_frame = []
                
                if self.model is not None:
                    # Use YOLO model for detection
                    faces_in_frame = self._detect_faces_yolo(frame, frame_data)
                elif self.face_cascade is not None:
                    # Fallback to OpenCV
                    faces_in_frame = self._detect_faces_opencv(frame, frame_data)
                
                # Get face boxes from detections
                boxes = []
                face_records = []
                
                for face in faces_in_frame:
                    try:
                        # Extract bounding box from face record
                        if 'box' in face:
                            box = face['box']
                            boxes.append((box, face))
                            face_records.append(face)
                        else:
                            logger.warning(f"Face record missing box: {face}")
                    except Exception as e:
                        logger.error(f"Error processing face in frame {frame_number}: {e}")
                
                # If tracking is enabled, update tracks with new detections
                if enable_tracking:
                    # Update existing tracks first
                    self._update_tracks(frame, frame_number, boxes)
                    
                    # Get all active tracks for this frame
                    active_tracks = [track for track in self.tracks if track.active]
                    
                    # For each active track, save a face if we haven't already
                    for track in active_tracks:
                        # Only save a new face if this track spans multiple frames
                        track_frames = list(track.boxes.keys())
                        
                        # Skip tracks we've already processed
                        if track.face_id in processed_face_ids:
                            continue
                        
                        # Get the best frame for this track (highest confidence detection)
                        best_frame_data = None
                        for frame_num in track_frames:
                            # Find corresponding frame_data
                            for fd in frames:
                                if fd.get('frame_number') == frame_num:
                                    best_frame_data = fd
                                    break
                            if best_frame_data:
                                break
                        
                        if not best_frame_data:
                            # Use current frame as fallback
                            best_frame_data = frame_data
                        
                        # Get current box
                        box = track.get_latest_box()
                        x1, y1, x2, y2 = map(int, box)
                        
                        # Extract face from frame
                        try:
                            face = frame[y1:y2, x1:x2]
                            
                            # Skip invalid or too small faces
                            if face.size == 0 or face.shape[0] < 64 or face.shape[1] < 64:
                                continue
                            
                            # Save face with track ID
                            face_record = self._save_face(
                                face, 
                                best_frame_data.get('timestamp_ms', 0),
                                best_frame_data.get('frame_number', 0),
                                track.confidence
                            )
                            
                            # Update face record with tracking info
                            if face_record:
                                face_record['track_id'] = track.id
                                face_record['track_length'] = len(track_frames)
                                face_record['identity_code'] = track.identity_code
                                detected_faces.append(face_record)
                                processed_face_ids.add(track.face_id)
                                
                                # Also add this face to landmarks processing list
                                if ADVANCED_FACE_PROCESSING:
                                    # Process the face to detect landmarks and generate embedding
                                    try:
                                        landmark_data = face_landmark_detector.process_face(face)
                                        
                                        # If we successfully detected landmarks, add to the face record
                                        if landmark_data.get("success", False):
                                            # Add embedding to the track
                                            track.embedding = face_landmark_detector.deserialize_embedding(
                                                landmark_data["embedding_str"]
                                            )
                                            
                                            # Add to face record
                                            face_record.update({
                                                "has_landmarks": True,
                                                "landmarks_str": landmark_data["landmarks_str"],
                                                "embedding_str": landmark_data["embedding_str"]
                                            })
                                    except Exception as e:
                                        logger.error(f"Error processing landmarks: {e}")
                        except Exception as e:
                            logger.error(f"Error extracting face from track: {e}")
                
                # Process any detected faces that aren't part of tracks
                for face_record in face_records:
                    if ('id' in face_record and face_record['id'] not in processed_face_ids and 
                        'box' in face_record):
                        try:
                            # Extract box
                            x1, y1, x2, y2 = map(int, face_record['box'])
                            face = frame[y1:y2, x1:x2]
                            
                            # Skip invalid faces
                            if face.size == 0 or face.shape[0] < 64 or face.shape[1] < 64:
                                continue
                            
                            # Save the face
                            if 'id' not in face_record:
                                face_record['id'] = str(uuid.uuid4())
                                
                            detected_faces.append(face_record)
                            processed_face_ids.add(face_record['id'])
                        except Exception as e:
                            logger.error(f"Error saving individual face: {e}")
                
                # Update progress periodically
                if i % 10 == 0:
                    message = f"Processed {i}/{len(frames)} frames, found {len(detected_faces)} faces in {len(self.tracks)} tracks"
                    logger.info(message)
                    if progress_callback:
                        progress_callback(
                            min(90, 10 + (i / len(frames)) * 80), 
                            message
                        )
                
                # Store processing results for this frame
                processing_results[frame_number] = {
                    'frame_path': frame_path,
                    'detected_faces': len(faces_in_frame),
                    'active_tracks': len([t for t in self.tracks if t.active]),
                    'timestamp_ms': frame_data.get('timestamp_ms', 0)
                }
                
            except Exception as e:
                logger.exception(f"Error processing frame {frame_path}: {e}")
        
        # Assign identity groups to tracks that have similar embeddings
        if ADVANCED_FACE_PROCESSING and len(self.tracks) > 0:
            self._group_tracks_by_embeddings()
        
        message = f"Completed processing {len(frames)} frames, found {len(detected_faces)} faces in {len(self.tracks)} tracks"
        logger.info(message)
        if progress_callback:
            progress_callback(95, message)
        
        # Prepare result
        result = {
            'video_id': video_id,
            'face_count': len(detected_faces),
            'track_count': len(self.tracks),
            'faces': detected_faces,
            'processing_results': processing_results,
            'next_stage': 'landmarks',
            'next_data': {
                'video_id': video_id,
                'faces': detected_faces
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
            List of face records with bounding boxes
        """
        faces_in_frame = []
        
        try:
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
                        
                        # Skip if box is invalid
                        if x2 <= x1 or y2 <= y1:
                            continue
                            
                        # Get confidence with error checking
                        if not hasattr(box, 'conf') or len(box.conf) == 0:
                            confidence = 0.5  # Default confidence if not available
                        else:
                            confidence = float(box.conf[0])
                        
                        # Generate face ID
                        face_id = str(uuid.uuid4())
                        
                        # Create face record with box
                        face_record = {
                            'id': face_id,
                            'confidence': confidence,
                            'box': [x1, y1, x2, y2],
                            'frame_number': frame_data.get('frame_number'),
                            'timestamp_ms': frame_data.get('timestamp_ms')
                        }
                        
                        faces_in_frame.append(face_record)
                    except Exception as e:
                        logger.error(f"Error processing YOLO detection: {e}")
        except Exception as e:
            logger.error(f"Error in YOLO face detection: {e}")
        
        return faces_in_frame

    def _detect_faces_opencv(self, frame: np.ndarray, frame_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect faces using OpenCV cascade
        
        Args:
            frame: Image frame
            frame_data: Metadata about the frame
            
        Returns:
            List of face records with bounding boxes
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
                return []
            
            # Process each detected face
            for (x, y, w, h) in faces:
                try:
                    # Skip invalid dimensions
                    if w <= 0 or h <= 0:
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
                        continue
                    
                    # Generate face ID
                    face_id = str(uuid.uuid4())
                    
                    # Use fixed confidence for OpenCV detector
                    confidence = 0.9
                    
                    # Create face record with box
                    face_record = {
                        'id': face_id,
                        'confidence': confidence,
                        'box': [x1, y1, x2, y2],
                        'frame_number': frame_data.get('frame_number'),
                        'timestamp_ms': frame_data.get('timestamp_ms')
                    }
                    
                    faces_in_frame.append(face_record)
                except Exception as e:
                    logger.error(f"Error processing OpenCV detection: {e}")
        except Exception as e:
            logger.error(f"Error in OpenCV face detection: {e}")
        
        return faces_in_frame

    def _update_tracks(self, frame: np.ndarray, frame_number: int, detections: List[Tuple[np.ndarray, Dict[str, Any]]]):
        """
        Update tracks with new detections using IoU matching
        
        Args:
            frame: Current frame
            frame_number: Current frame number
            detections: List of (box, face_record) tuples
        """
        # First, update all existing trackers
        if OPENCV_TRACKING:
            self._update_trackers(frame, frame_number)
        
        # Mark all tracks as missed (will be updated below if matched)
        for track in self.tracks:
            if track.active:
                track.mark_missed()
        
        # Convert detections to just boxes for matching
        detection_boxes = [box for box, _ in detections]
        
        # No tracks or detections? Return early
        if not self.tracks or not detection_boxes:
            # If we have detections but no tracks, create new tracks for each detection
            if detection_boxes and not self.tracks:
                for box, face_record in detections:
                    new_track = FaceTrack(
                        face_record['id'], 
                        box, 
                        frame_number, 
                        face_record['confidence']
                    )
                    self.tracks.append(new_track)
            return
        
        # Get boxes of current active tracks
        track_boxes = []
        active_tracks = []
        
        for track in self.tracks:
            if track.active and track.last_frame != frame_number:
                try:
                    track_boxes.append(track.get_latest_box())
                    active_tracks.append(track)
                except Exception as e:
                    logger.error(f"Error getting box for track {track.id}: {e}")
        
        # Compute IoU between all track and detection boxes
        if track_boxes and detection_boxes:
            iou_matrix = self._compute_iou_matrix(track_boxes, detection_boxes)
            
            # Match detections to tracks using Hungarian algorithm
            matched_indices = self._match_detections_to_tracks(iou_matrix, len(track_boxes), len(detection_boxes))
            
            # Update matched tracks with new detections
            for track_idx, detection_idx in matched_indices:
                track = active_tracks[track_idx]
                box, face_record = detections[detection_idx]
                
                # Update track with new detection
                track.add_detection(frame_number, box, face_record['confidence'])
                
                # Initialize OpenCV tracker if tracking enabled
                if OPENCV_TRACKING and track.tracker is None:
                    track.initialize_tracker(frame)
            
            # Create new tracks for unmatched detections
            unmatched_detections = [
                i for i in range(len(detection_boxes)) 
                if i not in [detection_idx for _, detection_idx in matched_indices]
            ]
            
            for i in unmatched_detections:
                box, face_record = detections[i]
                new_track = FaceTrack(
                    face_record['id'], 
                    box, 
                    frame_number, 
                    face_record['confidence']
                )
                self.tracks.append(new_track)
                
                # Initialize OpenCV tracker if tracking enabled
                if OPENCV_TRACKING:
                    new_track.initialize_tracker(frame)
        
    def _update_trackers(self, frame: np.ndarray, frame_number: int):
        """
        Update the OpenCV trackers for all active tracks
        
        Args:
            frame: Current frame
            frame_number: Current frame number
        """
        if not OPENCV_TRACKING:
            return
            
        for track in self.tracks:
            if track.active and track.last_frame != frame_number and track.tracker is not None:
                # Update the tracker with the current frame
                success, bbox = track.tracker.update(frame)
                
                if success:
                    # Convert from (x, y, w, h) to (x1, y1, x2, y2)
                    x, y, w, h = bbox
                    x1, y1, x2, y2 = int(x), int(y), int(x+w), int(y+h)
                    
                    # Add the tracked position as a new detection
                    track.add_detection(frame_number, np.array([x1, y1, x2, y2]))
                    
                    # Downgrade confidence slightly when using just tracking
                    track.confidence *= 0.95
                else:
                    # Tracking failed
                    track.mark_missed()
                    track.tracker = None

    def _compute_iou_matrix(self, track_boxes: List[np.ndarray], detection_boxes: List[np.ndarray]) -> np.ndarray:
        """
        Compute IoU (Intersection over Union) between all track and detection boxes
        
        Args:
            track_boxes: List of track bounding boxes
            detection_boxes: List of detection bounding boxes
            
        Returns:
            IoU matrix of shape (num_tracks, num_detections)
        """
        iou_matrix = np.zeros((len(track_boxes), len(detection_boxes)))
        
        for t_idx, track_box in enumerate(track_boxes):
            for d_idx, detection_box in enumerate(detection_boxes):
                iou_matrix[t_idx, d_idx] = self._calculate_iou(track_box, detection_box)
        
        return iou_matrix
    
    def _calculate_iou(self, box1: np.ndarray, box2: np.ndarray) -> float:
        """
        Calculate IoU between two boxes
        
        Args:
            box1: First box in format [x1, y1, x2, y2]
            box2: Second box in format [x1, y1, x2, y2]
            
        Returns:
            IoU score between 0 and 1
        """
        # Calculate intersection area
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
            
        intersection_area = (x2 - x1) * (y2 - y1)
        
        # Calculate union area
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union_area = box1_area + box2_area - intersection_area
        
        # Calculate IoU
        if union_area > 0:
            return intersection_area / union_area
        else:
            return 0.0

    def _match_detections_to_tracks(self, iou_matrix: np.ndarray, num_tracks: int, num_detections: int, iou_threshold: float = 0.3) -> List[Tuple[int, int]]:
        """
        Match detections to tracks using greedy matching with IoU threshold
        
        Args:
            iou_matrix: IoU matrix of shape (num_tracks, num_detections)
            num_tracks: Number of tracks
            num_detections: Number of detections
            iou_threshold: Minimum IoU to consider a match
            
        Returns:
            List of matched (track_idx, detection_idx) pairs
        """
        # Greedy matching based on highest IoU
        matches = []
        
        # Create a copy of the IoU matrix
        iou_copy = iou_matrix.copy()
        
        # While there are potential matches
        while np.max(iou_copy) >= iou_threshold:
            # Find best match
            track_idx, detection_idx = np.unravel_index(np.argmax(iou_copy), iou_copy.shape)
            
            # Add match if above threshold
            if iou_copy[track_idx, detection_idx] >= iou_threshold:
                matches.append((track_idx, detection_idx))
                
                # Remove this match from consideration
                iou_copy[track_idx, :] = 0
                iou_copy[:, detection_idx] = 0
            else:
                break
        
        return matches

    def _save_face(self, face: np.ndarray, timestamp_ms: int, frame_number: int, confidence: float) -> Dict[str, Any]:
        """
        Save a detected face and create metadata
        
        Args:
            face: Face image
            timestamp_ms: Timestamp in milliseconds
            frame_number: Frame number
            confidence: Detection confidence
            
        Returns:
            Face record dictionary
        """
        try:
            # Generate a unique ID for this face
            face_id = str(uuid.uuid4())
            
            # Format timestamp for display
            timestamp = self._format_timestamp(timestamp_ms / 1000)
            
            # Check if face is valid
            if face is None or face.size == 0 or face.shape[0] == 0 or face.shape[1] == 0:
                logger.warning(f"Invalid face image detected, cannot save")
                return None
                
            # Convert to BGR if not already (sometimes faces can be grayscale)
            if len(face.shape) == 2:  # Grayscale
                face = cv2.cvtColor(face, cv2.COLOR_GRAY2BGR)
                
            # Resize face to 128x128 pixels
            face_resized = cv2.resize(face, (128, 128), interpolation=cv2.INTER_AREA)
            
            # Save face image
            face_filename = f"{face_id}.jpg"
            face_path = os.path.join(self.faces_dir, face_filename)
            
            # Make sure directory exists
            os.makedirs(os.path.dirname(face_path), exist_ok=True)
            
            # Save the resized face with high quality (95%)
            # PNG is lossless but larger, JPG is smaller but needs quality parameter
            quality_params = [cv2.IMWRITE_JPEG_QUALITY, 95]
            success = cv2.imwrite(face_path, face_resized, quality_params)
            
            if not success:
                logger.warning(f"Failed to save face image to {face_path}")
                # Try with PNG format instead
                png_path = face_path.replace(".jpg", ".png")
                png_success = cv2.imwrite(png_path, face_resized)
                
                if png_success:
                    logger.info(f"Successfully saved face as PNG to {png_path}")
                    # Update filename for the return value
                    face_filename = face_filename.replace(".jpg", ".png")
                else:
                    logger.error(f"Failed to save face image in any format")
                    return None
            
            # Convert to relative path for frontend
            relative_path = f"/static/faces/{face_filename}"
            
            # Create basic face record with all necessary fields
            face_record = {
                "id": face_id,
                "imageUrl": relative_path,  # This is the key expected by background_processor
                "image_url": relative_path,  # Alternative key for backward compatibility
                "timestamp": timestamp,
                "timestamp_ms": timestamp_ms,
                "frameNumber": frame_number,
                "confidence": float(confidence) if confidence is not None else 0.5,
                "labeled": False,
                "identity_code": None,
                "has_landmarks": False,
                "metadata": {
                    "timestamp": timestamp,
                    "timestamp_ms": timestamp_ms,
                    "frame": frame_number,
                    "confidence": float(confidence) if confidence is not None else 0.5
                },
                "assigned": False
            }
            
            return face_record
        except Exception as e:
            logger.error(f"Error saving face: {e}")
            return None

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS"""
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
    def recover_processing(self, video_id: str) -> List[Dict[str, Any]]:
        """
        Recovery function for partially processed videos
        
        Args:
            video_id: ID of the video to recover
            
        Returns:
            List of detected faces that were successfully processed
        """
        logger.info(f"Attempting to recover processing for video {video_id}")
        
        # Check if we have any faces already processed for this track
        detected_faces = []
        
        # For each active track, extract saved faces
        for track in self.tracks:
            if track.active and hasattr(track, 'face_id'):
                # Look for face images that were already saved
                face_id = track.face_id
                face_path = os.path.join(self.faces_dir, f"{face_id}.jpg")  # Must match _save_face format (line 756)
                
                if os.path.exists(face_path):
                    # Create a face record for this saved face
                    timestamp = "00:00:00"  # Default timestamp
                    
                    # Get a frame number if available
                    frame_number = 0
                    if hasattr(track, 'last_frame'):
                        frame_number = track.last_frame
                    
                    # Create face record - use the SAME filename format as _save_face
                    face_record = {
                        "id": face_id,
                        "imageUrl": f"/static/faces/{face_id}.jpg",  # Must match _save_face format (line 766)
                        "image_url": f"/static/faces/{face_id}.jpg",  # Must match _save_face format
                        "timestamp": timestamp,
                        "confidence": track.confidence if hasattr(track, 'confidence') else 0.7,
                        "frameNumber": frame_number,
                        "labeled": False,
                        "assigned": False,
                        "identity_code": track.identity_code if hasattr(track, 'identity_code') else None,
                        "metadata": {
                            "timestamp": timestamp,
                            "frame": frame_number,
                            "confidence": track.confidence if hasattr(track, 'confidence') else 0.7
                        }
                    }
                    
                    detected_faces.append(face_record)
                    logger.info(f"Recovered face {face_id} from track")
        
        # If we found faces, return them
        if detected_faces:
            logger.info(f"Successfully recovered {len(detected_faces)} faces")
            return detected_faces
        
        logger.warning(f"No faces recovered for video {video_id}")
        return []
    
    def process_video_file(self, video_path: str, time_window_ms: int = 100) -> List[Dict[str, Any]]:
        """
        Process a video file for face detection using frame extraction
        
        Args:
            video_path: Path to the video file
            time_window_ms: Time window in milliseconds (used for compatibility)
            
        Returns:
            List of detected faces
        """
        logger.info(f"Processing video file: {video_path}")
        
        try:
            # Open the video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")
                
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(f"Video info: {width}x{height}, {fps} FPS, {frame_count} frames")
            
            # Extract frames from the video first
            frames = []
            temp_frame_dir = os.path.join(tempfile.gettempdir(), f"video_frames_{uuid.uuid4()}")
            os.makedirs(temp_frame_dir, exist_ok=True)
            
            try:
                # Sample frames (use time_window_ms for frame sampling rate)
                frames_per_sample = max(1, int((time_window_ms / 1000) * fps))
                logger.info(f"Extracting frames (sampling every {frames_per_sample} frames)")
                
                current_frame = 0
                frame_data_list = []
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                        
                    # Process every Nth frame
                    if current_frame % frames_per_sample == 0:
                        # Calculate timestamp
                        timestamp_ms = int((current_frame / fps) * 1000)
                        
                        # Save frame to temp directory
                        frame_filename = f"frame_{current_frame:06d}.jpg"
                        frame_path = os.path.join(temp_frame_dir, frame_filename)
                        cv2.imwrite(frame_path, frame)
                        
                        # Add frame metadata
                        frame_data = {
                            'frame_number': current_frame,
                            'frame_path': frame_path,
                            'timestamp_ms': timestamp_ms
                        }
                        frame_data_list.append(frame_data)
                    
                    current_frame += 1
                    
                    # Log progress
                    if current_frame % 100 == 0:
                        logger.info(f"Extracted {len(frame_data_list)} frames from {current_frame}/{frame_count}")
                
                # Release video after frame extraction
                cap.release()
                
                # Prepare data for processing
                process_data = {
                    'frames': frame_data_list,
                    'video_id': os.path.basename(video_path).split('.')[0],
                    'frame_directory': temp_frame_dir,
                    'enable_tracking': True,
                    'fps': fps
                }
                
                # Process frames with tracking
                # Use a simple progress callback for logging
                def log_progress(percent, message):
                    logger.info(f"Processing progress: {percent:.1f}% - {message}")
                
                try:
                    # Process the frames
                    result = self.process_video(process_data, log_progress)
                    
                    # Get the detected faces from the result
                    faces = result.get('faces', [])
                except Exception as e:
                    logger.error(f"Error during video processing: {e}")
                    logger.info("Attempting to recover partial results...")
                    
                    # Attempt to recover any faces that were already processed
                    faces = []
                    
                    # If there are active tracks, we can recover faces from them
                    if hasattr(self, 'tracks') and self.tracks:
                        faces = self.recover_processing(os.path.basename(video_path).split('.')[0])
                        
                        if faces:
                            logger.info(f"Recovered {len(faces)} faces after processing error")
                        else:
                            logger.warning("No faces could be recovered - results will be incomplete")
                            # Re-raise the exception if we couldn't recover any faces
                            if not faces:
                                raise
                
                # Ensure the face records have the required fields for compatibility with background_processor
                for face in faces:
                    # Make sure each face has required fields
                    if 'id' not in face:
                        face['id'] = str(uuid.uuid4())
                    if 'imageUrl' not in face and 'image_url' in face:
                        face['imageUrl'] = face['image_url']
                    elif 'imageUrl' not in face:
                        # If no image URL, construct a default one
                        face['imageUrl'] = f"/static/faces/{face['id']}.jpg"  # Must match _save_face format (line 766)
                    if 'timestamp' not in face and 'timestamp_ms' in face:
                        timestamp_ms = face['timestamp_ms']
                        face['timestamp'] = self._format_timestamp(timestamp_ms / 1000)
                    elif 'timestamp' not in face:
                        face['timestamp'] = "00:00:00"
                        
                logger.info(f"Returning {len(faces)} processed faces")
                
                # Return the processed faces
                return faces
                
            finally:
                # Clean up temp directory
                try:
                    import shutil
                    shutil.rmtree(temp_frame_dir, ignore_errors=True)
                except Exception as e:
                    logger.error(f"Error cleaning up temp directory: {e}")
            
        except Exception as e:
            logger.exception(f"Error processing video: {e}")
            raise
    
    def _group_tracks_by_embeddings(self, similarity_threshold: float = 0.6):
        """
        Group tracks by embedding similarity and assign identity codes
        
        Args:
            similarity_threshold: Similarity threshold for grouping (0-1)
        """
        # Filter tracks with embeddings
        tracks_with_embeddings = [track for track in self.tracks if track.embedding is not None]
        
        if not tracks_with_embeddings:
            logger.info("No tracks with embeddings to group")
            return
        
        # Create a similarity matrix between all tracks
        num_tracks = len(tracks_with_embeddings)
        similarity_matrix = np.zeros((num_tracks, num_tracks))
        
        # Calculate similarity between all pairs of tracks
        for i in range(num_tracks):
            for j in range(i, num_tracks):
                # For the diagonal, use maximum similarity
                if i == j:
                    similarity_matrix[i, j] = 1.0
                    continue
                
                track_i = tracks_with_embeddings[i]
                track_j = tracks_with_embeddings[j]
                
                # Calculate cosine similarity between embeddings
                similarity = np.dot(track_i.embedding, track_j.embedding)
                
                # Update the matrix (symmetric)
                similarity_matrix[i, j] = similarity
                similarity_matrix[j, i] = similarity
        
        # Assign identity codes based on similarity
        assigned_groups = {}  # Track index to group ID mapping
        
        # Start with highest similarities
        while np.max(similarity_matrix) >= similarity_threshold:
            # Find the highest similarity
            i, j = np.unravel_index(np.argmax(similarity_matrix), similarity_matrix.shape)
            
            if similarity_matrix[i, j] < similarity_threshold:
                break
                
            # Mark as processed
            similarity_matrix[i, j] = 0
            
            # Get the tracks
            track_i = tracks_with_embeddings[i]
            track_j = tracks_with_embeddings[j]
            
            # Check if either track is already assigned to a group
            group_i = assigned_groups.get(i)
            group_j = assigned_groups.get(j)
            
            if group_i is None and group_j is None:
                # Neither track is assigned, create a new group
                group_id = f"PERSON-{self.next_identity_group:04d}"
                self.next_identity_group += 1
                
                # Assign both tracks to this group
                assigned_groups[i] = group_id
                assigned_groups[j] = group_id
                
                # Update track identity codes
                track_i.identity_code = group_id
                track_j.identity_code = group_id
                
            elif group_i is not None and group_j is None:
                # Track i is already assigned, assign track j to the same group
                assigned_groups[j] = group_i
                track_j.identity_code = group_i
                
            elif group_i is None and group_j is not None:
                # Track j is already assigned, assign track i to the same group
                assigned_groups[i] = group_j
                track_i.identity_code = group_j
                
            elif group_i != group_j:
                # Both tracks are assigned to different groups
                # Merge the groups by assigning all tracks in group_j to group_i
                for k, group in assigned_groups.items():
                    if group == group_j:
                        assigned_groups[k] = group_i
                        tracks_with_embeddings[k].identity_code = group_i
        
        # For any unassigned tracks, assign new group IDs
        for i, track in enumerate(tracks_with_embeddings):
            if i not in assigned_groups:
                group_id = f"PERSON-{self.next_identity_group:04d}"
                self.next_identity_group += 1
                
                assigned_groups[i] = group_id
                track.identity_code = group_id
        
        # Print summary
        logger.info(f"Grouped {len(tracks_with_embeddings)} tracks into {len(set(assigned_groups.values()))} identity groups")
        group_counts = {}
        for group_id in assigned_groups.values():
            group_counts[group_id] = group_counts.get(group_id, 0) + 1
        
        for group_id, count in group_counts.items():
            logger.info(f"Group {group_id}: {count} tracks")

# Create singleton instance
face_detector = FaceDetector()