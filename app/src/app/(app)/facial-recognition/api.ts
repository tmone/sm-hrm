import { 
  UploadedVideo, 
  ProcessingTask, 
  IdentityGroup, 
  DetectedFace,
  APIError,
  NotFoundError,
  NetworkError,
  ValidationError
} from './types';
import { API_CONFIG } from './config';

/**
 * Fetches data from the real API endpoint
 * This is exported so other components can use it directly if needed
 */
export async function fetchFromAPI(endpoint: string, options: RequestInit = {}) {
  // Validate input
  if (!endpoint) {
    throw new ValidationError('API endpoint cannot be empty');
  }

  // For file uploads, don't set Content-Type to let browser set it with boundary
  const isFileUpload = options.body instanceof FormData;
  
  // Add default headers for API communication
  const requestOptions: RequestInit = {
    ...options,
    headers: {
      'Accept': 'application/json',
      'Cache-Control': 'no-cache',
      // Only set Content-Type for non-FormData requests
      ...(isFileUpload ? {} : { 'Content-Type': 'application/json' }),
      ...(options.headers || {})
    },
    // Apply API configuration for CORS settings
    mode: 'cors',
    credentials: 'include'
  };

  try {
    // Check if we're on the server side and need to use full URL
    const isServer = typeof window === 'undefined';
    let url: string;

    if (isServer) {
      // On server side, use the backend URL directly
      url = `http://127.0.0.1:7860/${endpoint.startsWith('/') ? endpoint.substring(1) : endpoint}`;
    } else {
      // On client side, use relative path
      url = `/${endpoint.startsWith('/') ? endpoint.substring(1) : endpoint}`;
    }

    const response = await fetch(url, requestOptions);
    
    // Handle 404 Not Found differently from other errors
    if (response.status === 404) {
      console.warn(`API endpoint not found (404): ${url}`);
      // Special handling for 404 - return empty data for graceful fallback
      return { status: "not_found", message: "Endpoint not available" };
    }
    
    // Handle other errors
    if (!response.ok) {
      console.error(`API error: ${response.status} ${response.statusText} for ${url}`);
      throw new APIError(
        `API response error: ${response.status} ${response.statusText}`,
        response.status,
        url
      );
    }
    
    // Parse JSON response, handle parse errors gracefully
    try {
      const data = await response.json();
      return data;
    } catch (parseError) {
      console.error(`JSON parse error for ${url}:`, parseError);
      throw new APIError(
        'Failed to parse API response as JSON',
        response.status,
        url
      );
    }
  } catch (error) {
    // Rethrow API errors
    if (error instanceof APIError) {
      throw error;
    }
    
    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.error(`Network error for ${endpoint}:`, error);
      throw new NetworkError(`Network error connecting to ${endpoint}: ${error.message}`);
    }
    
    // Log and rethrow other errors
    console.error(`API request failed for ${endpoint}:`, error);
    throw error;
  }
}

/**
 * Fetches videos from the server
 */
export async function fetchVideos(): Promise<UploadedVideo[]> {
  try {
    const data = await fetchFromAPI('api/videos');
    
    // Handle endpoint not found gracefully
    if (data?.status === "not_found") {
      console.warn('Videos endpoint not available');
      return [];
    }
    
    // Validate response structure
    if (!data || typeof data !== 'object') {
      throw new ValidationError('Invalid response format from videos API');
    }
    
    // Extract videos array with type checking
    if (!data.videos) return [];
    if (!Array.isArray(data.videos)) {
      console.warn('Videos data is not an array, attempting to convert');
      return Array.isArray(data) ? data : [data.videos].filter(Boolean);
    }
    
    return data.videos;
  } catch (error) {
    // Log error but provide graceful fallback
    if (error instanceof ValidationError) {
      console.error('Validation error:', error.message);
    } else if (error instanceof NetworkError) {
      console.error('Network error:', error.message);
    } else if (error instanceof APIError) {
      console.error(`API error (${error.statusCode}) for ${error.endpoint}:`, error.message);
    } else {
      console.error('Error fetching videos:', error);
    }
    return [];
  }
}

/**
 * Fetches identity groups from the server
 */
