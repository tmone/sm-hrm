import os
import json
import uuid
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
import cv2
import logging
from db.identity_groups import identity_group_manager
from db.face_landmarks import face_landmark_detector
import pickle

logger = logging.getLogger(__name__)

class LightweightAttendanceTrainer:
    """
    Lightweight attendance trainer for demo purposes
    Creates a simple face embedding database instead of full YOLO training
    """
    
    def __init__(self):
        """Initialize the lightweight trainer"""
        self.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
        self.models_dir = os.path.join(self.base_dir, "attendance_models")
        self.faces_dir = os.path.join(self.base_dir, "faces")
        
        os.makedirs(self.models_dir, exist_ok=True)
        
        # In-memory job tracking
        self.jobs = {}
        
    def start_training(self, group_ids: List[str], model_name: str = "lightweight") -> str:
        """Create a new training job for employee detection"""
        job_id = str(uuid.uuid4())
        
        # Create job record
        self.jobs[job_id] = {
            'id': job_id,
            'status': 'queued',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'group_ids': group_ids,
            'message': 'Training job queued',
            'error': None,
            'model_name': model_name
        }
        
        # Start training in background thread
        thread = threading.Thread(target=self._train_model, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        return job_id
        
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a training job"""
        return self.jobs.get(job_id)
        
    def _train_model(self, job_id: str):
        """Train lightweight face recognition model"""
        try:
            job = self.jobs.get(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return
                
            group_ids = job.get('group_ids', [])
            logger.info(f"Starting lightweight training with {len(group_ids)} employee groups")
            
            # Update job status
            job['status'] = 'processing'
            job['progress'] = 10
            job['message'] = 'Processing employee faces'
            job['updated_at'] = datetime.now().isoformat()
            
            # Get all identity groups
            all_groups = identity_group_manager.identities.get('groups', {})
            
            # Create embedding database
            employee_database = {}
            faces_processed = 0
            successful_employees = 0
            
            for i, group_id in enumerate(group_ids):
                progress = 10 + (80 * i // len(group_ids))
                job['progress'] = progress
                job['message'] = f'Processing employee {group_id} ({i+1}/{len(group_ids)})'
                job['updated_at'] = datetime.now().isoformat()

                group_data = all_groups.get(group_id)
                if not group_data:
                    logger.warning(f"Group {group_id} not found")
                    continue

                face_ids = group_data.get('face_ids', [])
                employee_embeddings = []
                logger.info(f"Processing group {group_id} with {len(face_ids)} faces")

                # Process all faces (or limit for demo)
                faces_to_process = face_ids[:10]  # Increased limit to 10 faces
                logger.info(f"Processing {len(faces_to_process)} faces for employee {group_id}")

                for idx, face_id in enumerate(faces_to_process):
                    face_path = os.path.join(self.faces_dir, f"{face_id}.jpg")
                    logger.debug(f"Processing face {idx+1}/{len(faces_to_process)}: {face_path}")

                    if os.path.exists(face_path):
                        try:
                            # Load face image
                            img = cv2.imread(face_path)
                            if img is not None:
                                logger.debug(f"Loaded image {face_id}, shape: {img.shape}")
                                # Get embedding using dlib
                                embedding = face_landmark_detector.get_face_embedding(img)
                                if embedding is not None and len(embedding) == 128:
                                    employee_embeddings.append(embedding)
                                    faces_processed += 1
                                    logger.debug(f"Successfully extracted embedding for face {face_id}")
                                else:
                                    logger.warning(f"Failed to extract embedding for face {face_id}")
                            else:
                                logger.error(f"Failed to load image {face_id}")
                        except Exception as e:
                            logger.error(f"Error processing face {face_id}: {e}")
                    else:
                        logger.warning(f"Face image not found: {face_path}")

                if employee_embeddings:
                    # Store average embedding for this employee
                    avg_embedding = np.mean(employee_embeddings, axis=0)
                    employee_database[group_id] = {
                        'embedding': avg_embedding.tolist(),
                        'face_count': len(employee_embeddings),
                        'name': group_data.get('name', group_id)
                    }
                    successful_employees += 1
                    logger.info(f"Employee {group_id}: Successfully processed {len(employee_embeddings)} faces out of {len(face_ids)} total")
                else:
                    logger.warning(f"Employee {group_id}: No embeddings extracted from {len(face_ids)} faces")
            
            # Update status
            job['progress'] = 90
            job['message'] = 'Saving model'
            job['updated_at'] = datetime.now().isoformat()
            
            # Save the employee database
            model_filename = f"attendance_model_{job_id}.pkl"
            model_path = os.path.join(self.models_dir, model_filename)
            
            with open(model_path, 'wb') as f:
                pickle.dump({
                    'employee_database': employee_database,
                    'created_at': datetime.now().isoformat(),
                    'job_id': job_id,
                    'summary': {
                        'total_employees': len(group_ids),
                        'successful_employees': successful_employees,
                        'faces_processed': faces_processed
                    }
                }, f)
            
            # Save as latest model
            latest_model_path = os.path.join(self.models_dir, 'latest_attendance_model.pkl')
            with open(latest_model_path, 'wb') as f:
                pickle.dump({
                    'employee_database': employee_database,
                    'created_at': datetime.now().isoformat(),
                    'job_id': job_id
                }, f)
            
            # Update job status to completed
            job['status'] = 'completed'
            job['progress'] = 100
            job['message'] = f'Training completed. Model trained for {successful_employees} employees using {faces_processed} face images.'
            job['model_path'] = model_path
            job['updated_at'] = datetime.now().isoformat()
            job['summary'] = {
                'employees_requested': len(group_ids),
                'employees_processed': successful_employees,
                'faces_processed': faces_processed,
                'average_faces_per_employee': faces_processed / successful_employees if successful_employees > 0 else 0
            }

            logger.info(f"=== Training Summary ===")
            logger.info(f"Job ID: {job_id}")
            logger.info(f"Employees requested: {len(group_ids)}")
            logger.info(f"Employees processed: {successful_employees}")
            logger.info(f"Total faces processed: {faces_processed}")
            logger.info(f"Average faces per employee: {faces_processed / successful_employees if successful_employees > 0 else 0:.2f}")
            logger.info(f"Model saved to: {model_path}")
            logger.info(f"======================")

            logger.info(f"Lightweight training job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error training model for job {job_id}: {str(e)}")
            job['status'] = 'failed'
            job['progress'] = 0
            job['message'] = 'Training failed'
            job['error'] = str(e)
            job['updated_at'] = datetime.now().isoformat()
    
    def test_model(self, model_path: str, video_path: str) -> Dict[str, Any]:
        """Test the model on a video (simplified demo version)"""
        try:
            # Load the model
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            employee_database = model_data['employee_database']
            
            # For demo, just return mock detection results
            # In production, this would process the video frame by frame
            mock_detections = []
            
            # Simulate some detections
            for employee_id in list(employee_database.keys())[:3]:  # Mock detect first 3 employees
                mock_detections.append({
                    'employee_id': employee_id,
                    'confidence': 0.85 + np.random.rand() * 0.1,
                    'timestamp': datetime.now().isoformat(),
                    'event': 'entrance'
                })
            
            return {
                'success': True,
                'detections': mock_detections,
                'total_frames': 100,  # Mock frame count
                'unique_employees': list(set(d['employee_id'] for d in mock_detections)),
                'message': 'Demo detection completed'
            }
            
        except Exception as e:
            logger.error(f"Error testing model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Create singleton instance
lightweight_attendance_trainer = LightweightAttendanceTrainer()