#!/usr/bin/env python3
"""
Prepare YOLO dataset from selected employee face groups
"""
import os
import sys
import json
import shutil
import yaml
import argparse
from typing import List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.identity_groups import identity_group_manager

def prepare_yolo_dataset(job_id: str, group_ids: List[str], output_dir: str):
    """
    Prepare YOLO dataset from selected face groups
    
    Args:
        job_id: Training job ID
        group_ids: List of employee group IDs
        output_dir: Output directory for YOLO dataset
    """
    print(f"Preparing YOLO dataset for job {job_id}")
    print(f"Selected groups: {len(group_ids)}")
    
    # Create dataset structure
    dataset_dir = os.path.join(output_dir, f"dataset_{job_id}")
    images_train = os.path.join(dataset_dir, "images", "train")
    images_val = os.path.join(dataset_dir, "images", "val")
    labels_train = os.path.join(dataset_dir, "labels", "train")
    labels_val = os.path.join(dataset_dir, "labels", "val")
    
    os.makedirs(images_train, exist_ok=True)
    os.makedirs(images_val, exist_ok=True)
    os.makedirs(labels_train, exist_ok=True)
    os.makedirs(labels_val, exist_ok=True)
    
    # Get face groups data
    all_groups = identity_group_manager.identities.get('groups', {})
    
    # Create class mapping
    class_names = []
    class_mapping = {}
    
    for idx, group_id in enumerate(group_ids):
        group_data = all_groups.get(group_id)
        if group_data:
            class_names.append(group_id)
            class_mapping[group_id] = idx
    
    print(f"Classes (employees): {len(class_names)}")
    
    # Process faces
    train_count = 0
    val_count = 0
    # Fix the path to faces directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(script_dir)  # Go up from training to app directory
    faces_dir = os.path.join(app_dir, "static", "faces")

    print(f"Looking for faces in: {faces_dir}")
    if not os.path.exists(faces_dir):
        print(f"ERROR: Faces directory not found at {faces_dir}")
        return {}
    
    for group_id in group_ids:
        group_data = all_groups.get(group_id)
        if not group_data:
            print(f"Warning: Group {group_id} not found")
            continue
            
        face_ids = group_data.get('face_ids', [])
        class_idx = class_mapping[group_id]
        
        # Split 80/20 for train/val
        split_idx = int(len(face_ids) * 0.8)
        train_faces = face_ids[:split_idx]
        val_faces = face_ids[split_idx:]
        
        print(f"Processing {group_id}: {len(train_faces)} train, {len(val_faces)} val")
        
        # Process training faces
        for face_id in train_faces:
            src_path = os.path.join(faces_dir, f"{face_id}.jpg")
            if os.path.exists(src_path):
                # Copy image
                dst_image = os.path.join(images_train, f"{face_id}.jpg")
                shutil.copy2(src_path, dst_image)

                # Create label (full image is the face)
                # Format: class_idx center_x center_y width height (normalized)
                label_path = os.path.join(labels_train, f"{face_id}.txt")
                with open(label_path, 'w') as f:
                    f.write(f"{class_idx} 0.5 0.5 1.0 1.0\n")

                train_count += 1
                if train_count <= 3:  # Log first few files
                    print(f"  Copied: {src_path} -> {dst_image}")
            else:
                print(f"  Warning: Face image not found: {src_path}")
        
        # Process validation faces
        for face_id in val_faces:
            src_path = os.path.join(faces_dir, f"{face_id}.jpg")
            if os.path.exists(src_path):
                # Copy image
                dst_image = os.path.join(images_val, f"{face_id}.jpg")
                shutil.copy2(src_path, dst_image)
                
                # Create label
                label_path = os.path.join(labels_val, f"{face_id}.txt")
                with open(label_path, 'w') as f:
                    f.write(f"{class_idx} 0.5 0.5 1.0 1.0\n")
                
                val_count += 1
    
    # Create dataset.yaml with absolute paths
    yaml_config = {
        'path': os.path.abspath(dataset_dir),  # Use absolute path
        'train': 'images/train',
        'val': 'images/val',
        'nc': len(class_names),
        'names': class_names
    }

    yaml_path = os.path.join(dataset_dir, 'dataset.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_config, f)

    print(f"\nDataset YAML config:")
    print(f"  path: {yaml_config['path']}")
    print(f"  classes: {len(class_names)}")
    print(f"  train: {yaml_config['train']}")
    print(f"  val: {yaml_config['val']}")
    
    # Save metadata
    metadata = {
        'job_id': job_id,
        'groups': group_ids,
        'train_images': train_count,
        'val_images': val_count,
        'classes': len(class_names),
        'dataset_path': dataset_dir,
        'yaml_path': yaml_path
    }
    
    metadata_path = os.path.join(dataset_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nDataset prepared:")
    print(f"  Training images: {train_count}")
    print(f"  Validation images: {val_count}")
    print(f"  Classes (employees): {len(class_names)}")
    print(f"  Dataset path: {dataset_dir}")
    print(f"  YAML config: {yaml_path}")
    
    return metadata

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prepare YOLO dataset')
    parser.add_argument('--job-id', required=True, help='Training job ID')
    parser.add_argument('--groups', required=True, help='JSON array of group IDs')
    parser.add_argument('--output-dir', default='./datasets', help='Output directory')
    
    args = parser.parse_args()
    
    # Parse group IDs
    group_ids = json.loads(args.groups)
    
    # Prepare dataset
    metadata = prepare_yolo_dataset(args.job_id, group_ids, args.output_dir)
    
    # Write result to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_file = os.path.join(script_dir, f"{args.job_id}_dataset.json")
    with open(result_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nDataset metadata saved to: {result_file}")

    # Also save to current directory for compatibility
    current_dir_result = f"{args.job_id}_dataset.json"
    with open(current_dir_result, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Also saved to: {current_dir_result}")