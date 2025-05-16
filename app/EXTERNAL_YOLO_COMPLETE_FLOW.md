# External YOLO Training - Complete Flow

## System Architecture

```
Main App (FastAPI)
     │
     ├─> ExternalYOLOTrainer.start_training()
     │         │
     │         ├─> Launch prepare_yolo_dataset.py
     │         │     ├─> Load identity groups
     │         │     ├─> Copy face images
     │         │     ├─> Create YOLO labels
     │         │     ├─> Generate dataset.yaml
     │         │     └─> Save metadata.json
     │         │
     │         ├─> Monitor dataset preparation
     │         │
     │         ├─> Launch train_yolo_model.py
     │         │     ├─> Load YOLOv8 model
     │         │     ├─> Train on prepared dataset
     │         │     ├─> Save best model
     │         │     └─> Update status files
     │         │
     │         └─> Monitor training progress
     │
     └─> No restart required!
```

## File Structure

```
StepmediaHRM/app/
├── db/
│   └── external_yolo_trainer.py      # Main controller
├── training/
│   ├── prepare_yolo_dataset.py       # Dataset preparation
│   ├── train_yolo_model.py          # YOLO training
│   ├── datasets/                    # Generated datasets
│   │   └── dataset_<job_id>/
│   │       ├── images/
│   │       │   ├── train/
│   │       │   └── val/
│   │       ├── labels/
│   │       │   ├── train/
│   │       │   └── val/
│   │       └── dataset.yaml
│   └── models/                      # Trained models
│       └── yolo_<job_id>/
│           └── employee_detector_<job_id>.pt
└── static/
    └── faces/                       # Source face images
```

## Training Flow

### 1. User Selects Employees
```javascript
// In Face Labeling tab
selectedGroups = ['PERSON-0001', 'PERSON-0002', ..., 'PERSON-0094']
```

### 2. Start Training
```python
# In app.py
job_id = training_manager.start_training(selectedGroups)
```

### 3. Dataset Preparation
```bash
# ExternalYOLOTrainer launches:
python3 prepare_yolo_dataset.py \
    --job-id "abc123" \
    --groups '["PERSON-0001", "PERSON-0002"]' \
    --output-dir ./datasets
```

Creates:
```
datasets/dataset_abc123/
├── images/
│   ├── train/
│   │   ├── face_001.jpg    # From PERSON-0001
│   │   ├── face_002.jpg    # From PERSON-0001
│   │   └── face_003.jpg    # From PERSON-0002
│   └── val/
│       └── face_004.jpg    # From PERSON-0002
├── labels/
│   ├── train/
│   │   ├── face_001.txt    # "0 0.5 0.5 1.0 1.0"
│   │   ├── face_002.txt    # "0 0.5 0.5 1.0 1.0"
│   │   └── face_003.txt    # "1 0.5 0.5 1.0 1.0"
│   └── val/
│       └── face_004.txt    # "1 0.5 0.5 1.0 1.0"
└── dataset.yaml
```

### 4. YOLO Training
```bash
# ExternalYOLOTrainer launches:
python3 train_yolo_model.py \
    --job-id "abc123" \
    --dataset ./datasets/dataset_abc123/dataset.yaml \
    --epochs 10 \
    --batch 4
```

### 5. Status Monitoring
```python
# Main app checks status files
status = training_manager.get_job_status(job_id)
# Returns: {
#   "status": "training",
#   "progress": 45,
#   "message": "Training epoch 5/10"
# }
```

### 6. Training Output
```
models/yolo_abc123/
├── attendance/
│   ├── weights/
│   │   ├── best.pt
│   │   └── last.pt
│   └── results.csv
├── employee_detector_abc123.pt  # Final model
└── metadata.json
```

## Status Files

### Dataset Preparation
```json
// abc123_dataset.json
{
  "job_id": "abc123",
  "groups": ["PERSON-0001", "PERSON-0002"],
  "train_images": 80,
  "val_images": 20,
  "classes": 2,
  "dataset_path": "./datasets/dataset_abc123",
  "yaml_path": "./datasets/dataset_abc123/dataset.yaml"
}
```

### Training Status
```json
// abc123_status.json
{
  "job_id": "abc123",
  "status": "training",
  "progress": 60,
  "message": "Training epoch 6/10"
}
```

### Training Result
```json
// abc123_result.json
{
  "job_id": "abc123",
  "model_path": "./models/yolo_abc123/employee_detector_abc123.pt",
  "status": "completed"
}
```

## Using the Trained Model

```python
from ultralytics import YOLO

# Load trained model
model = YOLO('models/yolo_abc123/employee_detector_abc123.pt')

# Process surveillance video
results = model.predict('entrance_camera.mp4')

# Extract employee detections
for r in results:
    for box in r.boxes:
        employee_id = r.names[int(box.cls)]  # "PERSON-0001"
        confidence = float(box.conf)         # 0.92
        bbox = box.xyxy[0].tolist()         # [x1, y1, x2, y2]
        
        # Log attendance
        log_attendance(employee_id, timestamp, 'entrance')
```

## Benefits

1. **No Server Restart**: Training runs independently
2. **Memory Efficient**: Separate process manages memory
3. **Progress Tracking**: Real-time status updates
4. **Modular Design**: Easy to update training logic
5. **Scalable**: Multiple training jobs can run in parallel

## Troubleshooting

### Common Issues

1. **File Not Found Error**
   - Check working directory
   - Verify paths in scripts
   - Ensure face images exist

2. **Memory Error**
   - Reduce batch size
   - Decrease image size
   - Use fewer epochs

3. **Training Fails**
   - Check Python dependencies
   - Verify YOLO installation
   - Review error logs

### Debug Commands

```bash
# Test dataset preparation
cd training
python prepare_yolo_dataset.py \
    --job-id "test123" \
    --groups '["PERSON-0001"]' \
    --output-dir ./datasets

# Test training
python train_yolo_model.py \
    --job-id "test123" \
    --dataset ./datasets/dataset_test123/dataset.yaml \
    --epochs 1 \
    --batch 1
```

## Future Enhancements

1. **GPU Support**: Add CUDA device selection
2. **Advanced Augmentation**: Improve training data variety
3. **Model Versioning**: Track multiple model versions
4. **Distributed Training**: Support multi-GPU training
5. **Real-time Monitoring**: WebSocket for live updates