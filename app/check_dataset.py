#!/usr/bin/env python3
"""
Check YOLO dataset structure
"""
import os
import sys
import json

def check_dataset(job_id):
    # Check training directory
    training_dir = os.path.dirname(os.path.abspath(__file__)) + "/training"
    datasets_dir = os.path.join(training_dir, "datasets")
    dataset_dir = os.path.join(datasets_dir, f"dataset_{job_id}")
    
    print(f"Checking dataset for job: {job_id}")
    print(f"Dataset directory: {dataset_dir}")
    
    if not os.path.exists(dataset_dir):
        print(f"ERROR: Dataset directory not found!")
        return
    
    # Check directory structure
    dirs_to_check = [
        "images/train",
        "images/val",
        "labels/train",
        "labels/val"
    ]
    
    for dir_path in dirs_to_check:
        full_path = os.path.join(dataset_dir, dir_path)
        if os.path.exists(full_path):
            files = os.listdir(full_path)
            print(f"✓ {dir_path}: {len(files)} files")
            if len(files) > 0:
                print(f"  Sample files: {files[:3]}")
        else:
            print(f"✗ {dir_path}: NOT FOUND")
    
    # Check dataset.yaml
    yaml_path = os.path.join(dataset_dir, "dataset.yaml")
    if os.path.exists(yaml_path):
        print(f"\n✓ dataset.yaml found")
        with open(yaml_path, 'r') as f:
            print(f"Content:\n{f.read()}")
    else:
        print(f"\n✗ dataset.yaml NOT FOUND")
    
    # Check metadata
    metadata_path = os.path.join(dataset_dir, "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            print(f"\nMetadata:")
            print(json.dumps(metadata, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_dataset.py <job_id>")
        sys.exit(1)
    
    check_dataset(sys.argv[1])