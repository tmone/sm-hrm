#!/usr/bin/env python3
"""
Test the complete external YOLO training flow
"""
import os
import sys
import time
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.external_yolo_trainer import external_yolo_trainer

def test_training_flow():
    print("Testing External YOLO Training Flow")
    print("==================================")
    
    # Test with just 2 groups for quick testing
    test_groups = ["PERSON-0017", "PERSON-0020"]
    
    print(f"\nStarting training with groups: {test_groups}")
    
    # Start training
    job_id = external_yolo_trainer.start_training(
        group_ids=test_groups,
        epochs=1,  # Just 1 epoch for testing
        batch_size=2
    )
    
    print(f"Training job started with ID: {job_id}")
    
    # Monitor progress
    for i in range(30):  # Monitor for up to 5 minutes
        time.sleep(10)
        status = external_yolo_trainer.get_job_status(job_id)
        print(f"\nStatus check {i+1}:")
        print(f"  Status: {status.get('status')}")
        print(f"  Progress: {status.get('progress')}%")
        print(f"  Message: {status.get('message')}")
        print(f"  Error: {status.get('error')}")
        
        if status.get('status') in ['completed', 'failed']:
            break
    
    print("\nFinal status:")
    print(json.dumps(status, indent=2))
    
    # Check dataset creation
    dataset_dir = f"/home/tmone/pinokio/api/StepmediaHRM/app/training/datasets/dataset_{job_id}"
    if os.path.exists(dataset_dir):
        print(f"\nDataset created at: {dataset_dir}")
        images_train = os.path.join(dataset_dir, "images", "train")
        if os.path.exists(images_train):
            image_count = len(os.listdir(images_train))
            print(f"Training images: {image_count}")

if __name__ == "__main__":
    test_training_flow()