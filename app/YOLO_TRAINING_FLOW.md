# YOLO Training Flow for Employee Attendance

## External Script Architecture

```
Main App (app.py)
    │
    ├─> ExternalYOLOTrainer
    │       │
    │       ├─> Launch prepare_yolo_dataset.py
    │       │       │
    │       │       ├─> Load face groups
    │       │       ├─> Copy face images
    │       │       ├─> Create YOLO labels
    │       │       └─> Generate dataset.yaml
    │       │
    │       └─> Launch train_yolo_model.py
    │               │
    │               ├─> Load YOLOv8 model
    │               ├─> Train on dataset
    │               ├─> Save best model
    │               └─> Update status
    │
    └─> No server restart needed!
```

## Dataset Structure

```
datasets/dataset_{job_id}/
├── images/
│   ├── train/
│   │   ├── face_001.jpg    # Employee PERSON-0001
│   │   ├── face_002.jpg    # Employee PERSON-0001
│   │   └── face_003.jpg    # Employee PERSON-0002
│   └── val/
│       ├── face_004.jpg    # Employee PERSON-0001
│       └── face_005.jpg    # Employee PERSON-0002
├── labels/
│   ├── train/
│   │   ├── face_001.txt    # "0 0.5 0.5 1.0 1.0"
│   │   ├── face_002.txt    # "0 0.5 0.5 1.0 1.0"
│   │   └── face_003.txt    # "1 0.5 0.5 1.0 1.0"
│   └── val/
│       ├── face_004.txt    # "0 0.5 0.5 1.0 1.0"
│       └── face_005.txt    # "1 0.5 0.5 1.0 1.0"
└── dataset.yaml
```

## YOLO Label Format

Each label file contains:
```
class_index center_x center_y width height
```

For face images (already cropped):
```
0 0.5 0.5 1.0 1.0
```

Where:
- `0` = Employee class index (PERSON-0001 = 0, PERSON-0002 = 1, etc.)
- `0.5 0.5` = Center of image (normalized)
- `1.0 1.0` = Full image width/height (normalized)

## Training Process

### 1. Select Employees
```javascript
// In Face Labeling tab
selected = ['PERSON-0001', 'PERSON-0002', 'PERSON-0003']
```

### 2. Prepare Dataset
```bash
python prepare_yolo_dataset.py \
    --job-id "abc123" \
    --groups '["PERSON-0001", "PERSON-0002", "PERSON-0003"]' \
    --output-dir ./datasets
```

Creates:
- Face images copied to train/val folders
- Label files with employee class indices
- dataset.yaml configuration

### 3. Train YOLO Model
```bash
python train_yolo_model.py \
    --job-id "abc123" \
    --dataset ./datasets/dataset_abc123/dataset.yaml \
    --epochs 10 \
    --batch 4
```

Outputs:
- Trained model: `employee_detector_abc123.pt`
- Can detect specific employees in videos

### 4. Use for Attendance
```python
# Load trained model
model = YOLO('employee_detector_abc123.pt')

# Process surveillance video
results = model.predict('entrance_camera.mp4')

# Track employee presence
for r in results:
    for box in r.boxes:
        employee_id = r.names[int(box.cls)]  # e.g., "PERSON-0001"
        confidence = float(box.conf)
        # Log attendance time
```

## Benefits

1. **No Server Restart**: Training runs in separate process
2. **Memory Efficient**: External scripts manage their own memory
3. **Progress Tracking**: Status files monitor training progress
4. **Modular**: Easy to update training logic independently
5. **Scalable**: Can run multiple training jobs in parallel

## Example Training Output

```
Preparing YOLO dataset for job abc123
Selected groups: 94
Classes (employees): 94
Processing PERSON-0001: 8 train, 2 val
Processing PERSON-0002: 6 train, 2 val
...

Dataset prepared:
  Training images: 750
  Validation images: 188
  Classes (employees): 94
  Dataset path: ./datasets/dataset_abc123

Starting YOLO training...
Epoch 1/10: 100%|████████| 40/40 [00:45<00:00,  1.12s/it]
Epoch 2/10: 100%|████████| 40/40 [00:42<00:00,  1.05s/it]
...

Training completed. Model saved to: models/yolo_abc123/employee_detector_abc123.pt
```