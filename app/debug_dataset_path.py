#!/usr/bin/env python3
"""
Debug dataset paths and check what's actually being created
"""
import os
import json
import sys

def debug_dataset(job_id):
    training_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training")
    datasets_dir = os.path.join(training_dir, "datasets")
    dataset_dir = os.path.join(datasets_dir, f"dataset_{job_id}")
    
    print(f"Checking dataset for job: {job_id}")
    print(f"Training dir: {training_dir}")
    print(f"Datasets dir: {datasets_dir}")
    print(f"Dataset dir: {dataset_dir}")
    print(f"Dataset exists: {os.path.exists(dataset_dir)}")
    
    if os.path.exists(dataset_dir):
        print("\nDirectory contents:")
        for root, dirs, files in os.walk(dataset_dir):
            level = root.replace(dataset_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 2 * (level + 1)
            for file in files[:5]:  # Show first 5 files
                print(f"{sub_indent}{file}")
            if len(files) > 5:
                print(f"{sub_indent}... and {len(files) - 5} more files")
    
    # Check dataset.yaml
    yaml_path = os.path.join(dataset_dir, "dataset.yaml")
    if os.path.exists(yaml_path):
        print(f"\ndataset.yaml contents:")
        with open(yaml_path, 'r') as f:
            print(f.read())
    
    # Check images directory
    images_train = os.path.join(dataset_dir, "images", "train")
    if os.path.exists(images_train):
        image_count = len(os.listdir(images_train))
        print(f"\nImages in train directory: {image_count}")
        if image_count > 0:
            sample_images = os.listdir(images_train)[:3]
            print(f"Sample images: {sample_images}")
    else:
        print(f"\nTrain images directory NOT FOUND: {images_train}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_dataset(sys.argv[1])
    else:
        # List recent datasets
        training_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training")
        datasets_dir = os.path.join(training_dir, "datasets")
        
        if os.path.exists(datasets_dir):
            datasets = [d for d in os.listdir(datasets_dir) if d.startswith("dataset_")]
            print(f"Available datasets: {datasets[-5:]}")  # Show last 5
            
            if datasets:
                latest = datasets[-1]
                job_id = latest.replace("dataset_", "")
                print(f"\nChecking latest dataset: {job_id}")
                debug_dataset(job_id)