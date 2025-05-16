import os
import json
import time
import uuid
import threading
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
import torch
import cv2
from ultralytics import YOLO
import logging

logger = logging.getLogger(__name__)

class YOLOTrainingManager:
    """
    Training manager using YOLO for face classification
    Uses the existing YOLO model to train a custom classifier for face recognition
    """
    
    def __init__(self):
        """Initialize the YOLO training manager"""
        self.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
        self.models_dir = os.path.join(self.base_dir, "models")
        self.jobs_dir = os.path.join(self.base_dir, "training_jobs")
        self.datasets_dir = os.path.join(self.base_dir, "yolo_datasets")
        
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.jobs_dir, exist_ok=True)
        os.makedirs(self.datasets_dir, exist_ok=True)
        
        # Active training jobs
        self.active_jobs = {}
        
        # Base YOLO model for face detection
        self.base_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "yolov8n-face.pt")
        
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
            
    def _prepare_yolo_dataset(self, job_id: str, identity_group_ids: List[str]) -> str:
        """Prepare YOLO dataset structure for training"""
        from db.identity_groups import identity_group_manager
        
        # Create dataset directory
        dataset_dir = os.path.join(self.datasets_dir, job_id)
        train_dir = os.path.join(dataset_dir, "train")
        val_dir = os.path.join(dataset_dir, "val")
        
        os.makedirs(train_dir, exist_ok=True)
        os.makedirs(val_dir, exist_ok=True)
        
        # Create images and labels directories
        train_images = os.path.join(train_dir, "images")
        train_labels = os.path.join(train_dir, "labels")
        val_images = os.path.join(val_dir, "images")
        val_labels = os.path.join(val_dir, "labels")
        
        os.makedirs(train_images, exist_ok=True)
        os.makedirs(train_labels, exist_ok=True)
        os.makedirs(val_images, exist_ok=True)
        os.makedirs(val_labels, exist_ok=True)
        
        # Copy faces and create labels
        class_names = []
        class_mapping = {}
        
        for idx, group_id in enumerate(identity_group_ids):
            group = identity_group_manager.get_identity(group_id)
            if not group:
                continue
                
            class_names.append(group_id)
            class_mapping[group_id] = idx
            
            face_ids = group.get("face_ids", [])
            
            # Split faces into train/val (80/20)
            split_idx = int(len(face_ids) * 0.8)
            train_faces = face_ids[:split_idx]
            val_faces = face_ids[split_idx:]
            
            # Process training faces
            for face_id in train_faces:
                src_path = os.path.join(self.base_dir, "faces", f"{face_id}.jpg")
                if os.path.exists(src_path):
                    dst_path = os.path.join(train_images, f"{face_id}.jpg")
                    shutil.copy2(src_path, dst_path)
                    
                    # Create label file (YOLO format: class_id x_center y_center width height)
                    label_path = os.path.join(train_labels, f"{face_id}.txt")
                    with open(label_path, 'w') as f:
                        # For face classification, we use the whole image as the bounding box
                        f.write(f"{idx} 0.5 0.5 1.0 1.0\n")
                        
            # Process validation faces
            for face_id in val_faces:
                src_path = os.path.join(self.base_dir, "faces", f"{face_id}.jpg")
                if os.path.exists(src_path):
                    dst_path = os.path.join(val_images, f"{face_id}.jpg")
                    shutil.copy2(src_path, dst_path)
                    
                    label_path = os.path.join(val_labels, f"{face_id}.txt")
                    with open(label_path, 'w') as f:
                        f.write(f"{idx} 0.5 0.5 1.0 1.0\n")
                        
        # Create dataset.yaml
        yaml_content = f"""
path: {dataset_dir}
train: train/images
val: val/images

names:
"""
        for idx, name in enumerate(class_names):
            yaml_content += f"  {idx}: {name}\n"
            
        yaml_path = os.path.join(dataset_dir, "dataset.yaml")
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
            
        return yaml_path
            
    def _train_model(self, job_id: str):
        """Train the YOLO model for face classification"""
        try:
            job_data = self.active_jobs[job_id]
            identity_group_ids = job_data["identity_group_ids"]
            
            self._update_job_status(job_id, "processing", 10, "Preparing dataset")
            
            # Prepare YOLO dataset
            dataset_yaml = self._prepare_yolo_dataset(job_id, identity_group_ids)
            
            self._update_job_status(job_id, "processing", 30, "Loading base model")
            
            # Load YOLO model
            if os.path.exists(self.base_model_path):
                model = YOLO(self.base_model_path)
            else:
                # Use pre-trained model
                model = YOLO('yolov8n.pt')
                
            self._update_job_status(job_id, "processing", 40, "Starting training")
            
            # Train the model
            results = model.train(
                data=dataset_yaml,
                epochs=10,  # Fewer epochs for faster training
                imgsz=640,
                batch=16,
                device='cpu',  # Use CPU if no CUDA available
                project=self.models_dir,
                name=job_id,
                exist_ok=True,
                verbose=False
            )
            
            self._update_job_status(job_id, "processing", 90, "Saving model")
            
            # Save the best model
            model_path = os.path.join(self.models_dir, job_id, "weights", "best.pt")
            
            # Update job with model path
            job_data["model_path"] = model_path
            self._update_job_status(job_id, "completed", 100, "Training completed successfully")
            
            # Save as the latest model
            latest_model_path = os.path.join(self.models_dir, "latest_yolo_model.pt")
            shutil.copy2(model_path, latest_model_path)
            
            logger.info(f"Training job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error training model for job {job_id}: {str(e)}")
            self._update_job_status(job_id, "failed", 0, "Training failed", str(e))
            
    def get_latest_model(self):
        """Get the latest trained model"""
        latest_model_path = os.path.join(self.models_dir, "latest_yolo_model.pt")
        
        if os.path.exists(latest_model_path):
            return YOLO(latest_model_path)
            
        return None
        
    def predict_identity(self, face_image: np.ndarray) -> Dict[str, Any]:
        """Predict identity for a face image using the trained YOLO model"""
        model = self.get_latest_model()
        
        if not model:
            return {"identity_id": None, "confidence": 0.0}
            
        # Run inference
        results = model.predict(face_image, verbose=False)
        
        if results and len(results[0].probs) > 0:
            probs = results[0].probs
            top_class = probs.top1
            confidence = probs.top1conf.item()
            
            # Get class name (identity ID)
            identity_id = model.names[top_class]
            
            return {
                "identity_id": identity_id,
                "confidence": float(confidence),
                "all_probabilities": {
                    model.names[i]: float(probs.data[i]) 
                    for i in range(len(probs.data))
                }
            }
            
        return {"identity_id": None, "confidence": 0.0}

# Create singleton instance
yolo_training_manager = YOLOTrainingManager()