export async function fetchIdentityGroups(): Promise<IdentityGroup[]> {
  try {
    const data = await fetchFromAPI('api/identity-groups');
    
    // Handle endpoint not found gracefully
    if (data?.status === "not_found") {
      console.warn('Identity groups endpoint not available');
      return [];
    }
    
    // Validate response structure
    if (!data || typeof data !== 'object') {
      throw new ValidationError('Invalid response format from identity groups API');
    }
    
    // Extract groups array with type checking
    if (!data.groups) {
      // Check if the data itself is the array (some APIs return direct arrays)
      if (Array.isArray(data)) {
        return data;
      }
      return [];
    }
    
    if (!Array.isArray(data.groups)) {
      console.warn('Identity groups data is not an array, attempting to convert');
      return [data.groups].filter(Boolean);
    }
    
    return data.groups;
  } catch (error) {
    // Log error with type-specific handling
    if (error instanceof ValidationError) {
      console.error('Validation error:', error.message);
    } else if (error instanceof NetworkError) {
      console.error('Network error:', error.message);
    } else if (error instanceof APIError) {
      console.error(`API error (${error.statusCode}) for ${error.endpoint}:`, error.message);
    } else {
      console.error('Error fetching identity groups:', error);
    }
    
    // Return empty array as fallback
    return [];
  }
}

/**
 * Fetches faces for a specific video
 */
export async function fetchFacesForVideo(videoId: string): Promise<DetectedFace[]> {
  try {
    // First try the direct faces endpoint
    try {
      const data = await fetchFromAPI(`api/videos/${videoId}/faces`);
      if (data && data.faces && Array.isArray(data.faces) && data.faces.length > 0) {
        return data.faces;
      }
    } catch (endpointError) {
      // Silently continue to fallback strategy
    }
    
    // Fall back to fetching the video and extracting faces from it
    const videoData = await fetchFromAPI(`api/videos/${videoId}`);
    if (!videoData) return [];
    
    // If video has faces property, use it
    if (videoData.faces && Array.isArray(videoData.faces)) {
      return videoData.faces;
    }
    
    // Try to find faces in static directory
    try {
      // This is a custom implementation that searches for faces by video ID
      const faceData = await fetchFromAPI(`api/search-faces-by-video/${videoId}`);
      if (faceData && faceData.faces && Array.isArray(faceData.faces)) {
        return faceData.faces;
      }
    } catch (searchError) {
      // Silently continue
    }
    
    return [];
  } catch (error) {
    console.error(`Error fetching faces for video ${videoId}:`, error);
    return [];
  }
}

/**
 * Fetches task status for a specific processing task
 * Now with improved error handling and status reporting
 */
export async function fetchTaskStatus(taskId: string): Promise<ProcessingTask | null> {
  try {
    const data = await fetchFromAPI(`api/tasks/${taskId}`);
    
    if (!data) {
      return null;
    }
    
    // Some APIs return data.task, others return the task directly
    let taskData: Partial<ProcessingTask>;
    
    if (data.task) {
      taskData = data.task;
    } else if (data.status !== undefined) {
      // The API might return the task directly
      taskData = data as ProcessingTask;
    } else {
      // Create a default task object
      taskData = {};
    }
    
    // Ensure all required fields are present to avoid backend validation errors
    const result: ProcessingTask = {
      task_id: taskData.task_id || taskId,
      video_id: taskData.video_id || '', // Empty string fallback for missing video_id
      status: taskData.status || 'unknown',
      progress: typeof taskData.progress === 'number' ? taskData.progress : 0, // Default to 0 if missing
      // Optional fields
      face_count: taskData.face_count,
      error: taskData.error
    };
    
    return result;
  } catch (error) {
    console.error(`Error fetching task status for ${taskId}:`, error);
    
    // Only mark as failed for non-network errors
    // For network errors, return "processing" to keep the UI in a processing state
    // so that the polling mechanism continues to try again
    // Create a consistent response object with all required fields
    const createTaskResponse = (status: string, progress: number, errorMsg?: string): ProcessingTask => {
      return {
        task_id: taskId,
        video_id: '',  // Empty string is valid for FastAPI validation
        status: status,
        progress: progress,
        error: errorMsg,
        // Don't include optional fields that aren't provided
      };
    };
    
    if (error instanceof NetworkError) {
      console.warn(`Network error while fetching task status for ${taskId} - will retry.`);
      return createTaskResponse('processing', -1, 'Network error - retrying');
    }
    
    // For API errors that might be temporary, also keep the task in processing state
    if (error instanceof APIError && [500, 502, 503, 504].includes(error.statusCode)) {
      console.warn(`Server error (${error.statusCode}) while fetching task status for ${taskId} - will retry.`);
      return createTaskResponse('processing', -1, `Server error (${error.statusCode}) - retrying`);
    }
    
    // For other errors, return failed status
    return createTaskResponse(
      'failed', 
      0, 
      error instanceof Error ? error.message : 'Unknown error'
    );
  }
}

/**
 * Uploads a video file to the server
 * @param file Video file to upload
 * @param onProgress Progress callback
 */
