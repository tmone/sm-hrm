# Employee Attendance System - YOLO-based Face Detection

## Overview
This system uses YOLO (You Only Look Once) to detect and identify specific employees in surveillance videos for automatic attendance tracking.

## Problem Statement
HR departments need to:
1. Automatically track when employees enter/exit the workplace
2. Calculate work hours based on face detection in surveillance footage
3. Generate attendance reports without manual intervention

## Solution Architecture

### 1. Data Collection Phase
- Upload surveillance videos from entrance/exit cameras
- Extract faces from videos
- Group faces by identity (each employee gets a unique PERSON-XXXX code)

### 2. Training Phase
- Select employee groups to train the model on
- Create YOLO dataset with employee faces as training data
- Train custom YOLO model to detect specific employees
- Each employee becomes a "class" in the YOLO model

### 3. Detection Phase
- Process new surveillance videos through trained model
- Detect and identify employees in real-time
- Track entry/exit times for attendance calculation

## Technical Implementation

### Training Data Format (YOLO)
```
dataset/
├── images/
│   ├── train/
│   │   ├── face_001.jpg  # Employee PERSON-0001
│   │   ├── face_002.jpg  # Employee PERSON-0001
│   │   └── face_003.jpg  # Employee PERSON-0002
│   └── val/
│       ├── face_004.jpg  # Employee PERSON-0001
│       └── face_005.jpg  # Employee PERSON-0002
├── labels/
│   ├── train/
│   │   ├── face_001.txt  # "0 0.5 0.5 1.0 1.0" (class 0 = PERSON-0001)
│   │   ├── face_002.txt  # "0 0.5 0.5 1.0 1.0"
│   │   └── face_003.txt  # "1 0.5 0.5 1.0 1.0" (class 1 = PERSON-0002)
│   └── val/
│       ├── face_004.txt  # "0 0.5 0.5 1.0 1.0"
│       └── face_005.txt  # "1 0.5 0.5 1.0 1.0"
└── dataset.yaml
```

### YOLO Configuration (dataset.yaml)
```yaml
path: /path/to/dataset
train: images/train
val: images/val
nc: 94  # number of employees
names: ['PERSON-0001', 'PERSON-0002', ..., 'PERSON-0094']
```

### Training Process
1. Convert identity groups to YOLO format
2. Train YOLOv8 model with employee faces
3. Model learns to detect and classify employees
4. Save trained model for inference

### Detection Workflow
```python
# Load trained model
model = YOLO('employee_detector.pt')

# Process surveillance video
results = model.predict(source='entrance_camera.mp4')

# Extract employee detections
for result in results:
    for box in result.boxes:
        employee_id = result.names[int(box.cls)]
        confidence = float(box.conf)
        timestamp = get_frame_timestamp()
        
        # Log attendance
        log_employee_presence(employee_id, timestamp, 'entrance')
```

## Key Features

### 1. Multi-Employee Detection
- Detects multiple employees in a single frame
- Tracks individual employees across video frames
- Handles overlapping detections

### 2. Attendance Calculation
- First detection = arrival time
- Last detection = departure time
- Calculate work hours = departure - arrival

### 3. Confidence Thresholds
- Only accept detections above confidence threshold (e.g., 0.7)
- Reduces false positives
- Ensures accurate attendance records

## Benefits
1. **Automated**: No manual attendance marking
2. **Accurate**: High precision employee identification
3. **Scalable**: Can handle hundreds of employees
4. **Real-time**: Process live video streams
5. **Historical**: Analyze past footage for attendance verification

## Testing Interface
The system includes a test page where you can:
1. Upload a surveillance video
2. Run the trained model
3. View detected employees and timestamps
4. Verify model accuracy before deployment

## Future Enhancements
1. Support for multiple camera angles
2. Integration with HR management systems
3. Real-time alerts for unauthorized access
4. Monthly/yearly attendance reports
5. Support for mask detection during COVID