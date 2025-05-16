import os
import json
import time
import uuid
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.svm import SVC
import pickle
import logging

logger = logging.getLogger(__name__)

class TrainingManager:
    """
    Manages model training for face recognition
    """
    
    def __init__(self):
        """Initialize the training manager"""
        self.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
        self.models_dir = os.path.join(self.base_dir, "models")
        self.jobs_dir = os.path.join(self.base_dir, "training_jobs")
        
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.jobs_dir, exist_ok=True)
        
        # Active training jobs
        self.active_jobs = {}
        
    def create_training_job(self, identity_group_ids: List[str]) -> str:
        """Create a new training job"""
        job_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        job_data = {
            "id": job_id,
            "status": "queued",
            "progress": 0,
            "message": "Training job queued",
            "identity_group_ids": identity_group_ids,
            "created_at": timestamp,
            "updated_at": timestamp,
            "model_path": None,
            "error": None
        }
        
        # Save job data
        job_file = os.path.join(self.jobs_dir, f"{job_id}.json")
        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2)
            
        # Add to active jobs
        self.active_jobs[job_id] = job_data
        
        # Start training in background thread
        thread = threading.Thread(target=self._train_model, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        return job_id
        
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a training job"""
        # Check active jobs first
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
            
        # Check saved jobs
        job_file = os.path.join(self.jobs_dir, f"{job_id}.json")
        if os.path.exists(job_file):
            with open(job_file, 'r') as f:
                return json.load(f)
                
        return None
        
    def _update_job_status(self, job_id: str, status: str, progress: int, message: str, error: str = None):
        """Update job status"""
        job_data = self.active_jobs.get(job_id, {})
        job_data["status"] = status
        job_data["progress"] = progress
        job_data["message"] = message
        job_data["updated_at"] = datetime.now().isoformat()
        
        if error:
            job_data["error"] = error
            
        # Update active jobs
        self.active_jobs[job_id] = job_data
        
        # Save to file
        job_file = os.path.join(self.jobs_dir, f"{job_id}.json")
        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2)
            
    def _train_model(self, job_id: str):
        """Train the face recognition model"""
        try:
            from db.identity_groups import identity_group_manager
            from db.face_landmarks import face_landmark_detector
            
            job_data = self.active_jobs[job_id]
            identity_group_ids = job_data["identity_group_ids"]
            
            self._update_job_status(job_id, "processing", 10, "Loading identity groups")
            
            # Load all identity groups
            all_embeddings = []
            all_labels = []
            
            for i, group_id in enumerate(identity_group_ids):
                group = identity_group_manager.get_identity(group_id)
                if not group:
                    continue
                    
                progress = 10 + (30 * i // len(identity_group_ids))
                self._update_job_status(job_id, "processing", progress, 
                                       f"Processing group {group.get('label', group_id)}")
                
                # Get embeddings for all faces in the group
                for face_id in group.get("face_ids", []):
                    # Load the face image
                    import cv2
                    face_path = os.path.join(self.base_dir, "faces", f"{face_id}.jpg")
                    if os.path.exists(face_path):
                        face_img = cv2.imread(face_path)
                        if face_img is not None:
                            embedding = face_landmark_detector.get_face_embedding(face_img)
                            if embedding is not None:
                                all_embeddings.append(embedding)
                                all_labels.append(group_id)
                        
            if not all_embeddings:
                raise Exception("No face embeddings found for training")
                
            self._update_job_status(job_id, "processing", 50, "Preparing training data")
            
            # Convert to numpy arrays
            X = np.array(all_embeddings)
            y = np.array(all_labels)
            
            self._update_job_status(job_id, "processing", 60, "Training model")
            
            # Train SVM classifier
            classifier = SVC(kernel='linear', probability=True)
            classifier.fit(X, y)
            
            self._update_job_status(job_id, "processing", 90, "Saving model")
            
            # Save the model
            model_filename = f"face_recognition_model_{job_id}.pkl"
            model_path = os.path.join(self.models_dir, model_filename)
            
            with open(model_path, 'wb') as f:
                pickle.dump({
                    'classifier': classifier,
                    'labels': list(set(all_labels)),
                    'created_at': datetime.now().isoformat(),
                    'job_id': job_id
                }, f)
                
            # Update job with model path
            job_data["model_path"] = model_path
            self._update_job_status(job_id, "completed", 100, "Training completed successfully")
            
            # Save as the latest model
            latest_model_path = os.path.join(self.models_dir, "latest_model.pkl")
            with open(latest_model_path, 'wb') as f:
                pickle.dump({
                    'classifier': classifier,
                    'labels': list(set(all_labels)),
                    'created_at': datetime.now().isoformat(),
                    'job_id': job_id
                }, f)
                
        except Exception as e:
            logger.error(f"Error training model for job {job_id}: {str(e)}")
            self._update_job_status(job_id, "failed", 0, "Training failed", str(e))
            
    def get_latest_model(self):
        """Get the latest trained model"""
        latest_model_path = os.path.join(self.models_dir, "latest_model.pkl")
        
        if os.path.exists(latest_model_path):
            with open(latest_model_path, 'rb') as f:
                return pickle.load(f)
                
        return None
        
    def predict_identity(self, face_embedding: np.ndarray) -> Dict[str, Any]:
        """Predict identity for a face embedding"""
        model_data = self.get_latest_model()
        
        if not model_data:
            return {"identity_id": None, "confidence": 0.0}
            
        classifier = model_data['classifier']
        
        # Make prediction
        probabilities = classifier.predict_proba([face_embedding])[0]
        predicted_label = classifier.predict([face_embedding])[0]
        confidence = max(probabilities)
        
        return {
            "identity_id": predicted_label,
            "confidence": float(confidence),
            "all_probabilities": {
                label: float(prob) 
                for label, prob in zip(classifier.classes_, probabilities)
            }
        }

# Create singleton instance
training_manager = TrainingManager()