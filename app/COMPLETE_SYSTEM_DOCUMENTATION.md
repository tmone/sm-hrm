# Employee Attendance System - Complete Documentation

## System Overview

This system uses YOLO-based face detection to track employee attendance in surveillance videos. It can:
1. Train custom YOLO models to detect specific employees
2. Process surveillance videos to identify employees
3. Track entry/exit times for attendance calculation

## Architecture

```
Frontend (React/Next.js)
    │
    ├─> Face Labeling Tab
    │   └─> Select employees → Train Model
    │
    ├─> Test Model Page
    │   └─> Upload video → Test detection
    │
Backend (FastAPI)
    │
    ├─> External YOLO Trainer
    │   ├─> prepare_yolo_dataset.py
    │   └─> train_yolo_model.py
    │
    └─> Trained Models
        └─> employee_detector_*.pt
```

## Training Workflow

### 1. Data Preparation
- **Face Groups**: Each employee is identified by a group ID (PERSON-XXXX)
- **Face Images**: Multiple face images per employee stored in `/static/faces/`
- **Identity Mapping**: JSON file tracks which faces belong to which employee

### 2. Training Process
1. Select employees in Face Labeling tab
2. Click "Train Model" button
3. System prepares YOLO dataset:
   - Copies face images to train/val directories
   - Creates YOLO label files
   - Generates dataset.yaml configuration
4. Trains YOLOv8 model in external process
5. Saves trained model as `employee_detector_{job_id}.pt`

### 3. Testing & Deployment
1. Upload surveillance video to Test Model page
2. System uses trained YOLO model to detect employees
3. Returns detection results with:
   - Employee IDs
   - Detection confidence
   - Frame numbers
   - Bounding boxes

## Key Components

### External YOLO Trainer (`external_yolo_trainer.py`)
- Manages training jobs
- Launches external Python scripts
- Monitors training progress
- No server restarts required

### Dataset Preparation (`prepare_yolo_dataset.py`)
- Converts face groups to YOLO format
- Creates train/val split (80/20)
- Generates proper directory structure
- Creates dataset.yaml configuration

### Model Training (`train_yolo_model.py`)
- Uses YOLOv8 for training
- Configurable epochs, batch size, image size
- Saves best model for deployment
- Updates status files for monitoring

### Model Testing
- Processes uploaded videos
- Detects employees frame by frame
- Returns comprehensive results
- Calculates attendance metrics

## API Endpoints

### Training
- `POST /api/training/start`: Start new training job
- `GET /api/training/status/{job_id}`: Check training progress
- `POST /api/training/test`: Test model on video

### Identity Groups
- `GET /api/identity-groups`: List all employee groups
- `POST /api/identity-groups`: Create new group
- `PUT /api/identity-groups/{id}`: Update group

## File Structure

```
StepmediaHRM/app/
├── training/
│   ├── prepare_yolo_dataset.py
│   ├── train_yolo_model.py
│   ├── datasets/
│   │   └── dataset_{job_id}/
│   │       ├── images/train/
│   │       ├── images/val/
│   │       ├── labels/train/
│   │       ├── labels/val/
│   │       └── dataset.yaml
│   └── models/
│       └── yolo_{job_id}/
│           └── employee_detector_{job_id}.pt
├── static/
│   └── faces/
│       └── {face_id}.jpg
└── db/
    └── external_yolo_trainer.py
```

## Configuration

### Training Parameters
```python
# Default settings
epochs = 10          # Training epochs
batch_size = 4       # Batch size
imgsz = 320         # Image size
device = 'cpu'      # CPU/GPU selection
conf = 0.5          # Detection confidence threshold
```

### Memory Optimization
- Small batch sizes (4-8)
- Reduced image size (320x320)
- CPU training for limited memory
- External process isolation

## Usage Example

### 1. Train Model
```javascript
// Select employees
const selectedGroups = ['PERSON-0001', 'PERSON-0002', ...];

// Start training
const response = await fetch('/api/training/start', {
  method: 'POST',
  body: JSON.stringify({ identity_group_ids: selectedGroups })
});
```

### 2. Test Model
```javascript
// Upload video
const formData = new FormData();
formData.append('file', videoFile);

// Test detection
const response = await fetch('/api/training/test', {
  method: 'POST',
  body: formData
});

// Results include:
// - Total frames processed
// - Unique employees detected
// - Detection confidence scores
// - Frame-by-frame detections
```

## Benefits

1. **Automated Attendance**: No manual check-in required
2. **High Accuracy**: YOLO provides precise detection
3. **Scalable**: Handles many employees
4. **No Downtime**: External training process
5. **Real-time Processing**: Fast inference on videos

## Future Enhancements

1. **Multi-camera Support**: Track across multiple entrances
2. **Live Stream Processing**: Real-time attendance
3. **Reporting Dashboard**: Attendance analytics
4. **GPU Acceleration**: Faster training/inference
5. **Mobile App**: Remote monitoring

## Troubleshooting

### Training Issues
- Check face images exist in `/static/faces/`
- Verify sufficient memory available
- Ensure ultralytics package installed
- Check Python virtual environment active

### Detection Issues
- Verify model trained successfully
- Check video format compatibility
- Adjust confidence threshold
- Ensure adequate lighting in videos

## Success Metrics

- Training completed: ✓
- Dataset created: ✓
- Model saved: ✓
- Video testing: ✓
- Employee detection: ✓
- No server restarts: ✓

The system is now fully operational for employee attendance tracking using YOLO-based face detection!