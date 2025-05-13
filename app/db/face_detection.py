import os
import cv2
import numpy as np
import uuid
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Import face landmark and grouping modules
from db.face_landmarks import face_landmark_detector, DLIB_AVAILABLE
from db.face_groups import face_group_manager

# Flag for whether advanced face processing is available
ADVANCED_FACE_PROCESSING = DLIB_AVAILABLE

# Will use YOLOv8 for face detection
try:
    from ultralytics import YOLO
except ImportError:
    print("Installing required packages...")
    os.system("pip install ultralytics")
    from ultralytics import YOLO

class FaceDetector:
    def __init__(self):
        # Set up model path and directory
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, "yolov8n-face.pt")

        # Download model if not present
        if not os.path.exists(model_path):
            print(f"Downloading YOLOv8 face detection model to {model_path}...")
            model_url = "https://github.com/akanametov/yolov8-face/releases/download/v0.0.0/yolov8n-face.pt"
            try:
                import requests
                response = requests.get(model_url, stream=True)
                response.raise_for_status()
                with open(model_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print("Model downloaded successfully")
            except Exception as e:
                print(f"Error downloading model: {e}")
                # Fallback to system wget if requests fails
                os.system(f"wget {model_url} -O {model_path}")

        # Load the model
        try:
            self.model = YOLO(model_path)
            # Set up face storage directory
            self.faces_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "faces")
            os.makedirs(self.faces_dir, exist_ok=True)
            print("Face detection model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            # Fallback to using a basic OpenCV face detector if YOLO fails
            self.model = None
            print("Using fallback face detection method")
            # Make sure opencv is installed
            try:
                import cv2
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            except:
                print("Error loading OpenCV face detector")

    def process_video(self, video_path: str, time_window_ms: int = 100) -> List[Dict[str, Any]]:
        """
        Process a video file and detect faces at specified time intervals.

        Args:
            video_path: Path to the video file
            time_window_ms: Time window in milliseconds between frame samples (default: 100ms)

        Returns:
            List of detected faces with metadata
        """
        print(f"Processing video: {video_path}")

        # Open the video file
        try:
            print(f"Attempting to open video file: {video_path}")
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")
            print("Video file opened successfully")
        except Exception as e:
            print(f"Error opening video file: {str(e)}")
            raise

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_seconds = total_frames / fps if fps > 0 else 0

        print(f"Video FPS: {fps}, Total frames: {total_frames}, Duration: {duration_seconds:.2f} seconds")

        # Calculate frame sampling based on time window
        # Convert time_window_ms to frame count
        frames_per_window = int((time_window_ms / 1000) * fps)
        frames_per_window = max(1, frames_per_window)  # Ensure minimum 1 frame

        print(f"Sampling every {frames_per_window} frames ({time_window_ms}ms time window)")

        # Track detected faces to avoid duplicates
        detected_faces = []
        current_frame = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Only process frames based on time window
            if current_frame % frames_per_window == 0:
                # Get frame timestamp
                timestamp_seconds = current_frame / fps
                timestamp = self._format_timestamp(timestamp_seconds)

                if self.model is not None:
                    # Use YOLO model if available
                    results = self.model(frame)

                    for result in results:
                        boxes = result.boxes
                        for box in boxes:
                            try:
                                # Get bounding box with error checking
                                if not hasattr(box, 'xyxy') or len(box.xyxy) == 0:
                                    print(f"Invalid box detected in frame {current_frame}")
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

                                self._save_face(face, timestamp, current_frame, confidence, detected_faces)
                            except Exception as e:
                                print(f"Error processing box in frame {current_frame}: {e}")
                                continue
                else:
                    # Fallback to OpenCV's face detector
                    # Convert to grayscale for face detection
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    # Detect faces
                    try:
                        faces = self.face_cascade.detectMultiScale(
                            gray,
                            scaleFactor=1.1,
                            minNeighbors=5,
                            minSize=(30, 30)
                        )

                        # In OpenCV's detectMultiScale, an empty result can be returned in different ways
                        # Make sure we have a valid array with a length
                        if faces is None or not hasattr(faces, '__len__') or len(faces) == 0:
                            print(f"No faces detected in frame {current_frame}")
                            faces = []
                    except Exception as e:
                        print(f"Error during face detection: {e}")
                        faces = []

                    # Check if any faces were found
                    if len(faces) > 0:
                        # Process each detected face
                        for (x, y, w, h) in faces:
                            try:
                                # Skip invalid dimensions
                                if w <= 0 or h <= 0:
                                    print(f"Invalid face dimensions ({w}x{h}) in frame {current_frame}")
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
                                    print(f"Invalid face region ({x1},{y1},{x2},{y2}) in frame {current_frame}")
                                    continue

                                # Extract face
                                face = frame[y1:y2, x1:x2]

                                # Skip if face is too small
                                if face.shape[0] < 64 or face.shape[1] < 64:
                                    continue

                                # Use fixed confidence for OpenCV detector
                                confidence = 0.9
                                self._save_face(face, timestamp, current_frame, confidence, detected_faces)
                            except Exception as e:
                                print(f"Error processing OpenCV face in frame {current_frame}: {e}")
                                continue
                    else:
                        print(f"No faces detected in frame {current_frame} using OpenCV detector")

            current_frame += 1

        cap.release()

        # Apply duplicate removal before returning faces
        if detected_faces:
            # Get unique faces
            unique_faces = self._remove_duplicates(detected_faces)

            # Group faces by similarity if advanced processing is available
            if ADVANCED_FACE_PROCESSING:
                self._group_detected_faces(unique_faces)
            else:
                print("Skipping face grouping - advanced processing not available")

            return unique_faces
        return detected_faces

    def _save_face(self, face, timestamp, current_frame, confidence, detected_faces):
        """Helper method to save a detected face and add it to the results list"""
        try:
            # Validate inputs
            if face is None or face.size == 0:
                print(f"Invalid face data in frame {current_frame}")
                return

            # Generate a unique ID for this face
            face_id = str(uuid.uuid4())

            # Resize face to 128x128 pixels while keeping original for landmark detection
            face_original = face.copy()  # Keep original for processing
            face_resized = cv2.resize(face, (128, 128), interpolation=cv2.INTER_AREA)

            # Save face image
            face_filename = f"{face_id}.jpg"
            face_path = os.path.join(self.faces_dir, face_filename)

            # Save the resized face
            cv2.imwrite(face_path, face_resized)

            # Convert to relative path for frontend
            relative_path = f"/static/faces/{face_filename}"

            # Create basic face record
            face_record = {
                "id": face_id,
                "imageUrl": relative_path,
                "timestamp": timestamp,
                "frameNumber": current_frame,
                "confidence": float(confidence) if confidence is not None else 0.5,
                "assigned": False,
                "group_id": None,
                "has_landmarks": False
            }

            # Only try to get landmarks if advanced processing is available
            if ADVANCED_FACE_PROCESSING:
                # Process the face to detect landmarks and generate embedding
                landmark_data = face_landmark_detector.process_face(face_original)

                # Add landmark data if detection was successful
                if landmark_data.get("success", False):
                    # Save the visualization image with landmarks
                    vis_filename = f"{face_id}_landmarks.jpg"
                    vis_path = os.path.join(self.faces_dir, vis_filename)
                    cv2.imwrite(vis_path, landmark_data["visualization"])

                    # Add to face record
                    face_record.update({
                        "has_landmarks": True,
                        "landmarks_str": landmark_data["landmarks_str"],
                        "embedding_str": landmark_data["embedding_str"],
                        "landmark_image": f"/static/faces/{vis_filename}"
                    })
                    print(f"Added landmarks to face {face_id}")
                else:
                    if "error" in landmark_data:
                        print(f"Failed to get landmarks for face {face_id}: {landmark_data['error']}")
            else:
                print(f"Advanced face processing not available - skipping landmarks for face {face_id}")

            detected_faces.append(face_record)
            print(f"Saved face {face_id} from frame {current_frame}")

        except Exception as e:
            print(f"Error saving face from frame {current_frame}: {e}")
            # Continue processing rather than crashing
        
        # Process continues in the main method
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS"""
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    def _remove_duplicates(self, faces: List[Dict[str, Any]], time_threshold: float = 0.5, max_faces: int = 1000) -> List[Dict[str, Any]]:
        """
        Remove duplicate faces based on timestamp proximity

        Args:
            faces: List of detected faces
            time_threshold: Time threshold in seconds
            max_faces: Maximum number of faces to return (set much higher to show more faces)

        Returns:
            List of unique faces
        """
        # Sort by confidence
        sorted_faces = sorted(faces, key=lambda x: x["confidence"], reverse=True)

        # Filter faces that are within time_threshold of each other
        unique_faces = []
        used_timestamps = []

        for face in sorted_faces:
            # Extract frame number
            frame_num = face["frameNumber"]

            # Check if this face is too close to any already selected face
            is_duplicate = False
            for used_frame in used_timestamps:
                if abs(frame_num - used_frame) < time_threshold * 30:  # Assuming 30fps
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_faces.append(face)
                used_timestamps.append(frame_num)

            # Limit to max_faces - set to a much higher number to show more faces
            if len(unique_faces) >= max_faces:
                break

        # Sort by timestamp
        unique_faces = sorted(unique_faces, key=lambda x: x["timestamp"])

        return unique_faces

    def _group_detected_faces(self, faces: List[Dict[str, Any]], similarity_threshold: float = 0.5) -> Dict[str, List[str]]:
        """
        Group detected faces based on embedding similarity

        Args:
            faces: List of detected faces with embeddings
            similarity_threshold: Threshold for similarity grouping

        Returns:
            Dictionary mapping group IDs to lists of face IDs
        """
        # Extract faces with embeddings
        faces_with_embeddings = [face for face in faces if face.get("has_landmarks", False)]

        if not faces_with_embeddings:
            print("No faces with embeddings to group")
            return {}

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
            print("No valid embeddings found")
            return {}

        # Group faces using the face group manager
        print(f"Grouping {len(embeddings)} faces with similarity threshold {similarity_threshold}")
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
        print(f"Created {len(groups)} groups from {len(embeddings)} faces")
        for group_id, face_ids in groups.items():
            print(f"Group {group_id}: {len(face_ids)} faces")

        return groups

face_detector = FaceDetector()