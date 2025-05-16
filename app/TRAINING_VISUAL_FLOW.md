# Employee Attendance Training - Visual Flow

## How Training Works on Selected Face Images

```
1. SELECT EMPLOYEES
   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
   │ PERSON-0001 │ │ PERSON-0002 │ │ PERSON-0003 │
   │ [✓] Select  │ │ [✓] Select  │ │ [✓] Select  │
   └─────────────┘ └─────────────┘ └─────────────┘

2. LOAD FACE IMAGES FOR EACH SELECTED EMPLOYEE
   
   PERSON-0001:
   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
   │Face1│ │Face2│ │Face3│ │Face4│ │Face5│
   └─────┘ └─────┘ └─────┘ └─────┘ └─────┘
   
   PERSON-0002:
   ┌─────┐ ┌─────┐ ┌─────┐
   │Face1│ │Face2│ │Face3│
   └─────┘ └─────┘ └─────┘

3. EXTRACT FACE EMBEDDINGS (using dlib)
   
   Each face image → 128-dimensional vector
   ┌─────┐          ┌─────────────────────┐
   │Face │  ──────► │ [0.12, 0.45, ...  ] │
   └─────┘          └─────────────────────┘

4. CREATE EMPLOYEE PROFILE
   
   PERSON-0001:
   - Average embedding from 5 faces
   - Stored as employee signature
   
   PERSON-0002:
   - Average embedding from 3 faces
   - Stored as employee signature

5. SAVE TRAINED MODEL
   
   attendance_model.pkl
   ├── PERSON-0001: embedding
   ├── PERSON-0002: embedding
   └── PERSON-0003: embedding
```

## What Happens During Training

1. **Group Selection**: When you select employees in the Face Labeling tab, their group IDs are sent to the training system.

2. **Face Loading**: For each selected employee group:
   - Load all associated face image files from disk
   - Each face is a cropped image of that employee
   - Process up to 10 faces per employee (configurable)

3. **Embedding Extraction**: For each face image:
   - Use dlib to extract a 128-dimensional face embedding
   - This embedding captures the unique facial features
   - Failed embeddings are logged and skipped

4. **Employee Profile Creation**:
   - Calculate the average embedding from all faces
   - This creates a "signature" for each employee
   - Store in the model database

5. **Model Saving**:
   - Save all employee profiles to a pickle file
   - This becomes the attendance recognition model

## Training Logs Example

```
INFO: Processing group PERSON-0001 with 8 faces
INFO: Processing 8 faces for employee PERSON-0001
DEBUG: Processing face 1/8: /static/faces/face_001.jpg
DEBUG: Successfully extracted embedding for face face_001
...
INFO: Employee PERSON-0001: Successfully processed 7 faces out of 8 total

=== Training Summary ===
Job ID: abc-123
Employees requested: 3
Employees processed: 3
Total faces processed: 18
Average faces per employee: 6.00
Model saved to: /static/attendance_models/attendance_model_abc-123.pkl
======================
```

## Why You See Face Processing

The training system IS processing face images, but it happens quickly:

1. Loads each face image from `/static/faces/{face_id}.jpg`
2. Extracts embeddings using dlib
3. Averages embeddings per employee
4. Saves the model

The process is fast, so you might not see individual images displayed, but the logs show exactly which faces are being processed.