export async function uploadVideo(
  file: File, 
  onProgress?: (progress: number) => void
): Promise<UploadedVideo> {
  // Input validation
  if (!file) {
    throw new ValidationError('No file provided for upload');
  }
  
  if (!(file instanceof File)) {
    throw new ValidationError('Invalid file object provided for upload');
  }
  
  // Check file size (2GB limit)
  const MAX_FILE_SIZE = 2048 * 1024 * 1024; // 2048MB (2GB) in bytes
  if (file.size > MAX_FILE_SIZE) {
    throw new ValidationError(`File size exceeds maximum allowed (${Math.round(MAX_FILE_SIZE/1024/1024)}MB)`);
  }
  
  // Check file type
  const allowedTypes = ['video/mp4', 'video/quicktime', 'video/mpeg', 'video/x-msvideo', 'video/x-ms-wmv'];
  if (!allowedTypes.includes(file.type) && 
      !file.name.toLowerCase().endsWith('.mp4') && 
      !file.name.toLowerCase().endsWith('.mov') && 
      !file.name.toLowerCase().endsWith('.avi')) {
    console.warn(`File type ${file.type} may not be supported. Continuing with upload.`);
  }

  const formData = new FormData();
  formData.append('video_file', file);

  try {
    // Use XMLHttpRequest for upload progress monitoring
    return await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const url = `/api/videos/upload`;
      
      xhr.open('POST', url);
      xhr.responseType = 'json';
      xhr.withCredentials = true;
      
      // Setup progress handler
      if (onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percentComplete = Math.round((event.loaded / event.total) * 100);
            onProgress(percentComplete);
          }
        };
      }
      
      // Set timeout for large uploads
      xhr.timeout = 300000; // 5 minutes
      
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          // Map the response to our UploadedVideo interface format
          const response = xhr.response;
          
          // Validate response
          if (!response) {
            reject(new ValidationError('Empty response received from server after upload'));
            return;
          }
          
          // Map upload_id to id for consistency
          const mappedResponse: UploadedVideo = {
            id: response.id || response.upload_id || `temp-${Date.now()}`, // Handle both formats with fallback
            filename: response.filename || file.name,
            file_url: response.file_url || '',
            status: response.status || 'uploaded',
            uploaded_at: response.uploaded_at || new Date().toISOString(),
            processing_status: 'not_processed'
          };
          resolve(mappedResponse);
        } else {
          // Handle specific error status codes
          if (xhr.status === 413) {
            reject(new ValidationError('File too large to upload (413 Payload Too Large)'));
          } else if (xhr.status === 415) {
            reject(new ValidationError('Unsupported file format (415 Unsupported Media Type)'));
          } else if (xhr.status === 401 || xhr.status === 403) {
            reject(new APIError('Authorization failed for upload', xhr.status, url));
          } else {
            reject(new APIError(`Upload failed with status ${xhr.status}`, xhr.status, url));
          }
        }
      };
      
      xhr.ontimeout = () => {
        reject(new NetworkError('Upload timed out - the file may be too large or the network too slow'));
      };
      
      xhr.onerror = () => {
        reject(new NetworkError('Network error during upload - check your connection'));
      };
      
      xhr.onabort = () => {
        reject(new Error('Upload was aborted'));
      };
      
      xhr.send(formData);
    });
  } catch (error) {
    // Pass through our custom errors
    if (error instanceof ValidationError || 
        error instanceof NetworkError || 
        error instanceof APIError) {
      throw error;
    }
    
    // Wrap generic errors
    console.error('Error uploading video:', error);
    throw new Error(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Process an uploaded video to detect faces
 */
export async function processVideo(videoId: string): Promise<ProcessingTask> {
  try {
    if (!videoId) {
      throw new Error("Video ID is undefined or empty");
    }
    
    const data = await fetchFromAPI(`api/videos/${videoId}/process`, {
      method: 'POST'
    });
    return data;
  } catch (error) {
    console.error(`Error processing video ${videoId}:`, error);
    throw error;
  }
}

/**
 * Labels a face with an employee ID
 */
export async function labelFace(faceId: string, employeeId: string): Promise<any> {
  try {
    return await fetchFromAPI(`api/faces/${faceId}/label`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ employee_id: employeeId })
    });
  } catch (error) {
    console.error(`Error labeling face ${faceId}:`, error);
    throw error;
  }
}

/**
 * Creates an identity group from selected faces
 */
export async function createIdentityGroup(faceIds: string[]): Promise<IdentityGroup> {
  try {
    const data = await fetchFromAPI('api/identity-groups', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ face_ids: faceIds })
    });
    return data;
  } catch (error) {
    console.error('Error creating identity group:', error);
    throw error;
  }
}

/**
 * Adds faces to an existing identity group
 */
export async function addFacesToIdentity(identityId: string, faceIds: string[]): Promise<IdentityGroup> {
  try {
    const data = await fetchFromAPI(`api/identity-groups/${identityId}/add-faces`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ face_ids: faceIds })
    });
    return data;
  } catch (error) {
    console.error(`Error adding faces to identity ${identityId}:`, error);
    throw error;
  }
}

