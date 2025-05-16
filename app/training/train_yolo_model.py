#!/usr/bin/env python3
"""
Train YOLO model for employee attendance detection
"""
import os
import sys
import json
import argparse
import shutil
from ultralytics import YOLO
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train_yolo_model(job_id: str, dataset_yaml: str, epochs: int = 50, batch_size: int = 16, imgsz: int = 640):
    """
    Train YOLO model on prepared dataset
    
    Args:
        job_id: Training job ID
        dataset_yaml: Path to dataset.yaml file
        epochs: Number of training epochs
        batch_size: Batch size for training
        imgsz: Image size for training
    """
    logger.info(f"Starting YOLO training for job {job_id}")
    logger.info(f"Dataset: {dataset_yaml}")
    logger.info(f"Epochs: {epochs}, Batch: {batch_size}, Image size: {imgsz}")
    
    # Create output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "models", f"yolo_{job_id}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Update training status
    script_dir = os.path.dirname(os.path.abspath(__file__))
    status_file = os.path.join(script_dir, f"{job_id}_status.json")

    def update_status(status, progress, message):
        # Save to script directory
        with open(status_file, 'w') as f:
            json.dump({
                'job_id': job_id,
                'status': status,
                'progress': progress,
                'message': message
            }, f)
        # Also save to current directory
        current_status = f"{job_id}_status.json"
        with open(current_status, 'w') as f:
            json.dump({
                'job_id': job_id,
                'status': status,
                'progress': progress,
                'message': message
            }, f)
    
    try:
        # Verify dataset exists
        update_status('training', 5, 'Verifying dataset')
        if not os.path.exists(dataset_yaml):
            raise Exception(f"Dataset YAML not found: {dataset_yaml}")

        # Check dataset structure
        with open(dataset_yaml, 'r') as f:
            import yaml
            dataset_config = yaml.safe_load(f)
            dataset_path = dataset_config.get('path')
            train_dir = os.path.join(dataset_path, dataset_config.get('train', 'images/train'))
            val_dir = os.path.join(dataset_path, dataset_config.get('val', 'images/val'))

            if not os.path.exists(train_dir):
                raise Exception(f"Training directory not found: {train_dir}")
            if not os.path.exists(val_dir):
                raise Exception(f"Validation directory not found: {val_dir}")

            train_images = len(os.listdir(train_dir))
            val_images = len(os.listdir(val_dir))
            logger.info(f"Dataset verified: {train_images} train, {val_images} val images")

        # Initialize model
        update_status('training', 10, 'Loading YOLO model')
        model = YOLO('yolov8n.pt')  # Start with nano model for speed
        
        # Train the model
        update_status('training', 20, 'Starting training')
        logger.info("Starting YOLO training...")
        
        results = model.train(
            data=dataset_yaml,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch_size,
            project=output_dir,
            name='attendance',
            exist_ok=True,
            device='cpu',  # Use CPU to avoid memory issues
            workers=0,     # Disable multiprocessing
            patience=10,   # Early stopping
            verbose=True,
            val=True
        )
        
        # Copy best model
        update_status('saving', 90, 'Saving model')
        best_model = os.path.join(output_dir, 'attendance', 'weights', 'best.pt')
        final_model = os.path.join(output_dir, f'employee_detector_{job_id}.pt')
        
        if os.path.exists(best_model):
            shutil.copy2(best_model, final_model)
            logger.info(f"Model saved to: {final_model}")
        else:
            raise Exception("Best model not found")
        
        # Save metadata
        metadata = {
            'job_id': job_id,
            'model_path': final_model,
            'dataset_yaml': dataset_yaml,
            'epochs': epochs,
            'batch_size': batch_size,
            'image_size': imgsz,
            'status': 'completed'
        }
        
        metadata_file = os.path.join(output_dir, 'metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        update_status('completed', 100, 'Training completed successfully')
        logger.info("Training completed successfully")
        
        return final_model
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        update_status('failed', 0, f'Training failed: {str(e)}')
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train YOLO model')
    parser.add_argument('--job-id', required=True, help='Training job ID')
    parser.add_argument('--dataset', required=True, help='Path to dataset.yaml')
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    parser.add_argument('--batch', type=int, default=8, help='Batch size')
    parser.add_argument('--imgsz', type=int, default=320, help='Image size')
    
    args = parser.parse_args()
    
    # Train model
    model_path = train_yolo_model(
        args.job_id,
        args.dataset,
        args.epochs,
        args.batch,
        args.imgsz
    )
    
    # Save result to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_file = os.path.join(script_dir, f"{args.job_id}_result.json")
    with open(result_file, 'w') as f:
        json.dump({
            'job_id': args.job_id,
            'model_path': model_path,
            'status': 'completed'
        }, f)

    # Also save to current directory
    current_dir_result = f"{args.job_id}_result.json"
    with open(current_dir_result, 'w') as f:
        json.dump({
            'job_id': args.job_id,
            'model_path': model_path,
            'status': 'completed'
        }, f)

    print(f"Training completed. Model saved to: {model_path}")
    print(f"Result saved to: {result_file}")