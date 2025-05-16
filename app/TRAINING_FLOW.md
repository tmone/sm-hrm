# Face Recognition Training Flow

## Overview
The training system creates a face recognition model that can identify people based on their facial features. Each identity group represents one unique person.

## Data Structure

```
Identity Groups (JSON)
├── PERSON-0001 (John Doe)
│   ├── face_id_123.jpg
│   ├── face_id_456.jpg
│   └── face_id_789.jpg
├── PERSON-0002 (Jane Smith)
│   ├── face_id_234.jpg
│   └── face_id_567.jpg
└── PERSON-0003 (Bob Johnson)
    ├── face_id_345.jpg
    ├── face_id_678.jpg
    └── face_id_901.jpg
```

## Training Steps

### 1. Selection Phase
- User selects identity groups to train on (can select all 94 groups)
- Each group ID (e.g., "PERSON-0001") is passed to the training system

### 2. Data Collection Phase
For each selected group:
1. Load the group data from JSON
2. Get all face IDs belonging to this group
3. For each face ID:
   - Load the face image from `static/faces/{face_id}.jpg`
   - Extract 128-dimensional face embedding using dlib
   - Store embedding with the group ID as its label

### 3. Dataset Preparation
```python
# Example dataset structure:
embeddings = [
    [0.1, 0.2, ..., 0.9],   # 128 dimensions - Face 1 of Person 1
    [0.11, 0.21, ..., 0.91], # 128 dimensions - Face 2 of Person 1
    [0.12, 0.22, ..., 0.92], # 128 dimensions - Face 3 of Person 1
    [0.8, 0.7, ..., 0.3],    # 128 dimensions - Face 1 of Person 2
    [0.81, 0.71, ..., 0.31], # 128 dimensions - Face 2 of Person 2
]

labels = [
    "PERSON-0001",  # Label for Face 1 of Person 1
    "PERSON-0001",  # Label for Face 2 of Person 1
    "PERSON-0001",  # Label for Face 3 of Person 1
    "PERSON-0002",  # Label for Face 1 of Person 2
    "PERSON-0002",  # Label for Face 2 of Person 2
]
```

### 4. Model Training
- Use SVM (Support Vector Machine) classifier
- Train the model to distinguish between different people
- The model learns patterns in the embeddings that differentiate each person

### 5. Model Saving
- Save the trained model to disk
- Model can now predict identity for new faces

## Prediction Process
When recognizing a new face:
1. Extract face embedding from the new image
2. Use trained model to predict which group ID it belongs to
3. Return the predicted identity (e.g., "PERSON-0001") and confidence score

## Key Concepts
- **One group = One person**: Each identity group represents a unique individual
- **Multiple faces per group**: Each person can have many photos
- **Label = Group ID**: The group ID serves as the person's identifier
- **Embeddings = Features**: 128-dimensional vectors that capture facial features
- **Training uses all faces**: Every face from every selected group is used

## Example Scenario
If you select all 94 groups and each group has 10 faces:
- Total faces processed: 940
- Total embeddings generated: 940 (one per face)
- Total unique labels: 94 (one per person)
- Model learns to distinguish between 94 different people