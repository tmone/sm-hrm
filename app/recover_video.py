#!/usr/bin/env python
"""
Recovery script for failed video processing.
This script will attempt to recover faces from a video that failed during processing.
"""
import sys
import os
import requests
import logging
import json
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def recover_video(video_id: str, api_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Attempt to recover a video that failed during processing
    
    Args:
        video_id: The ID of the video to recover
        api_url: Optional API base URL, defaults to localhost:7860
        
    Returns:
        Dict with recovery results
    """
    # Default API URL if not provided
    if api_url is None:
        api_url = "http://127.0.0.1:7860"
    
    # Ensure video_id is properly formatted (remove .mp4 if present)
    if video_id.endswith('.mp4'):
        video_id = video_id[:-4]
    
    recovery_endpoint = f"{api_url}/api/videos/{video_id}/recover"
    logger.info(f"Attempting to recover video {video_id}")
    logger.info(f"Making request to: {recovery_endpoint}")
    
    try:
        # Make request to recovery endpoint
        response = requests.post(recovery_endpoint)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Recovery successful: {json.dumps(result, indent=2)}")
            return result
        else:
            error_msg = f"Recovery failed with status code {response.status_code}: {response.text}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        error_msg = f"Error during recovery: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

if __name__ == "__main__":
    # Get video ID from command line or use the one from error message
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
    else:
        # Default to the video ID from the error message
        video_id = "a9b417e2-1616-4809-8072-2906d9446765"
    
    # Run recovery
    result = recover_video(video_id)
    
    # Print summary
    if result.get("success", False):
        faces_count = result.get("faces_count", 0)
        logger.info(f"Successfully recovered {faces_count} faces from video {video_id}")
        print(f"\nRECOVERY SUCCESSFUL: Saved {faces_count} faces from video {video_id}")
    else:
        logger.error(f"Recovery failed for video {video_id}: {result.get('error', 'Unknown error')}")
        print(f"\nRECOVERY FAILED: {result.get('error', 'Unknown error')}")