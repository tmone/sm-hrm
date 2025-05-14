import threading
import queue
import time
import traceback
import os
import uuid
import logging
from typing import Dict, Any, Callable, List, Optional, Tuple
from datetime import datetime

# Import our modules
from db.face_detection import face_detector
from db.uploads import upload_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundProcessor:
    """
    Handles background processing tasks for the application

    Runs tasks in separate threads to avoid blocking the main application
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = BackgroundProcessor()
        return cls._instance

    def __init__(self, max_workers=2):
        self.task_queue = queue.Queue()
        self.workers = []  # For original workers
        self.stage_workers = {}  # For parallel processing workers
        self.max_workers = max_workers
        self.running = False
        self.processing_results = {}

        # Create directory for storing processing results
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", "static", "processing")
        os.makedirs(self.results_dir, exist_ok=True)

        # Added for parallel processing system
        # Stage queues - each stage has its own job queue
        self.queues = {
            'upload': queue.Queue(),         # Video upload validation stage
            'extraction': queue.Queue(),     # Frame extraction from videos
            'detection': queue.Queue(),      # Face detection in frames
            'landmarks': queue.Queue(),      # Facial landmark extraction
            'grouping': queue.Queue(),       # Face grouping based on similarity
        }

        # Processor functions for each stage
        self.processors = {}

        # Shutdown flag for parallel workers
        self.shutdown_flag = False

        # Processing locks to prevent race conditions
        self.locks = {stage: threading.Lock() for stage in self.queues.keys()}

        # Job registry - tracks all jobs across all stages
        self.jobs = {}

        # Job progress tracking
        self.progress = {}
    
    def start(self):
        """Start the background processing threads"""
        if self.running:
            return
            
        self.running = True
        
        # Start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_thread, 
                                     args=(f"worker-{i}",), 
                                     daemon=True)
            worker.start()
            self.workers.append(worker)
            
        print(f"Started {self.max_workers} background worker threads")
    
    def stop(self):
        """Stop the background processing threads"""
        self.running = False
        
        # Wait for all workers to finish
        for worker in self.workers:
            worker.join(timeout=1.0)
            
        self.workers = []
        print("Stopped all background worker threads")
    
    def add_video_processing_task(self, video_id: str) -> str:
        """
        Schedule a video for face/human extraction processing
        
        Args:
            video_id: ID of the uploaded video to process
            
        Returns:
            ID of the processing task
        """
        # Get video details
        video = upload_manager.get_video(video_id)
        if not video:
            raise ValueError(f"Video with ID {video_id} not found")
            
        # Create a task ID and update video status
        task_id = f"task_{video_id}"
        upload_manager.update_video_status(video_id, "processing", {
            "task_id": task_id,
            "processing_started": datetime.now().isoformat()
        })
        
        # Add task to queue
        self.task_queue.put({
            "type": "process_video",
            "task_id": task_id,
            "video_id": video_id,
            "video_path": video["file_path"],
            "created_at": datetime.now().isoformat()
        })
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a background task"""
        if task_id in self.processing_results:
            return self.processing_results[task_id]
        
        # Return a response with all required fields to satisfy FastAPI validation
        # Extract video_id from task_id if possible (task_id often has format task_video_id)
        video_id = ""
        if task_id.startswith("task_"):
            video_id = task_id[5:]  # Remove "task_" prefix
            
        return {
            "status": "unknown", 
            "task_id": task_id,
            "video_id": video_id,  # Required field for VideoProcessingResponse
            "progress": 0.0,      # Required field for VideoProcessingResponse
        }
    
    def recover_video_processing(self, video_id: str, task_id: str = None) -> bool:
        """
        Attempt to recover a video that failed processing but was mostly complete
        
        Args:
            video_id: ID of the video to recover
            task_id: Optional task ID (will be generated from video_id if not provided)
            
        Returns:
            True if recovery was successful, False otherwise
        """
        print(f"Attempting to recover video processing for video {video_id}")
        
        # Generate task ID if not provided
        if not task_id:
            task_id = f"task_{video_id}"
        
        try:
            # Get video details
            video = upload_manager.get_video(video_id)
            if not video:
                print(f"Video {video_id} not found, cannot recover")
                return False
                
            # Call face detector's recover function
            detected_faces = face_detector.recover_processing(video_id)
            
            if not detected_faces:
                print(f"No faces could be recovered for video {video_id}")
                return False
                
            # Update the video record with the recovered faces
            upload_manager.update_video_status(video_id, "completed", {
                "detected_faces": len(detected_faces),
                "processing_completed": datetime.now().isoformat(),
                "processing_recovered": True,
                "faces": [
                    {
                        "id": face["id"],
                        "imageUrl": face["imageUrl"],
                        "timestamp": face["timestamp"],
                        "confidence": face.get("confidence", 1.0),
                        "frameNumber": face.get("frameNumber", 0),
                        "labeled": False
                    } 
                    for face in detected_faces
                ]
            })
            
            # Update task status
            self.processing_results[task_id] = {
                "status": "completed",
                "progress": 100,
                "task_id": task_id,
                "video_id": video_id,
                "face_count": len(detected_faces),
                "recovered": True,
                "completed_at": datetime.now().isoformat(),
                "error": None
            }
            
            print(f"Successfully recovered video {video_id} with {len(detected_faces)} faces")
            return True
            
        except Exception as e:
            print(f"Error recovering video {video_id}: {str(e)}")
            traceback.print_exc()
            return False
    
    def _worker_thread(self, worker_name: str):
        """Worker thread function that processes tasks from the queue"""
        print(f"Background worker {worker_name} started")
        
        while self.running:
            try:
                # Try to get a task with a timeout to allow for graceful shutdown
                try:
                    task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process the task based on type
                if task["type"] == "process_video":
                    self._process_video_task(task)
                else:
                    print(f"Unknown task type: {task['type']}")
                
                # Mark task as done
                self.task_queue.task_done()
                
            except Exception as e:
                print(f"Error in worker {worker_name}: {str(e)}")
                traceback.print_exc()
        
        print(f"Background worker {worker_name} stopped")
    
    def _process_video_task(self, task: Dict[str, Any]):
        """Process a video for face/human extraction"""
        video_id = task["video_id"]
        video_path = task["video_path"]
        task_id = task["task_id"]
        
        print(f"Processing video {video_id} in background task {task_id}")
        
        # Update task status
        self.processing_results[task_id] = {
            "status": "processing",
            "progress": 0,
            "task_id": task_id,
            "video_id": video_id,
            "started_at": datetime.now().isoformat()
        }
        
        try:
            # Process the video with our face detector using a time-based window
            # The face detector will save images to its own directory
            detected_faces = face_detector.process_video_file(video_path, time_window_ms=100)
            
            # Update the video record with the results
            upload_manager.update_video_status(video_id, "completed", {
                "detected_faces": len(detected_faces),
                "processing_completed": datetime.now().isoformat(),
                "faces": [
                    {
                        "id": face["id"],
                        "imageUrl": face["imageUrl"],
                        "timestamp": face["timestamp"],
                        "confidence": face.get("confidence", 1.0),
                        "frameNumber": face.get("frameNumber", 0),
                        "labeled": False
                    } 
                    for face in detected_faces
                ]
            })
            
            # Update task status
            self.processing_results[task_id] = {
                "status": "completed",
                "progress": 100,
                "task_id": task_id,
                "video_id": video_id,
                "face_count": len(detected_faces),
                "completed_at": datetime.now().isoformat(),
                "error": None
            }
            
            print(f"Completed processing video {video_id}, found {len(detected_faces)} faces")
            
        except Exception as e:
            # Update task status with error
            error_message = str(e)
            traceback.print_exc()
            
            # Update video status
            upload_manager.update_video_status(video_id, "failed", {
                "error": error_message,
                "processing_failed": datetime.now().isoformat()
            })
            
            # Update task status
            self.processing_results[task_id] = {
                "status": "failed",
                "progress": 0,
                "task_id": task_id,
                "video_id": video_id,
                "error": error_message,
                "failed_at": datetime.now().isoformat()
            }
            
            print(f"Failed to process video {video_id}: {error_message}")

    # Methods for parallel processing pipeline
    def register_processor(self, stage: str, processor_func: Callable):
        """Register a processing function for a stage"""
        self.processors[stage] = processor_func
        logger.info(f"Registered processor for stage: {stage}")

    def start_workers(self):
        """Start worker threads for all registered processors"""
        for stage, processor in self.processors.items():
            if stage not in self.stage_workers or not self.stage_workers[stage].is_alive():
                thread = threading.Thread(
                    target=self._parallel_worker_thread,
                    args=(stage,),
                    daemon=True
                )
                thread.start()
                self.stage_workers[stage] = thread
                logger.info(f"Started worker thread for stage: {stage}")

    def stop_workers(self):
        """Signal workers to shutdown and wait for them to finish"""
        self.shutdown_flag = True
        logger.info("Signaling all workers to stop")

        # Wait for workers to finish (with timeout)
        for stage, thread in self.stage_workers.items():
            if thread.is_alive():
                thread.join(timeout=5.0)
                logger.info(f"Worker for stage {stage} stopped")

    def enqueue_job(self, stage: str, data: Dict[str, Any], source_job_id: Optional[str] = None) -> str:
        """Add a new job to a stage queue"""
        job_id = str(uuid.uuid4())

        # Create job record
        self.jobs[job_id] = {
            'id': job_id,
            'stage': stage,
            'status': "pending",
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'source_job_id': source_job_id,
            'result': None,
            'error': None
        }

        # Create progress tracker
        self.progress[job_id] = {
            'percent': 0,
            'message': f"Job queued for {stage}"
        }

        # Create message and add to queue
        message = {
            "job_id": job_id,
            "stage": stage,
            "data": data,
            "source_job_id": source_job_id,
            "created_at": datetime.now().isoformat()
        }
        self.queues[stage].put(message)

        logger.info(f"Enqueued job {job_id} for stage {stage}")
        return job_id

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the current status of a job"""
        if job_id not in self.jobs:
            return {'status': 'unknown', 'error': 'Job not found'}

        job = self.jobs[job_id].copy()  # Return a copy to prevent modification

        # Add progress information
        if job_id in self.progress:
            job['progress'] = self.progress[job_id]

        return job

    def update_job_progress(self, job_id: str, percent: float, message: str):
        """Update the progress of a job"""
        if job_id in self.progress:
            self.progress[job_id] = {
                'percent': percent,
                'message': message
            }
            logger.debug(f"Updated progress for job {job_id}: {percent}% - {message}")

    def _parallel_worker_thread(self, stage: str):
        """Worker thread function that processes tasks from the queue for a specific stage"""
        logger.info(f"Parallel worker thread for stage {stage} started")

        while not self.shutdown_flag:
            try:
                # Get job from queue with timeout to check shutdown flag periodically
                try:
                    message = self.queues[stage].get(timeout=1.0)
                except queue.Empty:
                    continue

                job_id = message["job_id"]

                # Update job status
                with self.locks[stage]:
                    if job_id in self.jobs:
                        self.jobs[job_id]['status'] = "processing"
                        self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
                        self.update_job_progress(job_id, 10, f"Processing started in {stage}")

                # Process the job
                try:
                    logger.info(f"Processing job {job_id} in stage {stage}")

                    # Call the registered processor function
                    if stage in self.processors:
                        result = self.processors[stage](message["data"],
                                                      lambda p, m: self.update_job_progress(job_id, p, m))

                        # Update job with result
                        with self.locks[stage]:
                            if job_id in self.jobs:
                                self.jobs[job_id]['status'] = "completed"
                                self.jobs[job_id]['result'] = result
                                self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
                                self.update_job_progress(job_id, 100, f"Processing completed in {stage}")

                        # If the processor returned next stage data, enqueue it
                        if isinstance(result, dict) and 'next_stage' in result and 'next_data' in result:
                            next_stage = result['next_stage']
                            next_data = result['next_data']

                            if next_stage in self.queues:
                                self.enqueue_job(next_stage, next_data, job_id)
                                logger.info(f"Job {job_id} in {stage} triggered next job in {next_stage}")
                    else:
                        logger.error(f"No processor registered for stage {stage}")
                        with self.locks[stage]:
                            if job_id in self.jobs:
                                self.jobs[job_id]['status'] = "failed"
                                self.jobs[job_id]['error'] = f"No processor registered for stage {stage}"
                                self.jobs[job_id]['updated_at'] = datetime.now().isoformat()

                except Exception as e:
                    logger.exception(f"Error processing job {job_id} in stage {stage}: {str(e)}")
                    # Update job with error
                    with self.locks[stage]:
                        if job_id in self.jobs:
                            self.jobs[job_id]['status'] = "failed"
                            self.jobs[job_id]['error'] = str(e)
                            self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
                            self.update_job_progress(job_id, 100, f"Failed in {stage}: {str(e)}")

                finally:
                    # Mark task as done in queue
                    self.queues[stage].task_done()

            except Exception as e:
                logger.exception(f"Unexpected error in worker thread for {stage}: {str(e)}")
                # Sleep briefly to avoid CPU spinning on repeated errors
                time.sleep(0.1)

        logger.info(f"Worker thread for stage {stage} shutting down")

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Remove old completed jobs from memory to prevent memory leaks"""
        now = datetime.now()
        jobs_to_remove = []

        for job_id, job in self.jobs.items():
            if job['status'] in ["completed", "failed"]:
                updated_at = datetime.fromisoformat(job['updated_at'])
                age = now - updated_at
                if age.total_seconds() > max_age_hours * 3600:
                    jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            if job_id in self.progress:
                del self.progress[job_id]

        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")

# Create singleton instance
background_processor = BackgroundProcessor()