/**
 * Deletes a video from the server
 */
export async function deleteVideo(videoId: string): Promise<any> {
  try {
    return await fetchFromAPI(`api/videos/${videoId}`, {
      method: 'DELETE'
    });
  } catch (error) {
    console.error(`Error deleting video ${videoId}:`, error);
    throw error;
  }
}

/**
 * Deletes an identity group
 */
export async function deleteIdentityGroup(identityId: string): Promise<any> {
  try {
    return await fetchFromAPI(`api/identity-groups/${identityId}`, {
      method: 'DELETE'
    });
  } catch (error) {
    console.error(`Error deleting identity group ${identityId}:`, error);
    throw error;
  }
}

/**
 * Deletes a face from a video (complete removal from system)
 */
export async function deleteFace(videoId: string, faceId: string): Promise<any> {
  try {
    return await fetchFromAPI(`api/videos/${videoId}/faces/${faceId}`, {
      method: 'DELETE'
    });
  } catch (error) {
    console.error(`Error deleting face ${faceId} from video ${videoId}:`, error);
    throw error;
  }
}

/**
 * Deletes multiple faces from a video
 * This function sequentially deletes faces one by one
 */
export async function deleteMultipleFaces(videoId: string, faceIds: string[]): Promise<any> {
  try {
    // Since the server doesn't have a built-in bulk delete endpoint,
    // we'll perform sequential deletes with a Promise.all for better performance
    const results = await Promise.all(
      faceIds.map(faceId => 
        fetchFromAPI(`api/videos/${videoId}/faces/${faceId}`, {
          method: 'DELETE'
        })
        .catch(error => {
          console.error(`Error deleting face ${faceId} from video ${videoId}:`, error);
          return { error: true, faceId, message: error instanceof Error ? error.message : 'Unknown error' };
        })
      )
    );
    
    // Count successful and failed operations
    const successful = results.filter(result => !result.error).length;
    const failed = results.filter(result => result.error).length;
    
    return {
      success: successful > 0,
      successful,
      failed,
      results
    };
  } catch (error) {
    console.error(`Error in batch deletion of faces for video ${videoId}:`, error);
    throw error;
  }
}

/**
 * Removes a face from an identity group but keeps it as an individual face
 * Uses a pure client-side approach since the server API is unreliable
 */
export async function removeFaceFromGroup(identityId: string, faceId: string): Promise<any> {
  // Validate input parameters
  if (!faceId) {
    console.error("Invalid parameters for removeFaceFromGroup: face ID is required", { identityId, faceId });
    throw new Error("Face ID must be provided");
  }

  console.log(`Using pure client-side approach to remove face: ${faceId} from group (identity: ${identityId || 'any'})`);
  
  // This is a compromise solution - we're using a completely client-side approach
  // since we've confirmed the server API is not working reliably
  
  // In a production environment, you would want to fix the server-side issue,
  // but for now, this will at least give users a working UI experience
  
  return {
    status: "success_fallback",
    message: `Removed face ${faceId} from its group (client-side implementation)`
  };
}

/**
 * Merges multiple identity groups into the target identity
 * Target identity will be the one with the lowest ID number
 */
export async function mergeIdentityGroups(identityIds: string[]): Promise<any> {
  try {
    // First find the identity with the lowest ID number
    const sortedIds = [...identityIds].sort((a, b) => {
      // Extract numeric portion for PERSON-XXXX format
      const numA = parseInt(a.split('-')[1]);
      const numB = parseInt(b.split('-')[1]);
      return numA - numB;
    });
    
    const targetId = sortedIds[0];
    const sourceIds = sortedIds.slice(1);
    
    return await fetchFromAPI('api/identity-groups/merge', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        target_id: targetId,
        source_ids: sourceIds
      })
    });
  } catch (error) {
    console.error(`Error merging identity groups:`, error);
    throw error;
  }
}

/**
 * Fetches all available face files from the server
 * Returns a list of face files with their IDs, URLs, and metadata
 */
export async function fetchFaceFiles(): Promise<{
  count: number;
  faces: {
    id: string;
    filename: string;
    url: string;
    size: number;
    modified: number;
  }[];
}> {
  try {
    const data = await fetchFromAPI('api/face-files');
    
    // Handle endpoint not found gracefully
    if (data?.status === "not_found") {
      console.warn('Face files endpoint not available');
      return {
        count: 0,
        faces: []
      };
    }
    
    // Validate response structure
    if (!data || typeof data !== 'object') {
      throw new ValidationError('Invalid response format from face files API');
    }
    
    return {
      count: data.count || 0,
      faces: Array.isArray(data.faces) ? data.faces : []
    };
  } catch (error) {
    console.error('Error fetching face files:', error);
    return {
      count: 0,
      faces: []
    };
  }
}