# Employee Attendance Training Approach

## Current Implementation: Lightweight Face Recognition

Due to memory constraints on the server, we've implemented a lightweight approach that:

1. **Creates an employee face database** instead of full YOLO training
2. **Uses dlib face embeddings** for employee identification
3. **Simulates detection results** for testing purposes

### How It Works

1. **Data Collection**:
   - Select employee groups (PERSON-XXXX codes)
   - Extract face embeddings for each employee
   - Store average embeddings per employee

2. **Model Creation**:
   - Build a database of employee embeddings
   - Save as a pickle file for quick loading
   - No heavy neural network training required

3. **Testing**:
   - Load the employee database
   - Simulate detections for demo purposes
   - Return mock attendance data

## Future: Full YOLO Implementation

When more server resources are available, we can implement full YOLO training:

### YOLO Training Configuration
```python
model.train(
    data=yaml_path,
    epochs=50,
    imgsz=640,
    batch=16,
    device='cuda',  # GPU for faster training
    workers=4
)
```

### Benefits of Full YOLO:
1. **Real object detection** in surveillance videos
2. **Multi-person tracking** in single frames
3. **Better accuracy** with more training data
4. **Production-ready** deployment

## Memory Optimization Tips

For limited memory environments:

1. **Reduce batch size**: `batch=2` or `batch=4`
2. **Smaller images**: `imgsz=320` instead of `640`
3. **Fewer epochs**: `epochs=10` for quick tests
4. **Disable workers**: `workers=0` to avoid multiprocessing
5. **Use CPU**: `device='cpu'` if GPU memory is limited

## Testing the System

1. **Upload surveillance video**
2. **Run detection model**
3. **View employee detections**
4. **Calculate attendance times**

The current lightweight implementation is perfect for:
- Proof of concept
- Demo purposes
- Small-scale testing
- Limited server resources

For production deployment with hundreds of employees and real-time video processing, the full YOLO implementation would be recommended.