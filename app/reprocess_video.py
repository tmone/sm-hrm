#!/usr/bin/env python
"""
This script reprocesses a video by sending a request to the processing endpoint.
It can be used after removing all faces from a video to start fresh.
"""
import os
import sys
import json
import logging
import requests
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reprocess_video(video_id: str, api_url: str = None) -> dict:
    """
    Send a request to reprocess a video
    
    Args:
        video_id: The ID of the video to reprocess
        api_url: The base API URL (default: http://localhost:7860)
        
    Returns:
        Dict with the API response
    """
    # Set default API URL if not provided
    if not api_url:
        api_url = "http://localhost:7860"
    
    # Construct the endpoint URL
    endpoint = f"{api_url}/api/videos/{video_id}/process"
    logger.info(f"Sending reprocessing request to {endpoint}")
    
    try:
        # Send the request
        response = requests.post(endpoint)
        
        # Check the response
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Successfully initiated reprocessing for video {video_id}")
            return {"success": True, "data": result}
        else:
            error_msg = f"Error reprocessing video: {response.status_code} {response.text}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Exception during reprocessing request: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

def main():
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Reprocess a video")
    parser.add_argument("video_id", help="ID of the video to reprocess")
    parser.add_argument("--api-url", help="Base API URL (default: http://localhost:7860)")
    parser.add_argument("--force", action="store_true", help="Don't prompt for confirmation")
    args = parser.parse_args()
    
    video_id = args.video_id
    api_url = args.api_url
    
    # Confirm before proceeding
    if not args.force:
        confirm = input(f"This will reprocess video {video_id}. Continue? (y/N): ")
        if confirm.lower() != 'y':
            logger.info("Operation cancelled by user")
            return
    
    # Reprocess the video
    result = reprocess_video(video_id, api_url)
    
    # Print result
    if result["success"]:
        data = result["data"]
        print("=" * 50)
        print(f"Successfully initiated reprocessing for video {video_id}")
        print(f"Task ID: {data.get('task_id', 'N/A')}")
        print(f"Status: {data.get('status', 'N/A')}")
        print("\nThe video is now being processed in the background.")
        print("You can check the status in the UI or using the API.")
        print("=" * 50)
    else:
        print("=" * 50)
        print(f"Failed to reprocess video: {result['error']}")
        print("=" * 50)

if __name__ == "__main__":
    main()