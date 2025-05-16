#!/usr/bin/env python3
"""
Test YOLO model directly on sample images
"""
import os
import sys
import cv2
from ultralytics import YOLO
import glob

def test_model_on_faces():
    # Find latest model
    models_pattern = "/home/tmone/pinokio/api/StepmediaHRM/app/training/models/yolo_*/employee_detector_*.pt"
    model_files = glob.glob(models_pattern)
    
    if not model_files:
        print("No trained models found")
        return
        
    latest_model = max(model_files, key=os.path.getctime)
    print(f"Testing model: {latest_model}")
    
    # Load model
    model = YOLO(latest_model)
    print(f"Model classes: {model.names}")
    
    # Test on some training images
    faces_dir = "/home/tmone/pinokio/api/StepmediaHRM/app/static/faces"
    test_images = glob.glob(os.path.join(faces_dir, "*.jpg"))[:10]
    
    print(f"\nTesting on {len(test_images)} face images...")
    
    detections = 0
    for img_path in test_images:
        results = model.predict(img_path, conf=0.1, verbose=False)
        
        for r in results:
            if r.boxes is not None and len(r.boxes) > 0:
                detections += len(r.boxes)
                for box in r.boxes:
                    class_id = int(box.cls)
                    employee_id = r.names[class_id]
                    confidence = float(box.conf)
                    print(f"  {os.path.basename(img_path)}: {employee_id} (conf={confidence:.3f})")
    
    print(f"\nTotal detections: {detections}")
    
    # Test on a training dataset image
    dataset_train = "/home/tmone/pinokio/api/StepmediaHRM/app/training/datasets/dataset_*/images/train/*.jpg"
    train_images = glob.glob(dataset_train)
    
    if train_images:
        print(f"\nTesting on training dataset images...")
        test_img = train_images[0]
        print(f"Testing: {test_img}")
        
        results = model.predict(test_img, conf=0.1, verbose=False)
        for r in results:
            if r.boxes is not None:
                print(f"  Detections: {len(r.boxes)}")
                for box in r.boxes:
                    class_id = int(box.cls)
                    employee_id = r.names[class_id]
                    confidence = float(box.conf)
                    print(f"    {employee_id} (conf={confidence:.3f})")

if __name__ == "__main__":
    test_model_on_faces()