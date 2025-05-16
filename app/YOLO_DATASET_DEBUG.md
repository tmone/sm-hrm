# YOLO Dataset Debug Guide

## Expected Dataset Structure

```
training/datasets/dataset_<job_id>/
├── images/
│   ├── train/
│   │   ├── face_001.jpg
│   │   ├── face_002.jpg
│   │   └── ...
│   └── val/
│       ├── face_100.jpg
│       └── ...
├── labels/
│   ├── train/
│   │   ├── face_001.txt  # "0 0.5 0.5 1.0 1.0"
│   │   ├── face_002.txt  # "0 0.5 0.5 1.0 1.0"
│   │   └── ...
│   └── val/
│       ├── face_100.txt  # "1 0.5 0.5 1.0 1.0"
│       └── ...
└── dataset.yaml
```

## dataset.yaml Content

```yaml
path: /home/tmone/pinokio/api/StepmediaHRM/app/training/datasets/dataset_<job_id>
train: images/train
val: images/val
nc: 94
names: ['PERSON-0001', 'PERSON-0002', ..., 'PERSON-0094']
```

## Common Issues and Fixes

### 1. FileNotFoundError: Error loading data

**Cause**: YOLO can't find the image directory
**Fix**: Ensure absolute paths in dataset.yaml

```python
yaml_config = {
    'path': os.path.abspath(dataset_dir),  # Must be absolute!
    'train': 'images/train',
    'val': 'images/val'
}
```

### 2. Empty directories

**Cause**: Face images not copied properly
**Fix**: Check source faces directory

```python
# Verify face exists before copying
src_path = os.path.join(faces_dir, f"{face_id}.jpg")
if os.path.exists(src_path):
    shutil.copy2(src_path, dst_image)
else:
    print(f"Warning: {src_path} not found")
```

### 3. Wrong working directory

**Cause**: Scripts run from wrong directory
**Fix**: Change to training directory

```python
os.chdir(training_dir)
subprocess.run(prepare_cmd)
```

## Debug Commands

### Check dataset structure
```bash
cd /home/tmone/pinokio/api/StepmediaHRM/app
python check_dataset.py <job_id>
```

### Manual dataset check
```bash
cd training/datasets/dataset_<job_id>
ls -la images/train/ | head -5
ls -la labels/train/ | head -5
cat dataset.yaml
```

### Test prepare script
```bash
cd training
python prepare_yolo_dataset.py \
    --job-id test123 \
    --groups '["PERSON-0001"]' \
    --output-dir ./datasets
```

## Training Process Flow

1. **Prepare Dataset**
   - Copy face images to train/val directories
   - Create YOLO label files
   - Generate dataset.yaml with absolute paths

2. **Verify Dataset**
   - Check all directories exist
   - Verify image files are present
   - Validate dataset.yaml paths

3. **Start Training**
   - Load dataset configuration
   - Initialize YOLO model
   - Train on prepared data

## Error Messages

### "Error loading data from .../images/train"
- Directory doesn't exist or is empty
- Path in dataset.yaml is incorrect
- Working directory is wrong

### "No images found"
- Face images not copied
- Wrong source directory
- Permission issues

### "Invalid dataset format"
- Missing dataset.yaml
- Incorrect YAML structure
- Missing label files

## Testing Individual Components

### Test face image access
```python
import os
faces_dir = "/home/tmone/pinokio/api/StepmediaHRM/app/static/faces"
test_face = os.path.join(faces_dir, "face_001.jpg")
print(f"Exists: {os.path.exists(test_face)}")
```

### Test dataset preparation
```python
from prepare_yolo_dataset import prepare_yolo_dataset
metadata = prepare_yolo_dataset("test", ["PERSON-0001"], "./test_dataset")
print(metadata)
```

### Test YOLO loading
```python
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
results = model.train(data='path/to/dataset.yaml', epochs=1)
```