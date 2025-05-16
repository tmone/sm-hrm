import os
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
import logging
from ultralytics import YOLO
import threading
import queue
import time

logger = logging.getLogger(__name__)

class MultiThreadVideoTester:
    """
    Multi-threaded video testing that processes frames in parallel
    without blocking the main thread
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.model = None
        self.model_lock = threading.Lock()
        
    def load_model(self, model_path: str) -> bool:
        """Load YOLO model safely"""
        try:
            logger.info(f"[DEBUG] Attempting to load model from: {model_path}")
            with self.model_lock:
                self.model = YOLO(model_path)
                logger.info(f"[DEBUG] Model loaded successfully: {model_path}")
                return True
        except Exception as e:
            logger.error(f"[DEBUG] Error loading model: {e}")
            import traceback
            logger.error(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return False
            
    def process_frame_batch(self, frames: List[tuple]) -> List[Dict[str, Any]]:
        """Process a batch of frames"""
        results = []
        
        for frame_num, frame in frames:
            try:
                # Predict on single frame
                with self.model_lock:
                    predictions = self.model.predict(
                        frame, 
                        conf=0.25, 
                        verbose=False,
                        device='cpu'
                    )
                
                frame_results = {
                    'frame': frame_num,
                    'detections': [],
                    'error': None
                }
                
                for pred in predictions:
                    if pred.boxes is not None and len(pred.boxes) > 0:
                        for box in pred.boxes:
                            try:
                                detection = {
                                    'class_id': int(box.cls),
                                    'employee_id': pred.names[int(box.cls)],
                                    'confidence': float(box.conf),
                                    'bbox': box.xyxy[0].tolist()
                                }
                                frame_results['detections'].append(detection)
                            except Exception as e:
                                logger.warning(f"Error processing box in frame {frame_num}: {e}")
                
                results.append(frame_results)
                
            except Exception as e:
                logger.error(f"Error processing frame {frame_num}: {e}")
                results.append({
                    'frame': frame_num,
                    'detections': [],
                    'error': str(e)
                })
                
        return results
    
    def process_video_stream(self, video_path: str, progress_callback=None) -> Dict[str, Any]:
        """Process video using multi-threading with progress updates"""
        logger.info(f"[DEBUG] process_video_stream called with video_path={video_path}")
        
        if not self.model:
            logger.error("[DEBUG] Model not loaded")
            return {'success': False, 'error': 'Model not loaded'}

        try:
            # Debug video path
            logger.info(f"[DEBUG] About to open video file")
            logger.info(f"[DEBUG] video_path type: {type(video_path)}")
            logger.info(f"[DEBUG] video_path value: '{video_path}'")
            logger.info(f"[DEBUG] video_path exists: {os.path.exists(video_path) if video_path else 'N/A (None or empty)'}")
            
            if not video_path:
                logger.error("[DEBUG] video_path is None or empty!")
                return {'success': False, 'error': 'No video path provided'}
            
            # Open video
            logger.info(f"[DEBUG] Opening video: {video_path}")
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                logger.error(f"[DEBUG] Failed to open video: {video_path}")
                return {'success': False, 'error': f'Failed to open video: {video_path}'}
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            logger.info(f"[DEBUG] Processing video: {total_frames} frames at {fps} FPS")

            # Results storage
            all_detections = []
            unique_employees = set()
            frames_processed = 0
            frames_with_detections_counter = [0]  # Use list to make it mutable in nested function
            errors = []

            # Process frames in batches
            batch_size = 10
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                frame_batch = []

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    frames_processed += 1
                    frame_batch.append((frames_processed, frame))

                    # Submit batch for processing
                    if len(frame_batch) >= batch_size:
                        future = executor.submit(self.process_frame_batch, frame_batch.copy())
                        futures.append(future)
                        frame_batch = []

                        # Update progress - handle both sync and async callbacks
                        if progress_callback:
                            progress = int((frames_processed / total_frames) * 100)
                            logger.info(f"[DEBUG] Progress update: {progress}%, frames: {frames_processed}/{total_frames}")
                            
                            # If callback is async, run it in the event loop
                            import asyncio
                            import inspect
                            if inspect.iscoroutinefunction(progress_callback):
                                logger.info("[DEBUG] Using async progress callback")
                                # Get or create event loop
                                try:
                                    loop = asyncio.get_running_loop()
                                    loop.create_task(progress_callback(progress, frames_processed, total_frames))
                                except RuntimeError:
                                    # No event loop running, call synchronously
                                    logger.info("[DEBUG] No event loop, running async callback with asyncio.run")
                                    asyncio.run(progress_callback(progress, frames_processed, total_frames))
                            else:
                                logger.info("[DEBUG] Using sync progress callback")
                                progress_callback(progress, frames_processed, total_frames)
                    
                    # Limit concurrent futures to prevent memory overflow
                    if len(futures) >= self.max_workers * 2:
                        self._process_completed_futures(
                            futures[:self.max_workers],
                            all_detections,
                            unique_employees,
                            frames_with_detections_counter,
                            errors
                        )
                        futures = futures[self.max_workers:]
                
                # Process remaining frames
                if frame_batch:
                    future = executor.submit(self.process_frame_batch, frame_batch)
                    futures.append(future)
                
                # Process all remaining futures
                self._process_completed_futures(
                    futures,
                    all_detections,
                    unique_employees,
                    frames_with_detections_counter,
                    errors
                )
            
            cap.release()
            
            # Calculate summary statistics
            summary = {
                'total_detections': len(all_detections),
                'frames_with_detections': frames_with_detections_counter[0],
                'average_confidence': (
                    sum(d['confidence'] for d in all_detections) / len(all_detections)
                    if all_detections else 0
                ),
                'processing_errors': len(errors)
            }
            
            return {
                'success': True,
                'total_frames': frames_processed,
                'detections': all_detections[:1000],  # Limit to prevent memory issues
                'unique_employees': list(unique_employees),
                'summary': summary,
                'errors': errors[:10]  # First 10 errors
            }
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_completed_futures(self, futures, all_detections, unique_employees,
                                  frames_with_detections_counter, errors):
        """Process completed futures and update results"""
        for future in as_completed(futures):
            try:
                batch_results = future.result(timeout=30)
                
                for frame_result in batch_results:
                    if frame_result['error']:
                        errors.append(frame_result)
                    
                    if frame_result['detections']:
                        frames_with_detections_counter[0] += 1
                        
                        for detection in frame_result['detections']:
                            all_detections.append({
                                'frame': frame_result['frame'],
                                'employee_id': detection['employee_id'],
                                'confidence': detection['confidence'],
                                'bbox': detection['bbox']
                            })
                            unique_employees.add(detection['employee_id'])
                            
            except Exception as e:
                logger.error(f"Error processing future: {e}")
                errors.append({'error': str(e)})

    def test_video(self, model_path: str, video_path: str, progress_callback=None) -> Dict[str, Any]:
        """Main method to test a video with a YOLO model"""
        logger.info(f"[DEBUG] test_video called with model_path={model_path}, video_path={video_path}")
        
        # Load the model
        logger.info("[DEBUG] Loading model...")
        if not self.load_model(model_path):
            logger.error("[DEBUG] Failed to load model")
            return {'success': False, 'error': 'Failed to load model'}

        # Process the video
        logger.info("[DEBUG] Processing video stream...")
        return self.process_video_stream(video_path, progress_callback)

# Singleton instance
multi_thread_tester = MultiThreadVideoTester(max_workers=4)