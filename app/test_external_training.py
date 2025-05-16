#!/usr/bin/env python3
"""
Test the external YOLO training system
"""
import os
import sys
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.external_yolo_trainer import external_yolo_trainer

def test_training():
    """Test the external training system"""
    print("Testing External YOLO Training System")
    print("====================================")
    
    # Test with a few groups
    test_groups = ["PERSON-0001", "PERSON-0002", "PERSON-0003"]
    
    print(f"\nStarting training with groups: {test_groups}")
    
    # Start training
    job_id = external_yolo_trainer.start_training(
        group_ids=test_groups,
        epochs=2,  # Very few epochs for testing
        batch_size=4
    )
    
    print(f"Training job started with ID: {job_id}")
    
    # Check status
    import time
    for i in range(10):
        time.sleep(2)
        status = external_yolo_trainer.get_job_status(job_id)
        print(f"\nStatus check {i+1}:")
        print(f"  Status: {status.get('status')}")
        print(f"  Progress: {status.get('progress')}%")
        print(f"  Message: {status.get('message')}")
        
        if status.get('status') in ['completed', 'failed']:
            break
    
    print("\nFinal status:")
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    test_training()