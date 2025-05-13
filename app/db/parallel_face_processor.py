import os
import logging
from typing import Dict, Any, Optional

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
    Main class that orchestrates the parallel face processing pipeline.
    
    This class:
    1. Initializes all processor stages
    2. Registers processors with the background processor
    3. Provides a simple API for starting and monitoring processing
    """
    
    def __init__(self):
        """Initialize the parallel face processor"""
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
        
        logger.info("Parallel face processor initialized")
    
    def _register_processors(self):
        """Register all processor functions with the background processor"""
        # Video upload validation
        self.background_processor.register_processor('upload', self.video_processor.validate_video)
        
        # Frame extraction
        self.background_processor.register_processor('extraction', self.video_processor.extract_frames)
        
        # Face detection
        self.background_processor.register_processor('detection', self.face_processor.detect_faces)
        
        # Landmark detection
        self.background_processor.register_processor('landmarks', self.landmark_processor.process_landmarks)
        
        # Face grouping
        self.background_processor.register_processor('grouping', self.grouping_processor.group_faces)
        
        logger.info("All processors registered with background processor")
    
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