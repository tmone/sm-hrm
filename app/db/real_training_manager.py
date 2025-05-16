import os
import json
import time
import uuid
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import pickle
import cv2
import logging

logger = logging.getLogger(__name__)

class RealTrainingManager:
    """
    Real training manager using dlib face embeddings and SVM classifier
    This uses actual face embeddings for training a face recognition model
    """
    
    def __init__(self):
        """Initialize the real training manager"""
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
        """Train the face recognition model using real embeddings"""
        try:
            from db.models import IdentityGroup, Face, SessionManager

            job_data = self.active_jobs[job_id]
            identity_group_ids = job_data["identity_group_ids"]

            self._update_job_status(job_id, "processing", 10, f"Loading {len(identity_group_ids)} identity groups")

            # Load all identity groups and collect embeddings
            all_embeddings = []
            all_labels = []
            groups_processed = 0
            groups_with_embeddings = 0
            total_faces_processed = 0
            faces_with_embeddings = 0

            with SessionManager() as session:
                for i, group_id in enumerate(identity_group_ids):
                    try:
                        # Get the identity group from database
                        group = session.query(IdentityGroup).filter_by(id=group_id).first()
                        if not group:
                            logger.warning(f"Group {group_id} not found in database")
                            continue

                        groups_processed += 1
                        progress = 10 + (30 * i // len(identity_group_ids))
                        self._update_job_status(job_id, "processing", progress,
                                               f"Processing group {group.identity} ({i+1}/{len(identity_group_ids)})")

                        # Get all faces in this group
                        faces = session.query(Face).filter_by(identity_group_id=group_id).all()
                        logger.info(f"Group {group.identity} has {len(faces)} faces")

                        group_embedding_count = 0
                        for face in faces:
                            total_faces_processed += 1
                            if face.embedding_json:
                                try:
                                    embedding = json.loads(face.embedding_json)
                                    if isinstance(embedding, list) and len(embedding) == 128:
                                        all_embeddings.append(embedding)
                                        all_labels.append(group.identity)
                                        group_embedding_count += 1
                                        faces_with_embeddings += 1
                                    else:
                                        logger.warning(f"Invalid embedding size for face {face.id}: {len(embedding) if isinstance(embedding, list) else 'not a list'}")
                                except Exception as e:
                                    logger.error(f"Error parsing embedding for face {face.id}: {e}")
                            else:
                                logger.debug(f"Face {face.id} has no embedding")

                        if group_embedding_count > 0:
                            groups_with_embeddings += 1
                            logger.info(f"Added {group_embedding_count} embeddings for group {group.identity}")
                        else:
                            logger.warning(f"No valid embeddings found for group {group.identity}")

                    except Exception as e:
                        logger.error(f"Error processing group {group_id}: {e}")
                        continue

            # Log summary
            logger.info(f"Training summary:")
            logger.info(f"  - Groups requested: {len(identity_group_ids)}")
            logger.info(f"  - Groups found in DB: {groups_processed}")
            logger.info(f"  - Groups with embeddings: {groups_with_embeddings}")
            logger.info(f"  - Total faces processed: {total_faces_processed}")
            logger.info(f"  - Faces with embeddings: {faces_with_embeddings}")
            logger.info(f"  - Total embeddings collected: {len(all_embeddings)}")
            logger.info(f"  - Unique identities: {len(set(all_labels))}")

            if not all_embeddings:
                raise Exception(f"No face embeddings found for training. Processed {groups_processed} groups and {total_faces_processed} faces.")

            self._update_job_status(job_id, "processing", 50, f"Preparing {len(all_embeddings)} face embeddings from {len(set(all_labels))} identities")

            # Convert to numpy arrays
            X = np.array(all_embeddings)
            y = np.array(all_labels)

            # Normalize embeddings
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            self._update_job_status(job_id, "processing", 70, "Training SVM classifier")

            # Train SVM classifier
            classifier = SVC(kernel='rbf', probability=True, C=1.0, gamma='auto')
            classifier.fit(X_scaled, y)

            self._update_job_status(job_id, "processing", 90, "Saving model")

            # Save the model and scaler
            model_filename = f"face_recognition_model_{job_id}.pkl"
            model_path = os.path.join(self.models_dir, model_filename)

            with open(model_path, 'wb') as f:
                pickle.dump({
                    'classifier': classifier,
                    'scaler': scaler,
                    'labels': list(set(all_labels)),
                    'embedding_count': len(all_embeddings),
                    'created_at': datetime.now().isoformat(),
                    'job_id': job_id,
                    'summary': {
                        'groups_requested': len(identity_group_ids),
                        'groups_processed': groups_processed,
                        'groups_with_embeddings': groups_with_embeddings,
                        'total_faces': total_faces_processed,
                        'faces_with_embeddings': faces_with_embeddings
                    }
                }, f)

            # Update job with model path
            job_data["model_path"] = model_path
            self._update_job_status(job_id, "completed", 100,
                                   f"Training completed successfully. Model trained on {len(all_embeddings)} faces from {len(set(all_labels))} identities.")

            # Save as the latest model
            latest_model_path = os.path.join(self.models_dir, "latest_model.pkl")
            with open(latest_model_path, 'wb') as f:
                pickle.dump({
                    'classifier': classifier,
                    'scaler': scaler,
                    'labels': list(set(all_labels)),
                    'embedding_count': len(all_embeddings),
                    'created_at': datetime.now().isoformat(),
                    'job_id': job_id,
                    'summary': {
                        'groups_requested': len(identity_group_ids),
                        'groups_processed': groups_processed,
                        'groups_with_embeddings': groups_with_embeddings,
                        'total_faces': total_faces_processed,
                        'faces_with_embeddings': faces_with_embeddings
                    }
                }, f)

            logger.info(f"Training job {job_id} completed successfully")

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
        
    def predict_identity(self, face_image: np.ndarray) -> Dict[str, Any]:
        """Predict identity for a face image using the trained model"""
        try:
            from db.face_landmarks import face_landmark_detector
            
            model_data = self.get_latest_model()
            
            if not model_data:
                return {"identity_id": None, "confidence": 0.0, "error": "No trained model available"}
                
            # Get face embedding
            embedding = face_landmark_detector.get_face_embedding(face_image)
            if embedding is None:
                return {"identity_id": None, "confidence": 0.0, "error": "Could not extract face embedding"}
                
            classifier = model_data['classifier']
            scaler = model_data['scaler']
            
            # Normalize the embedding
            embedding_scaled = scaler.transform([embedding])
            
            # Make prediction
            probabilities = classifier.predict_proba(embedding_scaled)[0]
            predicted_label = classifier.predict(embedding_scaled)[0]
            confidence = max(probabilities)
            
            # Get all probabilities for each identity
            all_probs = {
                label: float(prob) 
                for label, prob in zip(classifier.classes_, probabilities)
            }
            
            return {
                "identity_id": predicted_label,
                "confidence": float(confidence),
                "all_probabilities": all_probs,
                "model_info": {
                    "embedding_count": model_data.get('embedding_count', 0),
                    "identity_count": len(model_data.get('labels', [])),
                    "created_at": model_data.get('created_at')
                }
            }
        except Exception as e:
            logger.error(f"Error predicting identity: {str(e)}")
            return {"identity_id": None, "confidence": 0.0, "error": str(e)}

# Create singleton instance
real_training_manager = RealTrainingManager()