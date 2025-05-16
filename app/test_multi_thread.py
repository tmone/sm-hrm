#!/usr/bin/env python3

"""Simple test to verify multi-threaded video testing"""

import asyncio
from db.multi_thread_tester import MultiThreadVideoTester
import os
import glob

async def progress_callback(progress, frames_processed, total_frames):
    """Async progress callback"""
    print(f"Progress: {progress}% ({frames_processed}/{total_frames} frames)")

def test_multi_threaded_processing():
    print("Testing multi-threaded video processing...")
    
    # Find a test video
    test_video = "tests/sample_video.mp4"  # Use the sample video in tests directory
    if not os.path.exists(test_video):
        print(f"Test video not found: {test_video}")
        return
    
    # Find latest YOLO model
    models_pattern = "training/models/yolo_*/employee_detector_*.pt"
    model_files = glob.glob(models_pattern)
    
    if not model_files:
        print("No trained YOLO models found")
        return
    
    latest_model = max(model_files, key=os.path.getctime)
    print(f"Using model: {latest_model}")
    
    # Create tester
    tester = MultiThreadVideoTester(max_workers=4)
    
    # Test the video with async progress callback
    async def run_test():
        result = tester.test_video(
            model_path=latest_model,
            video_path=test_video,
            progress_callback=progress_callback
        )
        
        if result['success']:
            print(f"\nTest completed successfully!")
            print(f"Total frames: {result['total_frames']}")
            print(f"Total detections: {result['summary']['total_detections']}")
            print(f"Unique employees: {result['unique_employees']}")
            print(f"Average confidence: {result['summary']['average_confidence']:.3f}")
        else:
            print(f"Test failed: {result.get('error', 'Unknown error')}")
    
    # Run the test
    asyncio.run(run_test())

if __name__ == "__main__":
    test_multi_threaded_processing()