# YOLO Employee Training System

This directory contains standalone scripts for training YOLO models to detect employees in surveillance videos.

## Overview

The training system runs in separate processes to avoid restarting the main application server. It consists of:

1. **Dataset Preparation**: Converts selected employee face groups into YOLO format
2. **Model Training**: Trains YOLOv8 model on the prepared dataset
3. **External Control**: Managed by the main app without restarts

## Directory Structure

```
training/
├── prepare_yolo_dataset.py    # Prepares YOLO dataset from face groups
├── train_yolo_model.py        # Trains YOLO model
├── yolo_template/             # Template for YOLO dataset structure
├── datasets/                  # Generated datasets
├── models/                    # Trained models
└── requirements.txt           # Python dependencies
```

## Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Dataset

```bash
python prepare_yolo_dataset.py \
    --job-id "unique-job-id" \
    --groups '["PERSON-0001", "PERSON-0002"]' \
    --output-dir ./datasets
```

### 3. Train Model

```bash
python train_yolo_model.py \
    --job-id "unique-job-id" \
    --dataset ./datasets/dataset_unique-job-id/dataset.yaml \
    --epochs 50 \
    --batch 8 \
    --imgsz 320
```

## Training Process

1. **Face Collection**: Gathers face images from selected employee groups
2. **Dataset Creation**: Creates YOLO format with:
   - Images in `images/train` and `images/val`
   - Labels in `labels/train` and `labels/val`
   - Configuration in `dataset.yaml`
3. **Model Training**: Trains YOLOv8 to detect specific employees
4. **Model Output**: Saves trained model as `employee_detector_{job_id}.pt`

## Configuration

### Dataset Split
- Training: 80% of faces
- Validation: 20% of faces

### YOLO Settings
- Model: YOLOv8n (nano) for efficiency
- Image Size: 320x320 (configurable)
- Batch Size: 4-8 (depending on memory)
- Device: CPU (can be changed to GPU)

## Output Files

### Dataset Preparation
- `{job_id}_dataset.json`: Dataset metadata
- `datasets/dataset_{job_id}/`: YOLO dataset directory

### Model Training
- `{job_id}_status.json`: Training status
- `{job_id}_result.json`: Training result
- `models/yolo_{job_id}/`: Training outputs
- `models/yolo_{job_id}/employee_detector_{job_id}.pt`: Final model

## Integration

The main application launches these scripts through `ExternalYOLOTrainer`:

```python
# In the main app
trainer = ExternalYOLOTrainer()
job_id = trainer.start_training(group_ids=['PERSON-0001', 'PERSON-0002'])
status = trainer.get_job_status(job_id)
```

## Memory Optimization

To reduce memory usage:
- Small batch size (4-8)
- Reduced image size (320x320)
- CPU training (no GPU memory)
- Single worker process
- Early stopping enabled

## Testing

After training, the model can be tested on surveillance videos to detect employees and track attendance.