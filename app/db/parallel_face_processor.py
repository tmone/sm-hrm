import os
import logging
import concurrent.futures
import threading
import math
from typing import Dict, List, Any, Optional, Callable

# Import all of our processor modules
from db.background_processor import BackgroundProcessor
from db.video_processor import VideoProcessor
from db.face_processor import FaceProcessor
from db.landmark_processor import LandmarkProcessor
from db.grouping_processor import GroupingProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParallelFaceProcessor:
    """
    Enhanced parallel processor with multi-threading capabilities.
    
    This class:
    1. Initializes all processor stages
    2. Registers processors with the background processor
    3. Provides a simple API for starting and monitoring processing
    4. Supports splitting large videos for multi-threaded processing
    """
    
    def __init__(self, max_workers: int = 8):
        """Initialize the parallel face processor with more workers for better parallelism"""
        # Set up directory paths
        self.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        self.static_dir = os.path.join(self.base_dir, "static")
        self.upload_dir = os.path.join(self.static_dir, "uploads")
        self.frame_dir = os.path.join(self.static_dir, "frames")
        self.faces_dir = os.path.join(self.static_dir, "faces")
        self.models_dir = os.path.join(self.base_dir, "models")
        
        # Create directories if they don't exist
        for directory in [self.static_dir, self.upload_dir, self.frame_dir, self.faces_dir, self.models_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Get the background processor instance
        # Use the existing singleton instance that was created in background_processor.py
        from db.background_processor import background_processor
        self.background_processor = background_processor
        
        # Initialize processor components
        self.video_processor = VideoProcessor(self.upload_dir, self.frame_dir)
        self.face_processor = FaceProcessor(self.faces_dir, self.models_dir)
        self.landmark_processor = LandmarkProcessor(self.faces_dir)
        self.grouping_processor = GroupingProcessor()
        
        # Register processors with the background processor
        self._register_processors()
        
        # Set up multi-threading parameters
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        
        logger.info(f"Parallel face processor initialized with {max_workers} workers")
    
    def _register_processors(self):
        """Register all processor functions with the background processor"""
        # Video upload validation
        self.background_processor.register_processor('upload', self.video_processor.validate_video)
        
        # Frame extraction - use our multi-threaded version
        self.background_processor.register_processor('extraction', self.extract_frames_parallel)
        
        # Face detection - use our multi-threaded version
        self.background_processor.register_processor('detection', self.detect_faces_parallel)
        
        # Landmark detection
        self.background_processor.register_processor('landmarks', self.landmark_processor.process_landmarks)
        
        # Face grouping
        self.background_processor.register_processor('grouping', self.grouping_processor.group_faces)
        
        logger.info("All processors registered with background processor")
    
    def extract_frames_parallel(self, data: Dict[str, Any], progress_callback: Callable) -> Dict[str, Any]:
        """
        Multi-threaded frame extraction that splits the video into chunks
        
        Args:
            data: Job data containing video_path
            progress_callback: Callback function to report progress
            
        Returns:
            Dict with extraction results
        """
        video_path = data.get('video_path')
        process_all_frames = data.get('process_all_frames', True)
        
        if not video_path or not os.path.exists(video_path):
            raise ValueError(f"Invalid video path: {video_path}")
        
        progress_callback(10, "Setting up parallel frame extraction")
        
        # First, get video info
        import cv2
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        # Determine how to split the video for multi-threading
        # For very large videos (>10000 frames), use more workers
        chunk_size = max(100, frame_count // self.max_workers)
        num_chunks = min(self.max_workers, math.ceil(frame_count / chunk_size))
        
        logger.info(f"Splitting video with {frame_count} frames into {num_chunks} chunks")
        
        # Create the results directory
        md5_hash = data.get('md5_hash', os.path.basename(video_path).split('.')[0])
        video_id = md5_hash[:10] if md5_hash else os.path.basename(video_path).split('.')[0]
        video_frame_dir = os.path.join(self.frame_dir, video_id)
        os.makedirs(video_frame_dir, exist_ok=True)
        
        # Define chunk parameters
        chunks = []
        for i in range(num_chunks):
            start_frame = i * chunk_size
            end_frame = min((i + 1) * chunk_size, frame_count)
            chunks.append((start_frame, end_frame))
        
        progress_callback(20, f"Extracting frames in {num_chunks} parallel chunks")
        
        # Process chunks in parallel
        extracted_frames = []
        progress_lock = threading.Lock()
        current_progress = 20
        
        def extract_chunk(chunk_idx, start_frame, end_frame):
            nonlocal current_progress
            chunk_frames = []
            
            # Open video and seek to start frame
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            frame_sampling = 1 if process_all_frames else max(1, int((100 / 1000) * fps))
            current_frame = start_frame
            frame_number = start_frame
            
            while current_frame < end_frame:
                # Read the next frame
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process based on sampling strategy
                if current_frame % frame_sampling == 0:
                    # Calculate timestamp in milliseconds
                    timestamp_ms = (current_frame / fps) * 1000
                    
                    # Save the frame
                    frame_filename = f"frame_{frame_number:06d}_{int(timestamp_ms):08d}.jpg"
                    frame_path = os.path.join(video_frame_dir, frame_filename)
                    cv2.imwrite(frame_path, frame)
                    
                    # Add to our list of extracted frames
                    chunk_frames.append({
                        'frame_number': frame_number,
                        'timestamp_ms': timestamp_ms,
                        'frame_path': frame_path,
                        'original_frame': current_frame
                    })
                    
                    frame_number += 1
                
                current_frame += 1
                
                # Update progress periodically
                if current_frame % 20 == 0:
                    with progress_lock:
                        # Calculate overall progress
                        chunk_progress = (current_frame - start_frame) / (end_frame - start_frame)
                        chunk_contribution = chunk_progress * 70 / num_chunks
                        new_progress = min(90, 20 + (chunk_idx / num_chunks) * 70 + chunk_contribution)
                        
                        if new_progress > current_progress:
                            current_progress = new_progress
                            progress_callback(current_progress, 
                                            f"Extracting frames from chunk {chunk_idx+1}/{num_chunks}")
            
            cap.release()
            return chunk_frames
        
        # Submit all chunks to the thread pool
        future_to_chunk = {
            self.executor.submit(extract_chunk, i, start, end): i
            for i, (start, end) in enumerate(chunks)
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk_idx = future_to_chunk[future]
            try:
                chunk_frames = future.result()
                extracted_frames.extend(chunk_frames)
                logger.info(f"Chunk {chunk_idx} completed with {len(chunk_frames)} frames")
            except Exception as e:
                logger.error(f"Error in chunk {chunk_idx}: {e}")
        
        # Sort frames by frame number
        extracted_frames.sort(key=lambda x: x['frame_number'])
        
        progress_callback(95, f"Completed frame extraction, found {len(extracted_frames)} frames")
        
        # Prepare result
        result = {
            'video_id': video_id,
            'frame_count': len(extracted_frames),
            'frames_directory': video_frame_dir,
            'next_stage': 'detection',
            'next_data': {
                'video_id': video_id,
                'frame_directory': video_frame_dir,
                'frames': extracted_frames,
                'fps': fps,
                'enable_tracking': process_all_frames
            }
        }
        
        return result
    
    def detect_faces_parallel(self, data: Dict[str, Any], progress_callback: Callable) -> Dict[str, Any]:
        """
        Multi-threaded face detection that splits frames into chunks
        
        Args:
            data: Job data with frames to process
            progress_callback: Callback function to report progress
            
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
        
        # Even with tracking enabled, we'll split into sequential chunks for parallel processing
        # We accept the possibility of losing track continuity at chunk boundaries
        # This is a performance vs. accuracy tradeoff requested by the user
        
        # Process frames in parallel in sequential chunks
        progress_callback(10, f"Setting up parallel face detection for {len(frames)} frames")
        
        # Split frames into sequential chunks for parallel processing
        # For tracking, use larger chunks to minimize boundary tracking issues
        chunk_size = 100  # Process 100 frames per chunk to balance tracking and parallelism
        if enable_tracking:
            # Use larger chunks when tracking is enabled (fewer chunks = fewer boundary issues)
            chunk_size = max(100, len(frames) // self.max_workers)
            logger.info(f"Using larger chunks ({chunk_size} frames) for parallel processing with tracking")
        
        num_chunks = max(1, len(frames) // chunk_size)
        # Limit to max workers
        num_chunks = min(self.max_workers, num_chunks)
        chunks = []
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min(start_idx + chunk_size, len(frames)) if i < num_chunks - 1 else len(frames)
            chunks.append((start_idx, end_idx))
            
        logger.info(f"Split {len(frames)} frames into {len(chunks)} sequential chunks for parallel processing")
        
        # Process chunks in parallel
        all_detected_faces = []
        progress_lock = threading.Lock()
        current_progress = 10
        
        def process_frames_chunk(chunk_idx, start_idx, end_idx):
            nonlocal current_progress
            chunk_frames = frames[start_idx:end_idx]
            chunk_faces = []
            
            # For tracking, we need to use the face_detector with tracking enabled
            if enable_tracking:
                # Import here to avoid circular imports
                from db.face_detection import face_detector
                
                # Prepare data for this chunk
                chunk_data = {
                    'frames': chunk_frames,
                    'video_id': video_id,
                    'frame_directory': frame_directory,
                    'enable_tracking': True,
                    'fps': fps
                }
                
                # Define a local progress callback for this chunk
                def chunk_progress_callback(percent, message):
                    nonlocal current_progress
                    with progress_lock:
                        # Scale the progress to this chunk's portion of the overall progress
                        chunk_contribution = percent * 80 / (100 * num_chunks)
                        new_progress = min(90, 10 + (chunk_idx / num_chunks) * 80 + chunk_contribution)
                        
                        if new_progress > current_progress:
                            current_progress = new_progress
                            progress_callback(current_progress, 
                                            f"Chunk {chunk_idx+1}/{num_chunks}: {message}")
                
                # Process this chunk with tracking
                try:
                    chunk_result = face_detector.process_video(chunk_data, chunk_progress_callback)
                    chunk_faces = chunk_result.get('faces', [])
                    
                    # Add chunk index to each face for debugging
                    for face in chunk_faces:
                        face['chunk_idx'] = chunk_idx
                        
                    logger.info(f"Chunk {chunk_idx}: Processed {len(chunk_frames)} frames, found {len(chunk_faces)} faces")
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_idx} with tracking: {e}")
            else:
                # Without tracking, use the FaceProcessor directly for each frame
                for i, frame_data in enumerate(chunk_frames):
                    frame_path = frame_data.get('frame_path')
                    if not frame_path or not os.path.exists(frame_path):
                        continue
                    
                    try:
                        # Read the frame
                        import cv2
                        frame = cv2.imread(frame_path)
                        if frame is None:
                            continue
                        
                        # Detect faces using available method
                        if self.face_processor.model is not None:
                            # Use YOLO model
                            faces = self.face_processor._detect_faces_yolo(frame, frame_data)
                        elif self.face_processor.face_cascade is not None:
                            # Fallback to OpenCV
                            faces = self.face_processor._detect_faces_opencv(frame, frame_data)
                        else:
                            faces = []
                        
                        # Save each detected face
                        for face_data in faces:
                            try:
                                # Extract face from frame using bounding box
                                if 'box' in face_data:
                                    x1, y1, x2, y2 = map(int, face_data['box'])
                                    face = frame[y1:y2, x1:x2]
                                    
                                    # Skip if face is too small
                                    if face.size == 0 or face.shape[0] < 64 or face.shape[1] < 64:
                                        continue
                                    
                                    # Save face
                                    face_record = self.face_processor._save_face(
                                        face,
                                        frame_data.get('timestamp_ms', 0),
                                        frame_data.get('frame_number', 0),
                                        face_data.get('confidence', 0.5)
                                    )
                                    
                                    if face_record:
                                        # Add chunk index for debugging
                                        face_record['chunk_idx'] = chunk_idx
                                        chunk_faces.append(face_record)
                            except Exception as e:
                                logger.error(f"Error processing face in chunk {chunk_idx}: {e}")
                    except Exception as e:
                        logger.error(f"Error processing frame in chunk {chunk_idx}: {e}")
                    
                    # Update progress periodically
                    if i % 10 == 0:
                        with progress_lock:
                            chunk_progress = i / len(chunk_frames)
                            chunk_contribution = chunk_progress * 80 / num_chunks
                            new_progress = min(90, 10 + (chunk_idx / num_chunks) * 80 + chunk_contribution)
                            
                            if new_progress > current_progress:
                                current_progress = new_progress
                                progress_callback(current_progress, 
                                                f"Detecting faces in chunk {chunk_idx+1}/{num_chunks}")
            
            return chunk_faces
        
        # Submit all chunks to the thread pool
        future_to_chunk = {
            self.executor.submit(process_frames_chunk, i, start, end): i
            for i, (start, end) in enumerate(chunks)
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk_idx = future_to_chunk[future]
            try:
                chunk_faces = future.result()
                all_detected_faces.extend(chunk_faces)
                logger.info(f"Chunk {chunk_idx} completed with {len(chunk_faces)} faces")
            except Exception as e:
                logger.error(f"Error in chunk {chunk_idx}: {e}")
        
        progress_callback(95, f"Completed face detection, found {len(all_detected_faces)} faces")
        
        # Remove duplicates
        unique_faces = self.face_processor._remove_duplicates(all_detected_faces)
        logger.info(f"Found {len(unique_faces)} unique faces out of {len(all_detected_faces)} total detections")
        
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
    
    def start_processing(self, video_path: str) -> str:
        """
        Start processing a video file through the parallel pipeline
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Job ID for tracking processing
        """
        # Make sure the background processor workers are running
        self.background_processor.start_workers()
        
        # Submit the initial job to the upload stage
        job_id = self.background_processor.enqueue_job('upload', {
            'video_path': video_path
        })
        
        logger.info(f"Started processing video {video_path} with job ID {job_id}")
        return job_id
    
    def get_processing_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a processing job
        
        Args:
            job_id: Job ID to check
            
        Returns:
            Job status information
        """
        return self.background_processor.get_job_status(job_id)

# Create singleton instance
parallel_face_processor = ParallelFaceProcessor()