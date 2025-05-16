import os
import json
import shutil
import uuid
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
import cv2
import logging
from ultralytics import YOLO
import yaml
from db.identity_groups import identity_group_manager

logger = logging.getLogger(__name__)

class YOLOAttendanceTrainer:
    """
    Train YOLO model for employee attendance tracking
    This creates a custom YOLO model that can detect specific employees
    """
    
    def __init__(self):
        """Initialize the YOLO attendance trainer"""
        self.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
        self.models_dir = os.path.join(self.base_dir, "yolo_models")
        self.datasets_dir = os.path.join(self.base_dir, "yolo_datasets")
        self.faces_dir = os.path.join(self.base_dir, "faces")
        
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.datasets_dir, exist_ok=True)
        
        # In-memory job tracking
        self.jobs = {}
        
    def start_training(self, group_ids: List[str], model_name: str = "yolov8n") -> str:
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
        thread = threading.Thread(target=self._train_yolo_model, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        return job_id
        
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a training job"""
        return self.jobs.get(job_id)
        
    def _create_yolo_dataset(self, job_id: str, group_ids: List[str]) -> str:
        """Create YOLO format dataset from identity groups"""
        dataset_dir = os.path.join(self.datasets_dir, f"dataset_{job_id}")
        images_dir = os.path.join(dataset_dir, "images")
        labels_dir = os.path.join(dataset_dir, "labels")
        
        # Create directories
        os.makedirs(os.path.join(images_dir, "train"), exist_ok=True)
        os.makedirs(os.path.join(images_dir, "val"), exist_ok=True)
        os.makedirs(os.path.join(labels_dir, "train"), exist_ok=True)
        os.makedirs(os.path.join(labels_dir, "val"), exist_ok=True)
        
        # Get all identity groups
        all_groups = identity_group_manager.identities.get('groups', {})
        
        # Create class mapping (employee names/IDs)
        class_names = []
        class_mapping = {}
        
        for idx, group_id in enumerate(group_ids):
            group_data = all_groups.get(group_id)
            if group_data:
                # Use group ID as class name (e.g., PERSON-0001)
                class_names.append(group_id)
                class_mapping[group_id] = idx
        
        # Process faces for each group
        train_count = 0
        val_count = 0
        
        for group_id in group_ids:
            group_data = all_groups.get(group_id)
            if not group_data:
                continue
                
            face_ids = group_data.get('face_ids', [])
            class_idx = class_mapping[group_id]
            
            # Split faces into train/val (80/20)
            split_idx = int(len(face_ids) * 0.8)
            train_faces = face_ids[:split_idx]
            val_faces = face_ids[split_idx:]
            
            # Process training faces
            for face_id in train_faces:
                face_path = os.path.join(self.faces_dir, f"{face_id}.jpg")
                if os.path.exists(face_path):
                    # Copy image
                    dest_image = os.path.join(images_dir, "train", f"{face_id}.jpg")
                    shutil.copy2(face_path, dest_image)
                    
                    # Create YOLO label (normalized bbox)
                    # For face crops, the whole image is the face
                    label_content = f"{class_idx} 0.5 0.5 1.0 1.0\n"
                    label_path = os.path.join(labels_dir, "train", f"{face_id}.txt")
                    with open(label_path, 'w') as f:
                        f.write(label_content)
                    
                    train_count += 1
            
            # Process validation faces
            for face_id in val_faces:
                face_path = os.path.join(self.faces_dir, f"{face_id}.jpg")
                if os.path.exists(face_path):
                    # Copy image
                    dest_image = os.path.join(images_dir, "val", f"{face_id}.jpg")
                    shutil.copy2(face_path, dest_image)
                    
                    # Create YOLO label
                    label_content = f"{class_idx} 0.5 0.5 1.0 1.0\n"
                    label_path = os.path.join(labels_dir, "val", f"{face_id}.txt")
                    with open(label_path, 'w') as f:
                        f.write(label_content)
                    
                    val_count += 1
        
        # Create YAML configuration
        yaml_config = {
            'path': dataset_dir,
            'train': 'images/train',
            'val': 'images/val',
            'nc': len(class_names),  # number of classes
            'names': class_names     # class names
        }
        
        yaml_path = os.path.join(dataset_dir, 'dataset.yaml')
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_config, f)
        
        logger.info(f"Created YOLO dataset with {train_count} training and {val_count} validation images")
        return yaml_path, train_count, val_count
        
    def _train_yolo_model(self, job_id: str):
        """Train YOLO model for employee detection"""
        try:
            job = self.jobs.get(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return
                
            group_ids = job.get('group_ids', [])
            model_name = job.get('model_name', 'yolov8n')
            
            logger.info(f"Starting YOLO training with {len(group_ids)} employee groups")
            
            # Update job status
            job['status'] = 'processing'
            job['progress'] = 10
            job['message'] = 'Creating YOLO dataset'
            job['updated_at'] = datetime.now().isoformat()
            
            # Create YOLO dataset
            yaml_path, train_count, val_count = self._create_yolo_dataset(job_id, group_ids)
            
            if train_count == 0:
                raise Exception("No training images found")
            
            # Update status
            job['progress'] = 30
            job['message'] = f'Training YOLO on {train_count} images'
            job['updated_at'] = datetime.now().isoformat()
            
            # Load base YOLO model
            model = YOLO(f'{model_name}.pt')
            
            # Train the model with reduced memory usage
            results = model.train(
                data=yaml_path,
                epochs=10,  # Reduced epochs for testing
                imgsz=320,  # Smaller image size to reduce memory
                batch=4,    # Smaller batch size to reduce memory
                project=self.models_dir,
                name=f'attendance_model_{job_id}',
                exist_ok=True,
                device='cpu',  # Use 'cuda' if GPU available
                verbose=True,
                workers=0,  # Disable multiprocessing to save memory
                patience=5,  # Early stopping patience
                amp=False   # Disable automatic mixed precision
            )
            
            # Update status
            job['progress'] = 90
            job['message'] = 'Saving model'
            job['updated_at'] = datetime.now().isoformat()
            
            # Copy best model to a standard location
            best_model_path = os.path.join(self.models_dir, f'attendance_model_{job_id}', 'weights', 'best.pt')
            final_model_path = os.path.join(self.models_dir, f'employee_detector_{job_id}.pt')
            
            if os.path.exists(best_model_path):
                shutil.copy2(best_model_path, final_model_path)
            
            # Save as latest model
            latest_model_path = os.path.join(self.models_dir, 'latest_employee_detector.pt')
            shutil.copy2(final_model_path, latest_model_path)
            
            # Update job status to completed
            job['status'] = 'completed'
            job['progress'] = 100
            job['message'] = f'Training completed. Model trained to detect {len(group_ids)} employees.'
            job['model_path'] = final_model_path
            job['updated_at'] = datetime.now().isoformat()
            job['summary'] = {
                'employees': len(group_ids),
                'train_images': train_count,
                'val_images': val_count,
                'model_type': model_name
            }
            
            logger.info(f"YOLO training job {job_id} completed successfully")

        except MemoryError as e:
            logger.error(f"Memory error during YOLO training for job {job_id}: {str(e)}")
            job['status'] = 'failed'
            job['progress'] = 0
            job['message'] = 'Training failed: Out of memory. Try reducing batch size or image size.'
            job['error'] = 'Out of memory'
            job['updated_at'] = datetime.now().isoformat()
        except Exception as e:
            import traceback
            logger.error(f"Error training YOLO model for job {job_id}: {str(e)}")
            logger.error(traceback.format_exc())
            job['status'] = 'failed'
            job['progress'] = 0
            job['message'] = 'Training failed'
            job['error'] = str(e)
            job['updated_at'] = datetime.now().isoformat()
    
    def test_model(self, model_path: str, video_path: str) -> Dict[str, Any]:
        """Test the trained model on a video"""
        try:
            # Load the trained model
            model = YOLO(model_path)
            
            # Process video
            results = model.predict(source=video_path, save=True, conf=0.5)
            
            # Analyze results
            detections = []
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        detections.append({
                            'employee_id': result.names[int(box.cls)],
                            'confidence': float(box.conf),
                            'bbox': box.xyxy[0].tolist()
                        })
            
            return {
                'success': True,
                'detections': detections,
                'total_frames': len(results),
                'unique_employees': list(set(d['employee_id'] for d in detections))
            }
            
        except Exception as e:
            logger.error(f"Error testing model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Create singleton instance
yolo_attendance_trainer = YOLOAttendanceTrainer()